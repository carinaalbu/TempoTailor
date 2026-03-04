from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_bearer_token
from app.core.config import settings
from app.schemas.curation import CurationRequest, CurationResponse, CurationTrack
from app.schemas.llm import JudgeResult
from app.schemas.llm import VibeTranslation
from app.services.pace_service import pace_to_bpm
from app.services.llm_service import translate_vibe, judge_tracks
from app.services.deezer_service import get_deezer_candidates
from app.services.spotify_service import (
    resolve_deezer_to_spotify,
)
from app.services.spotify_auth import get_spotify_client

router = APIRouter(prefix="/curation", tags=["curation"])


@router.post("", response_model=CurationResponse)
def create_curation(
    req: CurationRequest,
    token_str: str = Depends(get_bearer_token),
):
    token = {"access_token": token_str}

    try:
        return _create_curation_impl(req, token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Curation failed: {e}",
        ) from e


def _create_curation_impl(req: CurationRequest, token: dict):
    target_bpm = pace_to_bpm(req.pace_min_per_km)
    if req.target_energy is not None and req.seed_genres and len(req.seed_genres) > 0:
        vibe_translation = VibeTranslation(
            target_energy=req.target_energy,
            target_valence=req.target_valence if req.target_valence is not None else 0.6,
            target_danceability=req.target_danceability if req.target_danceability is not None else 0.6,
            seed_genres=req.seed_genres[:4],
            seed_artists=[],
            seed_tracks=[],
        )
    elif req.vibe_prompt.strip():
        try:
            vibe_translation = translate_vibe(req.vibe_prompt)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Vibe translation failed: {e}") from e
    else:
        raise HTTPException(status_code=400, detail="Provide vibe text or energy + genres")
    vibe_params = vibe_translation.model_dump()
    all_seed_genres = (vibe_params.get("seed_genres") or [])[:4]
    primary_seed_genres = all_seed_genres[:2]
    fallback_seed_genres = all_seed_genres[2:4]
    primary_vibe_params = {**vibe_params, "seed_genres": primary_seed_genres}

    try:
        sp = get_spotify_client(token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Spotify client failed: {e}") from e

    try:
        candidates = get_deezer_candidates(
            target_bpm=target_bpm,
            vibe_params=primary_vibe_params,
            limit=150,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Deezer discovery failed: {e}",
        ) from e

    resolved = resolve_deezer_to_spotify(sp, candidates, limit=100)

    # Fallback: second Deezer pass using backup genres only
    if len(resolved) < 20:
        backup_genres = fallback_seed_genres or primary_seed_genres
        backup_vibe_params = {**vibe_params, "seed_genres": backup_genres[:2]}
        try:
            backup_candidates = get_deezer_candidates(
                target_bpm=target_bpm,
                vibe_params=backup_vibe_params,
                limit=150,
            )
            backup_resolved = resolve_deezer_to_spotify(sp, backup_candidates, limit=100)
        except Exception:
            backup_resolved = []

        seen = {rt.spotify_track.get("id") for rt in resolved if rt.spotify_track.get("id")}
        for rt in backup_resolved:
            tid = rt.spotify_track.get("id")
            if tid and tid not in seen:
                seen.add(tid)
                resolved.append(rt)
                if len(resolved) >= 20:
                    break

    # Last resort: generic genres when still empty (e.g. niche genres like folk/nature don't map)
    if not resolved:
        last_resort_params = {**vibe_params, "seed_genres": ["pop", "electronic"]}
        try:
            last_candidates = get_deezer_candidates(
                target_bpm=target_bpm,
                vibe_params=last_resort_params,
                limit=150,
            )
            resolved = resolve_deezer_to_spotify(sp, last_candidates, limit=100)
        except Exception:
            pass

    if not resolved:
        raise HTTPException(
            status_code=502,
            detail="No matching tracks found. Try broadening your vibe.",
        )

    spotify_track_list = [rt.spotify_track for rt in resolved]

    if settings.skip_judge_tracks:
        track_ids = [rt.spotify_track.get("id") for rt in resolved if rt.spotify_track.get("id")]
        if not track_ids:
            raise HTTPException(
                status_code=502,
                detail="No matching tracks found on Spotify for Deezer results.",
            )
        judge_result = JudgeResult(
            track_ids=track_ids,
            vibe_score=75,
            curator_note="Top 20 from Deezer discovery (BPM-matched).",
        )
    else:
        try:
            judge_result = judge_tracks(spotify_track_list, req.vibe_prompt or "custom")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Track filtering failed: {e}") from e
    resolved_by_id = {rt.spotify_track.get("id"): rt for rt in resolved if rt.spotify_track.get("id")}
    pool_ids = list(resolved_by_id.keys())
    requested_ids = judge_result.track_ids
    chosen_ids: list[str] = []
    chosen_set: set[str] = set()

    for tid in requested_ids:
        if tid in resolved_by_id and tid not in chosen_set:
            chosen_set.add(tid)
            chosen_ids.append(tid)
            if len(chosen_ids) >= 20:
                break

    if len(chosen_ids) < 20:
        for tid in pool_ids:
            if tid not in chosen_set:
                chosen_set.add(tid)
                chosen_ids.append(tid)
                if len(chosen_ids) >= 20:
                    break

    track_ids = chosen_ids[:20]

    tracks_detail: list[CurationTrack] = []
    for tid in track_ids:
        rt = resolved_by_id.get(tid)
        if not rt:
            continue
        t = rt.spotify_track
        deezer_preview = rt.deezer_preview_url
        preview_url = t.get("preview_url") or deezer_preview
        try:
            artists = [a.get("name", "") for a in (t.get("artists") or [])]
            tracks_detail.append(
                CurationTrack(
                    id=t.get("id") or tid,
                    name=t.get("name") or "Unknown",
                    artists=artists,
                    preview_url=preview_url,
                )
            )
        except Exception:
            continue

    title_suffix = req.vibe_prompt[:30] if req.vibe_prompt else (primary_seed_genres[0] if primary_seed_genres else "custom")
    generated_title = f"Run @ {req.pace_min_per_km:.1f} min/km · {title_suffix}..."
    return CurationResponse(
        track_ids=track_ids,
        tracks=tracks_detail,
        vibe_score=judge_result.vibe_score,
        curator_note=judge_result.curator_note,
        target_bpm=target_bpm,
        generated_title=generated_title,
    )
