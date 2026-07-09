"""
Database session/engine setup for the Platform Data Store.
"""
from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from db.models import Base

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Requires PostGIS extension already enabled on the DB:
    `CREATE EXTENSION IF NOT EXISTS postgis;`
    """
    logger.info("Creating database tables (if not present)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready.")


def get_session():
    """Context-manager-friendly session generator."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
