"""Pydantic schemas for LLM structured outputs."""

from pydantic import BaseModel, Field


class VibeTranslation(BaseModel):
    """Spotify recommendation parameters from LLM vibe translator."""

    target_energy: float = Field(ge=0, le=1, description="0-1 energy level")
    target_valence: float = Field(ge=0, le=1, description="0-1 mood positivity")
    target_danceability: float = Field(ge=0, le=1, description="0-1 danceability")
    seed_genres: list[str] = Field(max_length=5, description="Spotify genre seeds")
    seed_artists: list[str] = Field(default_factory=list, max_length=5)
    seed_tracks: list[str] = Field(default_factory=list, max_length=5)
    release_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="Extract only if user mentions a year/era (e.g. 2010s, 2005, 90s). Songs filtered to year-5..year+5.",
    )


class JudgeResult(BaseModel):
    """LLM Judge output: filtered track IDs and metadata."""

    track_ids: list[str] = Field(min_length=1)  # truncated to 25 in llm_service before validation
    vibe_score: int = Field(ge=1, le=100)
    curator_note: str
    playlist_name: str = Field(
        default="Run Vibes",
        description="Cute, funky, suggestive playlist name (2–6 words) matching the vibe",
    )
