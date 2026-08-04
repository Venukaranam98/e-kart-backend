"""Database session management and engine initialization."""

import logging
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("[Database] Connection URL loaded successfully.")
else:
    logger.warning("[Database ERROR] DATABASE_URL environment variable is not set!")

try:
    engine = (
        create_engine(DATABASE_URL)
        if DATABASE_URL
        else create_engine("sqlite:///:memory:")
    )
except Exception as e:
    logger.error(f"[Database ERROR] Failed to create SQLAlchemy engine: {e}")
    engine = create_engine("sqlite:///:memory:")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session context for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
