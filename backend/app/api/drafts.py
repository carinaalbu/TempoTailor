from fastapi import APIRouter, Depends, HTTPException
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

    from app.services.spotify_auth import get_spotify_client
    sp = get_spotify_client({"access_token": token_str})

    playlist = sp.user_playlist_create(
        user=user_id,
        name=draft.title,
        public=True,
    )
    playlist_id = playlist["id"]
    track_uris = [f"spotify:track:{t.spotify_track_id}" for t in draft.tracks]
    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)

    return {"playlist_id": playlist_id, "playlist_url": playlist.get("external_urls", {}).get("spotify", "")}


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
