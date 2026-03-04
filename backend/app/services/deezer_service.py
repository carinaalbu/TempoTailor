"""Deezer API for music discovery (chart + search, BPM filtering)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import httpx

from app.core.config import settings

BPM_TOLERANCE = 10  # ±10 BPM for more candidates; rank by closeness
MIN_BPM_MATCHES = 10  # Below this, include tracks without BPM as fallback

# Deezer chart genre IDs (chart tracks have better BPM/ISRC metadata)
_GENRE_TO_CHART_ID: dict[str, int] = {
    "electronic": 113,
    "electro": 113,
    "pop": 132,
    "rock": 152,
    "hip-hop": 116,
    "hiphop": 116,
    "rap": 116,
    "indie": 169,
    "r&b": 75,
    "r-n-b": 75,
    "rnb": 75,
    "dance": 106,
    "house": 165,
    "acoustic": 98,
    "jazz": 129,
    "folk": 98,  # map to acoustic chart
    "nature": 98,  # map to acoustic chart
}

# Search query fallback when chart ID unknown
_GENRE_ALIASES = {
    "r-n-b": "r&b",
    "r&b": "r&b",
    "hip-hop": "hip hop",
    "hiphop": "hip hop",
    "folk": "acoustic",
    "nature": "acoustic",
}


@dataclass
class DeezerCandidate:
    """Normalized track candidate from Deezer for Spotify resolution."""

    title: str
    artist: str
    isrc: str | None
    bpm: float | None
    preview_url: str | None


def _mood_terms_from_vibe(vibe_params: dict) -> list[str]:
    """Derive search mood terms from target_energy, target_valence, target_danceability (0-1)."""
    terms: list[str] = []
    energy = vibe_params.get("target_energy")
    valence = vibe_params.get("target_valence")
    dance = vibe_params.get("target_danceability")
    if energy is not None:
        if energy >= 0.7:
            terms.append("upbeat")
        elif energy <= 0.3:
            terms.append("chill")
    if valence is not None:
        if valence >= 0.7:
            terms.append("happy")
        elif valence <= 0.3:
            terms.append("melancholic")
    if dance is not None:
        if dance >= 0.7:
            terms.append("dance")
        elif dance <= 0.3:
            terms.append("ambient")
    return terms[:2]  # Cap to avoid noisy queries


def _genre_to_query(genres: list[str], vibe_params: dict | None = None) -> str:
    """Build Deezer search query from genre/mood seeds, optionally with vibe-derived terms."""
    if not genres:
        base = "electronic"
    else:
        normalized = []
        for g in genres[:5]:
            g = (g or "").strip().lower()
            if not g:
                continue
            normalized.append(_GENRE_ALIASES.get(g, g))
        base = " ".join(normalized) if normalized else "electronic"
    if vibe_params:
        mood = _mood_terms_from_vibe(vibe_params)
        if mood:
            base = f"{base} {' '.join(mood)}"
    return base


def _build_advanced_query(
    artist: str | None = None,
    track: str | None = None,
    genres: list[str] | None = None,
) -> str | None:
    """Build Deezer advanced search query (artist:\"x\" track:\"y\" genre:\"z\")."""
    parts: list[str] = []
    if artist and (a := artist.strip()):
        parts.append(f'artist:"{a}"')
    if track and (t := track.strip()):
        parts.append(f'track:"{t}"')
    if genres:
        for g in genres[:2]:
            g = (g or "").strip().lower()
            if g:
                parts.append(f'genre:"{_GENRE_ALIASES.get(g, g)}"')
    return " ".join(parts) if parts else None


def _fetch_track_bpm(track_id: int) -> dict | None:
    """Fetch full track from Deezer to get BPM."""
    base = settings.deezer_base_url.rstrip("/")
    try:
        r = httpx.get(f"{base}/track/{track_id}", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _fetch_chart_tracks(base: str, genre_id: int, limit: int) -> list[dict]:
    """Fetch chart tracks for a genre (popular tracks, better metadata)."""
    tracks: list[dict] = []
    try:
        r = httpx.get(
            f"{base}/chart/{genre_id}/tracks",
            params={"limit": min(limit, 100)},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        for t in data.get("data") or []:
            if t.get("id"):
                tracks.append(t)
    except httpx.HTTPError:
        pass
    return tracks


def _search_artists(base: str, query: str, limit: int = 5) -> list[int]:
    """Search artists by name, return Deezer artist IDs."""
    ids: list[int] = []
    try:
        r = httpx.get(
            f"{base}/search/artist",
            params={"q": query, "limit": limit},
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        for a in data.get("data") or []:
            aid = a.get("id")
            if aid:
                ids.append(aid)
    except httpx.HTTPError:
        pass
    return ids


def _fetch_artist_top_tracks(base: str, artist_id: int, limit: int) -> list[dict]:
    """Fetch top tracks for an artist."""
    tracks: list[dict] = []
    try:
        r = httpx.get(
            f"{base}/artist/{artist_id}/top",
            params={"limit": min(limit, 50)},
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        for t in data.get("data") or []:
            if t.get("id"):
                tracks.append(t)
    except httpx.HTTPError:
        pass
    return tracks


def _search_deezer(base: str, query: str, limit: int, order: str = "RATING_DESC") -> list[dict]:
    """Search Deezer and paginate to collect up to limit tracks."""
    seen_ids: set[int] = set()
    tracks: list[dict] = []
    page_limit = min(50, limit)
    try:
        r = httpx.get(
            f"{base}/search",
            params={"q": query, "limit": page_limit, "order": order},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        for t in data.get("data") or []:
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                tracks.append(t)
        next_url = data.get("next")
        while next_url and len(tracks) < limit:
            r2 = httpx.get(next_url, timeout=15.0)
            r2.raise_for_status()
            data2 = r2.json()
            for t in data2.get("data") or []:
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    tracks.append(t)
                if len(tracks) >= limit:
                    break
            next_url = data2.get("next")
            if not data2.get("data"):
                break
    except httpx.HTTPError:
        pass
    return tracks


def get_deezer_candidates(
    target_bpm: int,
    vibe_params: dict,
    limit: int = 40,
) -> list[DeezerCandidate]:
    """
    Discover via Deezer charts (primary) + search (fallback). Chart tracks have better
    BPM/ISRC metadata. Filter to target_bpm ± 10, rank by closeness. Fallback to
    tracks without BPM if few matches.
    """
    genres = vibe_params.get("seed_genres") or []
    seed_artists = vibe_params.get("seed_artists") or []
    seed_tracks = vibe_params.get("seed_tracks") or []
    base = settings.deezer_base_url.rstrip("/")

    min_bpm = max(0, target_bpm - BPM_TOLERANCE)
    max_bpm = min(250, target_bpm + BPM_TOLERANCE)
    search_limit = min(400, limit * 4)

    seen_ids: set[int] = set()
    search_tracks: list[dict] = []

    # 0. Artist-based discovery: top tracks from seed artists (when LLM provides them)
    per_artist = max(15, search_limit // max(1, len(seed_artists)))
    for artist_name in seed_artists[:5]:
        if not (artist_name or "").strip():
            continue
        for aid in _search_artists(base, artist_name.strip(), limit=3):
            for t in _fetch_artist_top_tracks(base, aid, per_artist):
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    search_tracks.append(t)
            if len(search_tracks) >= search_limit:
                break
        if len(search_tracks) >= search_limit:
            break

    # 0b. Track-based discovery: search by track name with advanced syntax
    for track_name in seed_tracks[:3]:
        if not (track_name or "").strip():
            continue
        adv = _build_advanced_query(track=track_name.strip(), genres=genres[:2])
        q = adv if adv else track_name.strip()
        for t in _search_deezer(base, q, 20):
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                search_tracks.append(t)
        if len(search_tracks) >= search_limit:
            break

    # 1. Chart-based discovery (primary): popular tracks, better BPM/ISRC
    genre_ids = [0]  # 0 = all genres chart
    for g in (genres or ["electronic"])[:5]:
        g = (g or "").strip().lower()
        if g:
            gid = _GENRE_TO_CHART_ID.get(g)
            if gid is not None and gid not in genre_ids:
                genre_ids.append(gid)
    if not genres:
        genre_ids = [0, 113, 132]  # all, electronic, pop

    per_genre = max(50, search_limit // len(genre_ids))
    for gid in genre_ids:
        if len(search_tracks) >= search_limit:
            break
        for t in _fetch_chart_tracks(base, gid, per_genre):
            tid = t.get("id")
            if tid and tid not in seen_ids:
                seen_ids.add(tid)
                search_tracks.append(t)

    # 2. Search-based discovery (fallback): more diverse, genre-specific, with mood terms
    if len(search_tracks) < search_limit // 2:
        queries: list[str] = []
        # Artist + genre advanced search when we have both
        for artist_name in (seed_artists or [])[:2]:
            if (artist_name or "").strip() and genres:
                adv = _build_advanced_query(artist=artist_name.strip(), genres=genres[:2])
                if adv:
                    queries.append(adv)
        # Genre-based queries with mood terms
        for g in (genres or ["electronic", "indie"])[:5]:
            queries.append(_genre_to_query([g], vibe_params))
        per_query = max(25, (search_limit - len(search_tracks)) // max(1, len(queries)))
        for q in queries:
            if len(search_tracks) >= search_limit:
                break
            for t in _search_deezer(base, q, per_query):
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    search_tracks.append(t)

    if not search_tracks:
        raise RuntimeError("No tracks found from Deezer for this genre/mood.")

    # Fetch BPM for each track (concurrent)
    with_bpm: list[tuple[DeezerCandidate, float]] = []  # (candidate, bpm_distance)
    without_bpm: list[DeezerCandidate] = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_track_bpm, t["id"]): t for t in search_tracks}
        for fut in as_completed(futures):
            orig = futures[fut]
            full = fut.result()
            if not full:
                continue
            artist_name = "Unknown"
            if isinstance(full.get("artist"), dict):
                artist_name = full.get("artist", {}).get("name") or artist_name
            elif isinstance(orig.get("artist"), dict):
                artist_name = orig.get("artist", {}).get("name") or artist_name
            title = full.get("title") or orig.get("title") or "Unknown"
            isrc = full.get("isrc") or orig.get("isrc")
            raw_preview = full.get("preview") or orig.get("preview")
            preview_url = raw_preview if isinstance(raw_preview, str) and raw_preview.strip() else None
            cand = DeezerCandidate(title=title, artist=artist_name, isrc=isrc, bpm=None, preview_url=preview_url)

            bpm_val = full.get("bpm")
            if bpm_val is not None:
                try:
                    bpm = float(bpm_val)
                except (TypeError, ValueError):
                    without_bpm.append(DeezerCandidate(title=title, artist=artist_name, isrc=isrc, bpm=None, preview_url=preview_url))
                    continue
                if min_bpm <= bpm <= max_bpm:
                    dist = abs(bpm - target_bpm)
                    with_bpm.append((DeezerCandidate(title=title, artist=artist_name, isrc=isrc, bpm=bpm, preview_url=preview_url), dist))
            else:
                without_bpm.append(cand)

    # Sort by closeness to target BPM, then take up to limit
    with_bpm.sort(key=lambda x: x[1])
    candidates = [c for c, _ in with_bpm]

    # Fallback: add tracks without BPM if we have too few
    if len(candidates) < MIN_BPM_MATCHES and without_bpm:
        needed = limit - len(candidates)
        candidates.extend(without_bpm[:needed])

    if not candidates:
        raise RuntimeError(
            f"No Deezer tracks in BPM range {min_bpm}-{max_bpm} for genre."
        )

    return candidates[:limit]
