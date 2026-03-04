from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy.orm import Session

from app.api.dependencies import get_bearer_token, get_current_user_id
from app.db.session import get_db
from app.models.draft import Draft, DraftTrack
from app.schemas.draft import DraftCreate, DraftRead, DraftUpdate, DraftTrackRead, DraftTrackCreate

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.get("", response_model=list[DraftRead])
def list_drafts(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    drafts = db.query(Draft).filter(Draft.spotify_user_id == user_id).order_by(Draft.updated_at.desc()).all()
    return drafts


@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.spotify_user_id == user_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("", response_model=DraftRead)
def create_draft(
    body: DraftCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    draft = Draft(
        title=body.title,
        spotify_user_id=user_id,
        vibe_prompt=body.vibe_prompt,
        target_pace_min_per_km=body.target_pace_min_per_km,
        target_bpm=body.target_bpm,
        vibe_score=body.vibe_score,
        curator_note=body.curator_note,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    track_meta = {t.spotify_track_id: t for t in (body.tracks or [])}
    for i, tid in enumerate(body.track_ids):
        meta = track_meta.get(tid)
        artists_str = None
        if meta and meta.artists:
            artists_str = ", ".join(meta.artists) if isinstance(meta.artists, list) else meta.artists
        dt = DraftTrack(
            draft_id=draft.id,
            spotify_track_id=tid,
            track_order=i,
            name=meta.name if meta else None,
            artists=artists_str,
            preview_url=meta.preview_url if meta else None,
        )
        db.add(dt)
    db.commit()
    db.refresh(draft)
    return draft


@router.patch("/{draft_id}", response_model=DraftRead)
def update_draft(
    draft_id: int,
    body: DraftUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.spotify_user_id == user_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if body.title is not None:
        draft.title = body.title
    if body.track_ids is not None:
        db.query(DraftTrack).filter(DraftTrack.draft_id == draft_id).delete()
        track_meta = {t.spotify_track_id: t for t in (body.tracks or [])}
        for i, tid in enumerate(body.track_ids):
            meta = track_meta.get(tid)
            artists_str = None
            if meta and meta.artists:
                artists_str = ", ".join(meta.artists) if isinstance(meta.artists, list) else str(meta.artists)
            dt = DraftTrack(
                draft_id=draft.id,
                spotify_track_id=tid,
                track_order=i,
                name=meta.name if meta else None,
                artists=artists_str,
                preview_url=meta.preview_url if meta else None,
            )
            db.add(dt)
    db.commit()
    db.refresh(draft)
    return draft


def _create_playlist(token: str, title: str, public: bool = True) -> dict:
    """Create playlist via POST /me/playlists (Feb 2026 Spotify API)."""
    payload = {"name": title or "Pace Runner Playlist", "public": public}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = httpx.post("https://api.spotify.com/v1/me/playlists", json=payload, headers=headers, timeout=20.0)
    if resp.status_code >= 400:
        try:
            body = resp.json()
            message = (body.get("error") or {}).get("message", resp.text)
        except Exception:
            message = resp.text
        raise HTTPException(
            status_code=min(resp.status_code, 502),
            detail=f"Spotify denied access: {message}" if resp.status_code == 403 else f"Spotify error: {message}",
        )
    return resp.json()


def _add_playlist_items(token: str, playlist_id: str, uris: list[str]) -> None:
    """Add tracks via POST /playlists/{id}/items (Feb 2026 Spotify API)."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = httpx.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
        json={"uris": uris},
        headers=headers,
        timeout=20.0,
    )
    if resp.status_code >= 400:
        try:
            body = resp.json()
            message = (body.get("error") or {}).get("message", resp.text)
        except Exception:
            message = resp.text
        raise HTTPException(
            status_code=min(resp.status_code, 502),
            detail=f"Spotify denied access: {message}" if resp.status_code == 403 else f"Spotify error: {message}",
        )


@router.post("/{draft_id}/publish")
def publish_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    token_str: str = Depends(get_bearer_token),
):
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.spotify_user_id == user_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    track_uris = []
    for t in draft.tracks:
        tid = (t.spotify_track_id or "").strip()
        if tid and not any(c in tid for c in " /"):
            track_uris.append(f"spotify:track:{tid}")

    try:
        playlist = _create_playlist(
            token=token_str,
            title=draft.title or "Pace Runner Playlist",
            public=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create playlist: {e}") from e

    playlist_id = playlist.get("id")
    if not playlist_id:
        raise HTTPException(status_code=502, detail="Spotify did not return playlist ID")

    if track_uris:
        try:
            _add_playlist_items(token=token_str, playlist_id=playlist_id, uris=track_uris)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to add tracks: {e}") from e

    playlist_url = (playlist.get("external_urls") or {}).get("spotify", "")
    if not playlist_url:
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

    return {"playlist_id": playlist_id, "playlist_url": playlist_url}


@router.delete("/{draft_id}")
def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.spotify_user_id == user_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    db.delete(draft)
    db.commit()
    return {"ok": True}
