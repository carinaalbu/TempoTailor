"""Audio preview endpoints for just-in-time Deezer preview URL fetching."""

from fastapi import APIRouter, HTTPException

from app.services.deezer_service import fetch_fresh_preview_url

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/preview/{deezer_track_id}")
def get_fresh_preview_url(deezer_track_id: int):
    """
    Fetch a fresh Deezer preview URL for the given track ID.
    Use this when playing audio to avoid expired cached URLs.
    """
    url = fetch_fresh_preview_url(deezer_track_id)
    if url is None:
        raise HTTPException(
            status_code=404,
            detail="Preview not available for this track",
        )
    return {"preview_url": url}
