"""Database connection utilities.

Centralised helpers for building the SQLAlchemy engine and sessions, loading
credentials from environment variables (or a `.env` file loaded by the
application runner).
"""
from __future__ import annotations

import os
from typing import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# Load .env located at project/app root, if present
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

# ---------------------------------------------------------------------------
# Environment-configurable settings
# ---------------------------------------------------------------------------

_POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
_POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
_POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
_POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
_POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_news_aggregator")


def get_database_url() -> str:  # noqa: D401
    """Return SQLAlchemy URL for Postgres credentials pulled from env vars."""
    return (
        "postgresql+psycopg2://"
        f"{_POSTGRES_USER}:{_POSTGRES_PASSWORD}@{_POSTGRES_HOST}:{_POSTGRES_PORT}/{_POSTGRES_DB}"
    )


# ---------------------------------------------------------------------------
# SQLAlchemy engine / sessionmaker / Base
# ---------------------------------------------------------------------------

engine = create_engine(get_database_url(), echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


@contextmanager
def get_session():  # noqa: D401
    """Context-managed SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
