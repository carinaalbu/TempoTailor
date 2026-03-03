from fastapi import APIRouter, Header, HTTPException

from app.schemas.curation import CurationRequest, CurationResponse, CurationTrack
from app.services.pace_service import pace_to_bpm
from app.services.llm_service import translate_vibe, judge_tracks
from app.services.spotify_service import get_recommendations
from app.services.spotify_auth import get_spotify_client

router = APIRouter(prefix="/curation", tags=["curation"])


@router.post("", response_model=CurationResponse)
def create_curation(
    req: CurationRequest,
    authorization: str | None = Header(None, alias="Authorization"),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    token = {"access_token": authorization.replace("Bearer ", "")}

    target_bpm = pace_to_bpm(req.pace_min_per_km)
    try:
        vibe_translation = translate_vibe(req.vibe_prompt)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=f"Vibe translation failed: {e}") from e
    vibe_params = vibe_translation.model_dump()

    raw_tracks = get_recommendations(
        token=token,
        target_bpm=target_bpm,
        vibe_params=vibe_params,
        limit=40,
    )

    if not raw_tracks:
        raise HTTPException(status_code=502, detail="No recommendations from Spotify")

    try:
        judge_result = judge_tracks(raw_tracks, req.vibe_prompt)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=f"Track filtering failed: {e}") from e
    track_ids = judge_result.track_ids

    sp = get_spotify_client(token)
    tracks_detail: list[CurationTrack] = []
    for tid in track_ids:
        t = next((x for x in raw_tracks if x.get("id") == tid), None)
        if not t:
            try:
                t = sp.track(tid)
            except Exception:
                continue
        artists = [a.get("name", "") for a in t.get("artists", [])]
        tracks_detail.append(
            CurationTrack(
                id=t["id"],
                name=t.get("name", "Unknown"),
                artists=artists,
                preview_url=t.get("preview_url"),
            )
        )

    generated_title = f"Run @ {req.pace_min_per_km:.1f} min/km · {req.vibe_prompt[:30]}..."
    return CurationResponse(
        track_ids=track_ids,
        tracks=tracks_detail,
        vibe_score=judge_result.vibe_score,
        curator_note=judge_result.curator_note,
        target_bpm=target_bpm,
        generated_title=generated_title,
    )
