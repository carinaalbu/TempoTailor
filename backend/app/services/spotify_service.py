"""Spotify API interactions for playlist creation and track resolution."""

from spotipy import Spotify

from app.services.spotify_auth import get_spotify_client


def _sanitize_search_term(s: str) -> str:
    """Escape characters that break Spotify search."""
    return s.replace('"', "").strip() or "Unknown"


def resolve_deezer_to_spotify(
    sp: Spotify,
    candidates: list,
    limit: int = 20,
) -> list[dict]:
    """
    Resolve Deezer candidates to Spotify tracks.
    Tries ISRC first, then track+artist search. Deduplicates by Spotify ID.
    Returns list of Spotify track dicts (id, name, artists, preview_url).
    """
    seen_ids: set[str] = set()
    tracks: list[dict] = []

    for c in candidates:
        if len(tracks) >= limit:
            break
        spotify_track = None

        # 1. Try ISRC first if available
        if getattr(c, "isrc", None) and str(c.isrc).strip():
            try:
                q = f"isrc:{_sanitize_search_term(str(c.isrc))}"
                result = sp.search(q=q, type="track", limit=1)
                items = (result.get("tracks") or {}).get("items") or []
                if items:
                    t = items[0]
                    tid = t.get("id")
                    if tid and tid not in seen_ids:
                        spotify_track = t
            except Exception:
                pass

        # 2. Fallback: track + artist
        if not spotify_track:
            try:
                title = _sanitize_search_term(getattr(c, "title", "") or "Unknown")
                artist = _sanitize_search_term(getattr(c, "artist", "") or "Unknown")
                q = f'track:"{title}" artist:"{artist}"'
                result = sp.search(q=q, type="track", limit=1)
                items = (result.get("tracks") or {}).get("items") or []
                if items:
                    t = items[0]
                    tid = t.get("id")
                    if tid and tid not in seen_ids:
                        spotify_track = t
            except Exception:
                pass

        if spotify_track:
            tid = spotify_track.get("id")
            if tid:
                seen_ids.add(tid)
                tracks.append(spotify_track)

    return tracks[:limit]
