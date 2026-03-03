"""Pytest configuration. Use temp file SQLite for isolated tests."""

import os

# Use file-based DB so all connections share the same schema (in-memory uses per-connection DB)
os.environ["DATABASE_URL"] = "sqlite:///./test_tempo_tailor.db"
