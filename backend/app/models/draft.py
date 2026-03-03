from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    spotify_user_id = Column(String(255), nullable=True, index=True)
    vibe_prompt = Column(Text, nullable=True)
    target_pace_min_per_km = Column(Float, nullable=True)
    target_bpm = Column(Integer, nullable=True)
    vibe_score = Column(Integer, nullable=True)
    curator_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tracks = relationship("DraftTrack", back_populates="draft", cascade="all, delete-orphan")


class DraftTrack(Base):
    __tablename__ = "draft_tracks"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    spotify_track_id = Column(String(255), nullable=False)
    track_order = Column(Integer, nullable=False, default=0)
    name = Column(String(512), nullable=True)
    artists = Column(String(512), nullable=True)  # comma-separated
    preview_url = Column(String(1024), nullable=True)

    draft = relationship("Draft", back_populates="tracks")
