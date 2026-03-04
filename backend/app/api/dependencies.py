"""Shared auth dependencies for protected endpoints."""

from fastapi import Depends, Header, HTTPException
from spotipy.exceptions import SpotifyException

from app.services.spotify_auth import get_spotify_client


def get_bearer_token(authorization: str | None = Header(None, alias="Authorization")) -> str:
    """Extract and return bearer token. Raises 401 if missing or invalid format."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    return authorization.replace("Bearer ", "").strip()


def _auth_error_detail(exc: SpotifyException) -> str:
    """Return user-facing detail for auth/scope failures."""
    status = getattr(exc, "http_status", 401)
    msg = (getattr(exc, "msg", None) or str(exc)).lower()
    if status == 403 or "scope" in msg or "insufficient" in msg:
        return "Missing permissions. Please log out and log back in to grant access."
    return "Invalid or expired token. Please log out and log back in."


def get_current_user_id(token: str = Depends(get_bearer_token)) -> str:
    """Validate token with Spotify and return user ID. Raises 401/403 if invalid or expired."""
    try:
        sp = get_spotify_client({"access_token": token})
        user = sp.current_user()
        return user["id"]
    except SpotifyException as e:
        status = getattr(e, "http_status", 401)
        if status not in (401, 403):
            status = 401
        detail = _auth_error_detail(e)
        raise HTTPException(status_code=status, detail=detail) from e
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log out and log back in.")
