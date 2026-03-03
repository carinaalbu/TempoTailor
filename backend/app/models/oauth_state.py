from datetime import datetime
from sqlalchemy import Column, DateTime, String

from app.db.session import Base


class OAuthState(Base):
    """Persistent OAuth state for CSRF protection across redirects."""

    __tablename__ = "oauth_states"

    state = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
