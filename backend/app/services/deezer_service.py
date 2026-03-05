"""Deezer API for music discovery (chart + search, BPM filtering)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import NamedTuple

import httpx

from app.core.config import settings

BPM_VARIANCE = 8  # ±8 BPM for base range (no half/double—users want actual cadence)
MIN_BPM_MATCHES = 10  # Below this, include tracks without BPM as fallback
NEAR_BASE_TOLERANCE = 12  # When few harmonic matches, also accept ±12 of base
SEED_ARTIST_BPM_TOLERANCE = 20  # ±20 BPM for seed artist tracks (user asked for them)
HARMONIC_SEARCH_LIMIT = 50  # Tracks per parallel BPM-range query

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


class BpmRange(NamedTuple):
    """BPM range for harmonic entrainment search."""

    min_bpm: int
    max_bpm: int


def calculate_harmonic_bpm_ranges(
    target_cadence: int,
    variance: int = BPM_VARIANCE,
) -> dict[str, BpmRange]:
    """
    Calculate base, half-time, and double-time BPM ranges for harmonic entrainment.
    Runners can lock into music at 1x, 0.5x, or 2x the stated BPM.
    """
    base_bpm = target_cadence
    half_time_bpm = target_cadence // 2
    double_time_bpm = target_cadence * 2

    return {
        "base": BpmRange(
            min_bpm=max(0, base_bpm - variance),
            max_bpm=base_bpm + variance,
        ),
        "half_time": BpmRange(
            min_bpm=max(0, half_time_bpm - variance),
            max_bpm=half_time_bpm + variance,
        ),
        "double_time": BpmRange(
            min_bpm=max(0, double_time_bpm - variance),
            max_bpm=double_time_bpm + variance,
        ),
    }


def _bpm_in_any_harmonic_range(bpm: float, ranges: dict[str, BpmRange]) -> bool:
    """Check if BPM falls within any of the harmonic entrainment ranges."""
    for r in ranges.values():
        if r.min_bpm <= bpm <= r.max_bpm:
            return True
    return False


def _bpm_near_base(bpm: float, target_cadence: int, tolerance: int = NEAR_BASE_TOLERANCE) -> bool:
    """Check if BPM is within tolerance of base target (fallback when harmonic yields few)."""
    return abs(bpm - target_cadence) <= tolerance


def _is_seed_artist(artist_name: str, seed_artists: list[str]) -> bool:
    """Check if artist matches any seed artist (case-insensitive, partial)."""
    artist_lower = (artist_name or "").lower()
    for seed in (seed_artists or []):
        if not (seed or "").strip():
            continue
        if seed.strip().lower() in artist_lower or artist_lower in seed.strip().lower():
            return True
    return False


def _closest_harmonic_distance(bpm: float, target_cadence: int) -> float:
    """Distance to closest harmonic target (base, half, or double)."""
    base = target_cadence
    half = target_cadence / 2
    double = target_cadence * 2
    return min(abs(bpm - base), abs(bpm - half), abs(bpm - double))


@dataclass
class DeezerCandidate:
    """Normalized track candidate from Deezer for Spotify resolution."""

    title: str
    artist: str
    isrc: str | None
    bpm: float | None
    preview_url: str | None
    deezer_track_id: int | None = None


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
    """Fetch full track from Deezer to get BPM. Use HTTP to get non-signed preview URLs."""
    base = settings.deezer_base_url.rstrip("/").replace("https://", "http://", 1)
    try:
        r = httpx.get(f"{base}/track/{track_id}", timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_fresh_preview_url(deezer_track_id: int) -> str | None:
    """
    Fetch a fresh preview URL from Deezer for the given track ID.
    Deezer preview URLs are signed and expire; this fetches a new one on demand.
    """
    base = settings.deezer_base_url.rstrip("/")
    try:
        r = httpx.get(f"{base}/track/{deezer_track_id}", timeout=10.0)
        r.raise_for_status()
        data = r.json()
        raw_preview = data.get("preview")
        if isinstance(raw_preview, str) and raw_preview.strip():
            return raw_preview
        return None
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


def _search_deezer_with_bpm(
    base: str,
    genre: str,
    bpm_min: int,
    bpm_max: int,
    limit: int = HARMONIC_SEARCH_LIMIT,
) -> list[dict]:
    """
    Search Deezer with BPM filter using advanced query syntax.
    q string format: genre:"pop" bpm_min:"120" bpm_max:"130"
    """
    genre_normalized = _GENRE_ALIASES.get(genre.strip().lower(), genre.strip().lower())
    q = f'genre:"{genre_normalized}" bpm_min:"{bpm_min}" bpm_max:"{bpm_max}"'
    params: dict = {"q": q, "limit": min(limit, 50), "order": "RATING_DESC"}
    try:
        r = httpx.get(f"{base}/search", params=params, timeout=15.0)
        r.raise_for_status()
        data = r.json()
        return list(data.get("data") or [])
    except httpx.HTTPError:
        return []


def _deduplicate_tracks(tracks: list[dict]) -> list[dict]:
    """Remove duplicates by Deezer ID or ISRC, keeping first occurrence."""
    seen_ids: set[int] = set()
    seen_isrcs: set[str] = set()
    deduped: list[dict] = []
    for t in tracks:
        tid = t.get("id")
        isrc = t.get("isrc") if isinstance(t.get("isrc"), str) else None
        key_id = tid
        key_isrc = (isrc or "").strip().upper() if isrc else None

        if key_id and key_id in seen_ids:
            continue
        if key_isrc and key_isrc in seen_isrcs:
            continue

        if key_id:
            seen_ids.add(key_id)
        if key_isrc:
            seen_isrcs.add(key_isrc)
        deduped.append(t)
    return deduped


def get_deezer_candidates(
    target_bpm: int,
    vibe_params: dict,
    limit: int = 40,
) -> list[DeezerCandidate]:
    """
    Harmonic Entrainment: fetch base, half-time, and double-time BPM ranges in parallel
    to massively expand the candidate pool. Merge, deduplicate by ISRC/Deezer ID, then
    filter to tracks in any harmonic range for the LLM judge.
    """
    genres = vibe_params.get("seed_genres") or []
    seed_artists = vibe_params.get("seed_artists") or []
    seed_tracks = vibe_params.get("seed_tracks") or []
    base = settings.deezer_base_url.rstrip("/")

    ranges = calculate_harmonic_bpm_ranges(target_bpm)
    genres_to_query = list(dict.fromkeys(
        (genres or ["electronic"])[:3] + ["pop", "dance"]  # Always add pop/dance (BPM-rich)
    ))[:5]  # Up to 5 genres, deduped, pop/dance ensure diversity

    # 1. Parallel API queries: BASE BPM only (no half-time/double-time—users want actual cadence)
    # Half-time (e.g. 85 for target 170) feels wrong; prioritize songs that match target BPM.
    def _fetch_one(genre: str, rng: BpmRange) -> list[dict]:
        return _search_deezer_with_bpm(
            base, genre, rng.min_bpm, rng.max_bpm, limit=HARMONIC_SEARCH_LIMIT
        )

    tasks = [(g, ranges["base"]) for g in genres_to_query]
    with ThreadPoolExecutor(max_workers=min(9, len(tasks))) as ex:
        futures = [ex.submit(_fetch_one, g, r) for g, r in tasks]
        raw_results: list[list[dict]] = [f.result() for f in futures]

    candidate_tracks: list[dict] = []
    for batch in raw_results:
        candidate_tracks.extend(batch)

    seen_ids: set[int] = {t.get("id") for t in candidate_tracks if t.get("id")}
    search_limit = min(400, limit * 6)

    # Always run artist-based discovery when user mentions artists—ensures their songs appear
    if seed_artists:
        per_artist = max(25, search_limit // max(1, len(seed_artists)))
        for artist_name in seed_artists[:5]:
            if not (artist_name or "").strip():
                continue
            for aid in _search_artists(base, artist_name.strip(), limit=3):
                for t in _fetch_artist_top_tracks(base, aid, per_artist):
                    tid = t.get("id")
                    if tid and tid not in seen_ids:
                        seen_ids.add(tid)
                        candidate_tracks.append(t)
                if len(candidate_tracks) >= search_limit:
                    break
            if len(candidate_tracks) >= search_limit:
                break

    # Always run track-based discovery when user mentions specific songs
    if seed_tracks:
        for track_name in seed_tracks[:3]:
            if not (track_name or "").strip():
                continue
            adv = _build_advanced_query(track=track_name.strip(), genres=genres[:2])
            q = adv if adv else track_name.strip()
            for t in _search_deezer(base, q, 25):
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    candidate_tracks.append(t)
            if len(candidate_tracks) >= search_limit:
                break

    # Fallback: when BPM-filtered + artist/track discovery yields very few (< 25), add chart/search
    FALLBACK_THRESHOLD = 25
    if len(candidate_tracks) < FALLBACK_THRESHOLD:
        # Chart-based discovery (parallel across genres)
        genre_ids = [0]
        for g in (genres or ["electronic"])[:5]:
            g = (g or "").strip().lower()
            if g:
                gid = _GENRE_TO_CHART_ID.get(g)
                if gid is not None and gid not in genre_ids:
                    genre_ids.append(gid)
        if not genres:
            genre_ids = [0, 113, 132]

        per_genre = max(50, search_limit // len(genre_ids))
        for gid in genre_ids:
            if len(candidate_tracks) >= search_limit:
                break
            for t in _fetch_chart_tracks(base, gid, per_genre):
                tid = t.get("id")
                if tid and tid not in seen_ids:
                    seen_ids.add(tid)
                    candidate_tracks.append(t)

        # Search-based discovery
        if len(candidate_tracks) < search_limit // 2:
            for g in (genres or ["electronic", "indie"])[:5]:
                q = _genre_to_query([g], vibe_params)
                for t in _search_deezer(base, q, per_genre := max(25, search_limit // 5)):
                    tid = t.get("id")
                    if tid and tid not in seen_ids:
                        seen_ids.add(tid)
                        candidate_tracks.append(t)
                    if len(candidate_tracks) >= search_limit:
                        break

    # 2. Aggregate and deduplicate by ISRC or Deezer ID
    candidate_tracks = _deduplicate_tracks(candidate_tracks)

    if not candidate_tracks:
        raise RuntimeError("No tracks found from Deezer for this genre/mood.")

    # 3. Fetch BPM for each track (concurrent), filter to harmonic ranges
    with_bpm: list[tuple[DeezerCandidate, float]] = []
    near_base: list[tuple[DeezerCandidate, float]] = []  # Fallback when few harmonic matches
    seed_artist_tracks: list[tuple[DeezerCandidate, float]] = []  # User-requested artists, ±20 BPM
    without_bpm: list[DeezerCandidate] = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_fetch_track_bpm, t["id"]): t for t in candidate_tracks}
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
            deezer_track_id = full.get("id") or orig.get("id")
            cand = DeezerCandidate(
                title=title,
                artist=artist_name,
                isrc=isrc,
                bpm=None,
                preview_url=preview_url,
                deezer_track_id=deezer_track_id,
            )

            bpm_val = full.get("bpm")
            if bpm_val is not None:
                try:
                    bpm = float(bpm_val)
                except (TypeError, ValueError):
                    without_bpm.append(cand)
                    continue
                cand_with_bpm = DeezerCandidate(
                    title=title,
                    artist=artist_name,
                    isrc=isrc,
                    bpm=bpm,
                    preview_url=preview_url,
                    deezer_track_id=deezer_track_id,
                )
                # Base BPM only—no half-time/double-time (users want actual cadence match)
                base_rng = ranges["base"]
                if base_rng.min_bpm <= bpm <= base_rng.max_bpm:
                    dist = abs(bpm - target_bpm)
                    with_bpm.append((cand_with_bpm, dist))
                elif _bpm_near_base(bpm, target_bpm):
                    dist = abs(bpm - target_bpm)
                    near_base.append((cand_with_bpm, dist))
                elif seed_artists and _is_seed_artist(artist_name, seed_artists) and abs(bpm - target_bpm) <= SEED_ARTIST_BPM_TOLERANCE:
                    dist = abs(bpm - target_bpm)
                    seed_artist_tracks.append((cand_with_bpm, dist))
            else:
                # No BPM: include if from seed artist (user asked for them)
                if seed_artists and _is_seed_artist(artist_name, seed_artists):
                    seed_artist_tracks.append((cand, 999.0))  # Lower priority
                else:
                    without_bpm.append(cand)

    with_bpm.sort(key=lambda x: x[1])
    candidates = [c for c, _ in with_bpm]

    # When harmonic yields few, add near-base (±12 of target) to expand pool
    if len(candidates) < 30 and near_base:
        near_base.sort(key=lambda x: x[1])
        needed = min(limit - len(candidates), len(near_base))
        candidates.extend(c for c, _ in near_base[:needed])

    # Always add seed artist tracks (user explicitly asked for them), up to 10
    if seed_artist_tracks:
        seed_artist_tracks.sort(key=lambda x: x[1])
        seen_ids_cand = {c.deezer_track_id for c in candidates if c.deezer_track_id}
        added = 0
        for c, _ in seed_artist_tracks:
            if added >= 10 or len(candidates) >= limit:
                break
            if c.deezer_track_id and c.deezer_track_id not in seen_ids_cand:
                seen_ids_cand.add(c.deezer_track_id)
                candidates.append(c)
                added += 1

    if len(candidates) < MIN_BPM_MATCHES and without_bpm:
        needed = limit - len(candidates)
        candidates.extend(without_bpm[:needed])

    if not candidates:
        raise RuntimeError(
            f"No Deezer tracks in harmonic BPM ranges (base/half/double) for genre."
        )

    return candidates[:limit]
