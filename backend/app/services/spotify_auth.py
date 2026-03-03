from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

from app.core.config import settings

SCOPE = (
    "user-read-private user-read-email "
    "playlist-modify-public playlist-modify-private "
    "user-library-read"
)


def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope=SCOPE,
        cache_path=None,
    )


def get_auth_url(state: str | None = None) -> str:
    oauth = get_spotify_oauth()
    return oauth.get_authorize_url(state=state or "")


def exchange_code_for_token(code: str) -> dict:
    oauth = get_spotify_oauth()
    return oauth.get_access_token(code, as_dict=True)


def get_spotify_client(token: dict) -> Spotify:
    return Spotify(auth=token.get("access_token"))
