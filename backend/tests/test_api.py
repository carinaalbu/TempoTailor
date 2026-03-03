import os

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_auth_login_redirects():
    if not os.getenv("SPOTIPY_CLIENT_ID"):
        return  # Skip assertion when no credentials
    r = client.get("/auth/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "spotify.com" in r.headers.get("location", "")


def test_curation_requires_auth():
    r = client.post("/curation", json={"pace_min_per_km": 5.5, "vibe_prompt": "test"})
    assert r.status_code == 401
