import secrets
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.services.spotify_auth import get_auth_url, exchange_code_for_token

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory state store for OAuth (use Redis/DB in production)
_oauth_states: dict[str, str] = {}
# Token cache keyed by user_id (use secure storage in production)
_token_cache: dict[str, dict] = {}


def _get_frontend_url() -> str:
    return "http://localhost:5173"


@router.get("/login")
def login():
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = "pending"
    auth_url = get_auth_url(state=state)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(url=f"{_get_frontend_url()}/?error={error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    if state and state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")

    try:
        token_data = exchange_code_for_token(code)
    except Exception as e:
        return RedirectResponse(url=f"{_get_frontend_url()}/?error=auth_failed")

    # Get user id from token (we'll fetch it when we first use the token)
    access_token = token_data.get("access_token", "")
    # Store token - we'll key by a hash for now; in production use user_id from Spotify
    token_key = token_data.get("refresh_token", access_token[:32])
    _token_cache[token_key] = token_data

    # Redirect to frontend with token
    return RedirectResponse(
        url=f"{_get_frontend_url()}/?token={access_token}&refresh_token={token_data.get('refresh_token', '')}"
    )


def get_token_for_user(access_token: str) -> dict | None:
    for v in _token_cache.values():
        if v.get("access_token") == access_token:
            return v
    return None


@router.get("/me")
def me(authorization: str | None = None):
    """Validate token and return user info. Expects: Authorization: Bearer <token>"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    token = authorization.replace("Bearer ", "")
    from app.services.spotify_auth import get_spotify_client

    try:
        sp = get_spotify_client({"access_token": token})
        user = sp.current_user()
        return {
            "id": user["id"],
            "display_name": user.get("display_name"),
            "email": user.get("email"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
