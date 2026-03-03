"""Deezer API for music discovery (genre search + BPM filtering)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import httpx

from app.core.config import settings
BPM_TOLERANCE = 5

# Map LLM/Spotify genre names to Deezer-friendly search terms
_GENRE_ALIASES = {
    "r-n-b": "r&b",
    "r&b": "r&b",
    "hip-hop": "hip hop",
    "hiphop": "hip hop",
}


@dataclass
class DeezerCandidate:
    """Normalized track candidate from Deezer for Spotify resolution."""

    title: str
    artist: str
    isrc: str | None
    bpm: float | None


def _genre_to_query(genres: list[str]) -> str:
    """Build Deezer search query from genre/mood seeds."""
    if not genres:
        return "electronic"
    normalized = []
    for g in genres[:5]:
        g = (g or "").strip().lower()
        if not g:
            continue
        normalized.append(_GENRE_ALIASES.get(g, g))
    return " ".join(normalized) if normalized else "electronic"


def _fetch_track_bpm(track_id: int) -> dict | None:
    """Fetch full track from Deezer to get BPM."""
    base = settings.deezer_base_url.rstrip("/")
    try:
        r = httpx.get(f"{base}/track/{track_id}", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_deezer_candidates(
    target_bpm: int,
    vibe_params: dict,
    limit: int = 40,
) -> list[DeezerCandidate]:
    """
    Search Deezer by genre/mood, fetch BPM per track, filter to target_bpm ± 5.
    Returns normalized candidates (title, artist, isrc, bpm) for Spotify resolution.
    """
    genres = vibe_params.get("seed_genres") or []
    query = _genre_to_query(genres)

    min_bpm = max(0, target_bpm - BPM_TOLERANCE)
    max_bpm = min(250, target_bpm + BPM_TOLERANCE)

    # Over-fetch from search to have enough after BPM filter
    search_limit = min(100, limit * 4)
    seen_ids: set[int] = set()
    search_tracks: list[dict] = []

    base = settings.deezer_base_url.rstrip("/")
    try:
        r = httpx.get(
            f"{base}/search",
            params={"q": query, "limit": min(25, search_limit)},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        items = data.get("data") or []
        for t in items:
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                search_tracks.append(t)

        # Paginate if needed (next URL is absolute)
        next_url = data.get("next")
        while next_url and len(search_tracks) < search_limit:
            r2 = httpx.get(next_url, timeout=15.0)
            r2.raise_for_status()
            data2 = r2.json()
            items2 = data2.get("data") or []
            for t in items2:
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    search_tracks.append(t)
                if len(search_tracks) >= search_limit:
                    break
            next_url = data2.get("next")
            if not items2:
                break
    except httpx.HTTPError as e:
        raise RuntimeError(f"Deezer search failed: {e}") from e

    if not search_tracks:
        raise RuntimeError("No tracks found from Deezer for this genre/mood.")

    # Fetch BPM for each track (concurrent)
    candidates: list[DeezerCandidate] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_track_bpm, t["id"]): t for t in search_tracks}
        for fut in as_completed(futures):
            orig = futures[fut]
            full = fut.result()
            if not full:
                continue
            bpm_val = full.get("bpm")
            if bpm_val is None:
                continue
            try:
                bpm = float(bpm_val)
            except (TypeError, ValueError):
                continue
            if not (min_bpm <= bpm <= max_bpm):
                continue
            artist_name = "Unknown"
            if isinstance(full.get("artist"), dict):
                artist_name = full.get("artist", {}).get("name") or artist_name
            elif isinstance(orig.get("artist"), dict):
                artist_name = orig.get("artist", {}).get("name") or artist_name
            title = full.get("title") or orig.get("title") or "Unknown"
            isrc = full.get("isrc") or orig.get("isrc")
            candidates.append(
                DeezerCandidate(
                    title=title,
                    artist=artist_name,
                    isrc=isrc,
                    bpm=bpm,
                )
            )
            if len(candidates) >= limit:
                break

    if not candidates:
        raise RuntimeError(
            f"No Deezer tracks in BPM range {min_bpm}-{max_bpm} for genre '{query}'."
        )

    return candidates[:limit]
