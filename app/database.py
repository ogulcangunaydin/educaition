"""
DEPRECATED: Import from app.core.database instead.

This module re-exports from app.core.database for backward compatibility.
"""

from app.core.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
