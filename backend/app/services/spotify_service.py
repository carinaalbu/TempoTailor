"""Spotify API interactions for recommendations and playlist creation."""

from spotipy import Spotify

from app.services.spotify_auth import get_spotify_client


def get_recommendations(
    token: dict,
    target_bpm: int,
    vibe_params: dict,
    limit: int = 40,
) -> list[dict]:
    """Over-fetch track recommendations from Spotify."""
    sp = get_spotify_client(token)
    min_tempo = max(0, target_bpm - 10)
    max_tempo = min(250, target_bpm + 10)
    kwargs: dict = {
        "limit": limit,
        "min_tempo": min_tempo,
        "max_tempo": max_tempo,
        "target_energy": vibe_params.get("target_energy", 0.7),
        "target_valence": vibe_params.get("target_valence", 0.6),
        "target_danceability": vibe_params.get("target_danceability", 0.7),
    }
    if vibe_params.get("seed_genres"):
        kwargs["seed_genres"] = vibe_params["seed_genres"][:5]
    if vibe_params.get("seed_artists"):
        kwargs["seed_artists"] = vibe_params["seed_artists"][:5]
    if vibe_params.get("seed_tracks"):
        kwargs["seed_tracks"] = vibe_params["seed_tracks"][:5]
    # Ensure at least one seed
    if not kwargs.get("seed_genres") and not kwargs.get("seed_artists") and not kwargs.get("seed_tracks"):
        kwargs["seed_genres"] = ["pop", "electronic"]
    recs = sp.recommendations(**kwargs)
    return recs.get("tracks", [])
