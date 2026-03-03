import os

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_auth_login_redirects():
    if not os.getenv("SPOTIFY_CLIENT_ID"):
        return  # Skip when no credentials
    r = client.get("/auth/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "spotify.com" in r.headers.get("location", "")


def test_auth_me_requires_auth():
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert "authorization" in r.json().get("detail", "").lower()


def test_auth_me_invalid_token():
    r = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert r.status_code == 401


def test_auth_callback_missing_code_redirects():
    r = client.get("/auth/callback", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "error=missing_code" in r.headers.get("location", "")


def test_auth_callback_invalid_state_redirects():
    r = client.get("/auth/callback?code=abc&state=invalid-state", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "error=invalid_state" in r.headers.get("location", "")


def test_auth_refresh_missing_token():
    r = client.post("/auth/refresh", json={})
    assert r.status_code == 422  # Pydantic validation error for missing field


def test_auth_refresh_invalid_token():
    r = client.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert r.status_code == 401


def test_curation_requires_auth():
    r = client.post("/curation", json={"pace_min_per_km": 5.5, "vibe_prompt": "test"})
    assert r.status_code == 401


def test_drafts_require_auth():
    r = client.get("/drafts")
    assert r.status_code == 401
