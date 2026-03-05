import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.oauth_state import OAuthState
from app.schemas.auth import RefreshRequest
from app.services.spotify_auth import (
    exchange_code_for_token,
    get_auth_url,
    get_spotify_client,
    refresh_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Fallback in-memory state if DB fails (e.g. oauth_states table missing)
_fallback_states: set[str] = set()


def _get_frontend_url() -> str:
    return settings.frontend_url


def _redirect_error(error: str) -> RedirectResponse:
    params = urlencode({"error": error})
    return RedirectResponse(url=f"{_get_frontend_url()}/?{params}")


def _store_state(state: str, db: Session) -> None:
    """Store OAuth state in DB, or fallback to in-memory if DB fails."""
    try:
        db.add(OAuthState(state=state))
        db.commit()
    except Exception:
        db.rollback()
        _fallback_states.add(state)


def _validate_state(state: str, db: Session) -> bool:
    """Validate OAuth state from DB or fallback in-memory store."""
    try:
        row = db.query(OAuthState).filter(OAuthState.state == state).first()
        if row:
            db.delete(row)
            db.commit()
            return True
        if state in _fallback_states:
            _fallback_states.discard(state)
            return True
        return False
    except Exception:
        db.rollback()
        if state in _fallback_states:
            _fallback_states.discard(state)
            return True
        return False


@router.get("/login")
def login(db: Session = Depends(get_db)):
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Spotify credentials not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in backend/.env",
        )
    try:
        state = secrets.token_urlsafe(32)
        _store_state(state, db)
        auth_url = get_auth_url(state=state)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {type(e).__name__}: {str(e)}",
        ) from e


@router.get("/callback")
def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        return _redirect_error(error)
    if not code:
        return _redirect_error("missing_code")
    if state:
        if not _validate_state(state, db):
            return _redirect_error("invalid_state")

    try:
        token_data = exchange_code_for_token(code)
    except Exception:
        return _redirect_error("auth_failed")

    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")

    params = urlencode({
        "token": access_token,
        "refresh_token": refresh_token,
    })
    return RedirectResponse(url=f"{_get_frontend_url()}/?{params}")


@router.post("/refresh")
def refresh(body: RefreshRequest):
    """Exchange refresh token for new access token. Body: { \"refresh_token\": \"...\" }"""
    refresh_token = body.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")
    try:
        token_data = refresh_access_token(refresh_token)
        return {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token", refresh_token),
            "expires_in": token_data.get("expires_in"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token refresh failed")


@router.get("/me")
def me(authorization: str | None = Header(None, alias="Authorization")):
    """Validate token and return user info. Expects: Authorization: Bearer <token>"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    token = authorization.replace("Bearer ", "")
    from app.services.spotify_auth import get_spotify_client

    try:
        sp = get_spotify_client({"access_token": token})
        user = sp.current_user()
        images = user.get("images") or []
        image_url = images[0].get("url") if images and isinstance(images[0], dict) else None
        return {
            "id": user["id"],
            "display_name": user.get("display_name"),
            "email": user.get("email"),
            "image_url": image_url,
        }
    except Exception as e:
        from spotipy.exceptions import SpotifyException

        if isinstance(e, SpotifyException) and getattr(e, "http_status", None) == 403:
            raise HTTPException(
                status_code=403,
                detail="Missing permissions. Please log out and log in again to grant access.",
            ) from e
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e
