from datetime import datetime
from pydantic import BaseModel


class DraftTrackRead(BaseModel):
    id: int
    spotify_track_id: str
    track_order: int
    name: str | None = None
    artists: str | None = None
    preview_url: str | None = None

    class Config:
        from_attributes = True


class DraftTrackCreate(BaseModel):
    spotify_track_id: str
    name: str | None = None
    artists: list[str] | str | None = None  # list or comma-separated
    preview_url: str | None = None


class DraftCreate(BaseModel):
    title: str
    vibe_prompt: str | None = None
    target_pace_min_per_km: float | None = None
    target_bpm: int | None = None
    vibe_score: int | None = None
    curator_note: str | None = None
    track_ids: list[str]
    tracks: list[DraftTrackCreate] | None = None  # optional metadata


class DraftUpdate(BaseModel):
    title: str | None = None
    track_ids: list[str] | None = None
    tracks: list[DraftTrackCreate] | None = None  # optional metadata when updating


class DraftRead(BaseModel):
    id: int
    title: str
    vibe_prompt: str | None = None
    target_pace_min_per_km: float | None = None
    target_bpm: int | None = None
    vibe_score: int | None = None
    curator_note: str | None = None
    created_at: datetime
    updated_at: datetime
    tracks: list[DraftTrackRead]

    class Config:
        from_attributes = True
