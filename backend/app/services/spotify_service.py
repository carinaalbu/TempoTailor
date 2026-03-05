"""Spotify API interactions for playlist creation and track resolution."""

import re
from dataclasses import dataclass

from spotipy import Spotify

from app.services.spotify_auth import get_spotify_client


@dataclass
class ResolvedTrack:
    """Spotify track plus optional Deezer preview URL and track ID for JIT fetching."""

    spotify_track: dict
    deezer_preview_url: str | None
    deezer_track_id: int | None = None


def _sanitize_search_term(s: str) -> str:
    """Escape characters that break Spotify search."""
    return s.replace('"', "").strip() or "Unknown"


def _simplify_title(title: str) -> str:
    """Strip parentheticals, feat., remix etc. for looser matching."""
    s = title
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", s)
    s = re.sub(r"\s+feat\.?\s+[^-–—]+", "", s, flags=re.I)
    s = re.sub(r"\s+ft\.?\s+[^-–—]+", "", s, flags=re.I)
    s = re.sub(r"\s*[-–—]\s*.*$", "", s)
    return _sanitize_search_term(s) or "Unknown"


def _pick_best_match(items: list[dict], artist: str, seen_ids: set[str]) -> dict | None:
    """Pick best match from search results (prefer artist match, exclude seen)."""
    artist_lower = (artist or "").lower()
    for t in items:
        tid = t.get("id")
        if not tid or tid in seen_ids:
            continue
        artists = t.get("artists") or []
        names = [a.get("name", "").lower() for a in artists if a.get("name")]
        if artist_lower and any(artist_lower in n or n in artist_lower for n in names):
            return t
        if not artist_lower:
            return t
    for t in items:
        tid = t.get("id")
        if tid and tid not in seen_ids:
            return t
    return None


def resolve_deezer_to_spotify(
    sp: Spotify,
    candidates: list,
    limit: int = 20,
) -> list[ResolvedTrack]:
    """
    Resolve Deezer candidates to Spotify tracks.
    Tries ISRC first, then exact track+artist, then simplified query. Deduplicates.
    Returns list of ResolvedTrack (spotify_track, deezer_preview_url) for preview fallback.
    """
    seen_ids: set[str] = set()
    tracks: list[ResolvedTrack] = []

    for c in candidates:
        if len(tracks) >= limit:
            break
        spotify_track = None
        title = _sanitize_search_term(getattr(c, "title", "") or "Unknown")
        artist = _sanitize_search_term(getattr(c, "artist", "") or "Unknown")

        # 1. Try ISRC first if available
        if getattr(c, "isrc", None) and str(c.isrc).strip():
            try:
                q = f"isrc:{_sanitize_search_term(str(c.isrc))}"
                result = sp.search(q=q, type="track", limit=5)
                items = (result.get("tracks") or {}).get("items") or []
                spotify_track = _pick_best_match(items, artist, seen_ids)
            except Exception:
                pass

        # 2. Exact track + artist
        if not spotify_track and title != "Unknown" and artist != "Unknown":
            try:
                q = f'track:"{title}" artist:"{artist}"'
                result = sp.search(q=q, type="track", limit=5)
                items = (result.get("tracks") or {}).get("items") or []
                spotify_track = _pick_best_match(items, artist, seen_ids)
            except Exception:
                pass

        # 3. Simplified title (no parentheticals, feat., etc.)
        if not spotify_track:
            simple = _simplify_title(getattr(c, "title", "") or "")
            if simple and simple != "Unknown":
                try:
                    q = f'track:"{simple}" artist:"{artist}"' if artist != "Unknown" else f'track:"{simple}"'
                    result = sp.search(q=q, type="track", limit=5)
                    items = (result.get("tracks") or {}).get("items") or []
                    spotify_track = _pick_best_match(items, artist, seen_ids)
                except Exception:
                    pass

        # 4. Fuzzy: artist + partial title
        if not spotify_track and artist != "Unknown":
            try:
                words = title.split()[:4]
                partial = " ".join(w for w in words if len(w) > 2)[:40]
                if partial:
                    q = f'{partial} artist:"{artist}"'
                    result = sp.search(q=q, type="track", limit=5)
                    items = (result.get("tracks") or {}).get("items") or []
                    spotify_track = _pick_best_match(items, artist, seen_ids)
            except Exception:
                pass

        if spotify_track:
            tid = spotify_track.get("id")
            if tid:
                seen_ids.add(tid)
                deezer_preview = getattr(c, "preview_url", None)
                deezer_track_id = getattr(c, "deezer_track_id", None)
                tracks.append(ResolvedTrack(spotify_track=spotify_track, deezer_preview_url=deezer_preview, deezer_track_id=deezer_track_id))

    return tracks[:limit]
