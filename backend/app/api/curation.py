from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_bearer_token
from app.core.config import settings
from app.schemas.curation import CurationRequest, CurationResponse, CurationTrack
from app.schemas.llm import JudgeResult
from app.schemas.llm import VibeTranslation
from app.services.pace_service import pace_to_bpm
from app.services.llm_service import translate_vibe, judge_tracks
from app.services.deezer_service import get_deezer_candidates
from app.services.spotify_service import resolve_deezer_to_spotify
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
            seed_genres=req.seed_genres[:5],
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

    try:
        sp = get_spotify_client(token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Spotify client failed: {e}") from e

    try:
        candidates = get_deezer_candidates(
            target_bpm=target_bpm,
            vibe_params=vibe_params,
            limit=40,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Deezer discovery failed: {e}",
        ) from e

    raw_tracks = resolve_deezer_to_spotify(sp, candidates, limit=40)

    if not raw_tracks:
        raise HTTPException(
            status_code=502,
            detail="No matching tracks found on Spotify for Deezer results.",
        )

    if settings.skip_judge_tracks:
        track_ids = [t.get("id") for t in raw_tracks[:20] if t.get("id")]
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
            judge_result = judge_tracks(raw_tracks, req.vibe_prompt or "custom")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Track filtering failed: {e}") from e
    track_ids = judge_result.track_ids

    tracks_detail: list[CurationTrack] = []
    for tid in track_ids:
        t = next((x for x in raw_tracks if x.get("id") == tid), None)
        if not t:
            try:
                t = sp.track(tid)
            except Exception:
                continue
        if not t:
            continue
        try:
            artists = [a.get("name", "") for a in (t.get("artists") or [])]
            tracks_detail.append(
                CurationTrack(
                    id=t.get("id") or tid,
                    name=t.get("name") or "Unknown",
                    artists=artists,
                    preview_url=t.get("preview_url"),
                )
            )
        except Exception:
            continue

    title_suffix = req.vibe_prompt[:30] if req.vibe_prompt else (req.seed_genres[0] if req.seed_genres else "custom")
    generated_title = f"Run @ {req.pace_min_per_km:.1f} min/km · {title_suffix}..."
    return CurationResponse(
        track_ids=track_ids,
        tracks=tracks_detail,
        vibe_score=judge_result.vibe_score,
        curator_note=judge_result.curator_note,
        target_bpm=target_bpm,
        generated_title=generated_title,
    )
