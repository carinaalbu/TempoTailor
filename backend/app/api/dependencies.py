"""Shared auth dependencies for protected endpoints."""

from fastapi import Depends, Header, HTTPException

from app.services.spotify_auth import get_spotify_client


def get_bearer_token(authorization: str | None = Header(None, alias="Authorization")) -> str:
    """Extract and return bearer token. Raises 401 if missing or invalid format."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    return authorization.replace("Bearer ", "").strip()


def get_current_user_id(token: str = Depends(get_bearer_token)) -> str:
    """Validate token with Spotify and return user ID. Raises 401 if invalid or expired."""
    try:
        sp = get_spotify_client({"access_token": token})
        user = sp.current_user()
        return user["id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
