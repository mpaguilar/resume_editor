import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from resume_editor.app.core.config import get_settings

log = logging.getLogger(__name__)

# Global variables for engine and sessionmaker
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine.

    Args:
        None

    Returns:
        Engine: The SQLAlchemy engine instance used to connect to the database.

    Notes:
        1. Create the engine only when first accessed to avoid premature connection.
        2. Reuse the same engine instance on subsequent calls to ensure consistency.
        3. Network access occurs when creating the engine, using the database URL from settings.

    """
    global _engine
    if _engine is None:
        _msg = "Creating database engine"
        log.debug(_msg)
        settings = get_settings()
        DATABASE_URL = str(settings.database_url)
        _engine = create_engine(DATABASE_URL, echo=True)
    return _engine


def get_session_local():
    """Get or create the session local factory.

    Args:
        None

    Returns:
        sessionmaker: The SQLAlchemy sessionmaker instance used to create database sessions.

    Notes:
        1. Create the sessionmaker only when first accessed to avoid premature configuration.
        2. Reuse the same sessionmaker instance on subsequent calls to ensure consistent session behavior.
        3. No network access in this function itself; it uses the previously created engine.

    """
    global _SessionLocal
    if _SessionLocal is None:
        _msg = "Creating session local factory"
        log.debug(_msg)
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency to provide database sessions to route handlers.

    Args:
        None

    Returns:
        Generator[Session, None, None]: A generator that yields a database session for use in route handlers.

    Notes:
        1. Create a new database session using the sessionmaker factory.
        2. Yield the session to be used in route handlers.
        3. Ensure the session is closed after use to release resources.
        4. No network access in this function itself; the session is created from the existing engine.

    """
    _msg = "Creating database session"
    log.debug(_msg)

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        _msg = "Closing database session"
        log.debug(_msg)
        db.close()
