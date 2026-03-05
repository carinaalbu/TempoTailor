from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migration: add deezer_track_id to draft_tracks if missing (SQLite)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE draft_tracks ADD COLUMN deezer_track_id INTEGER"))
            conn.commit()
    except Exception:
        pass  # Column already exists or DB doesn't support this
