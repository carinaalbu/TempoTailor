"""Debug endpoints for verifying API behavior (e.g. Deezer BPM search)."""

from fastapi import APIRouter
import httpx

from app.core.config import settings

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/deezer-bpm")
def debug_deezer_bpm_search(
    genre: str = "electronic",
    bpm_min: int = 157,
    bpm_max: int = 163,
    limit: int = 5,
):
    """
    Test Deezer BPM search. Returns raw Deezer response + summary.
    Fetches full track details to show actual BPM—use this to verify bpm_min/bpm_max filter.
    """
    base = settings.deezer_base_url.rstrip("/")
    q = f'genre:"{genre}" bpm_min:"{bpm_min}" bpm_max:"{bpm_max}"'
    params = {"q": q, "limit": limit, "order": "RATING_DESC"}
    try:
        r = httpx.get(f"{base}/search", params=params, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        tracks = data.get("data") or []
        total = data.get("total", 0)

        # Fetch full track for first 3 to get actual BPM (search response doesn't include it)
        sample_with_bpm = []
        for t in tracks[:3]:
            tid = t.get("id")
            if not tid:
                continue
            try:
                tr = httpx.get(f"{base}/track/{tid}", timeout=5.0)
                tr.raise_for_status()
                full = tr.json()
                sample_with_bpm.append({
                    "id": tid,
                    "title": full.get("title") or t.get("title"),
                    "artist": (full.get("artist") or {}).get("name") if isinstance(full.get("artist"), dict) else None,
                    "bpm": full.get("bpm"),
                    "in_range": bpm_min <= (full.get("bpm") or 0) <= bpm_max if full.get("bpm") is not None else None,
                })
            except Exception:
                sample_with_bpm.append({
                    "id": tid,
                    "title": t.get("title"),
                    "artist": t.get("artist", {}).get("name") if isinstance(t.get("artist"), dict) else None,
                    "bpm": None,
                    "in_range": None,
                })

        all_in_range = all(s.get("in_range") for s in sample_with_bpm if s.get("in_range") is not None)
        return {
            "query": q,
            "total": total,
            "returned": len(tracks),
            "bpm_filter_working": total > 0 and (not sample_with_bpm or all_in_range),
            "sample_tracks_with_actual_bpm": sample_with_bpm,
        }
    except Exception as e:
        return {"error": str(e), "query": q}
