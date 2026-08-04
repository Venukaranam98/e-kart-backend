"""Database module compatibility shim re-exporting session components."""

from db.session import DATABASE_URL, Base, SessionLocal, engine, get_db

__all__ = ["DATABASE_URL", "Base", "SessionLocal", "engine", "get_db"]
