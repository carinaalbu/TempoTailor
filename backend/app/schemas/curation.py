from pydantic import BaseModel


class CurationRequest(BaseModel):
    pace_min_per_km: float
    vibe_prompt: str = ""
    target_energy: float | None = None
    target_valence: float | None = None
    target_danceability: float | None = None
    seed_genres: list[str] | None = None


class CurationTrack(BaseModel):
    id: str
    name: str
    artists: list[str]
    preview_url: str | None
    deezer_track_id: int | None = None
    release_year: int | None = None


class CurationResponse(BaseModel):
    track_ids: list[str]
    tracks: list[CurationTrack]
    vibe_score: int
    curator_note: str
    target_bpm: int
    generated_title: str
