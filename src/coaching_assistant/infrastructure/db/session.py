"""Database session factory for the infrastructure layer.

This module provides database session management following the
Clean Architecture pattern, isolating SQLAlchemy concerns from
the core domain.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ...core.config import Settings

# Global variables for engine and session factory
_engine = None
_SessionLocal = None


def _ensure_engine_and_session_factory(settings: Settings) -> None:
    """Ensure database engine and session factory are initialized."""
    global _engine, _SessionLocal

    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,  # Keep objects available after commit
        )


def get_database_session(settings: Settings) -> Session:
    """Get a database session instance.

    Returns a new SQLAlchemy session that should be closed after use.
    For use in repository implementations.

    Args:
        settings: Application settings containing database URL

    Returns:
        SQLAlchemy session instance
    """
    _ensure_engine_and_session_factory(settings)
    return _SessionLocal()


def get_session_dependency(
    settings: Settings,
) -> Generator[Session, None, None]:
    """Database session dependency for FastAPI dependency injection.

    Creates a session, yields it, and ensures it's closed after use.
    This is the recommended way to get sessions in API endpoints.

    Args:
        settings: Application settings containing database URL

    Yields:
        SQLAlchemy session instance
    """
    _ensure_engine_and_session_factory(settings)
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_all_tables(settings: Settings) -> None:
    """Create all database tables.

    This is mainly for testing and development.
    Production should use Alembic migrations.

    Args:
        settings: Application settings containing database URL
    """
    from ...models import Base  # Import all models to register them

    _ensure_engine_and_session_factory(settings)
    Base.metadata.create_all(bind=_engine)


def drop_all_tables(settings: Settings) -> None:
    """Drop all database tables.

    WARNING: This will delete all data! Only use for testing.

    Args:
        settings: Application settings containing database URL
    """
    from ...models import Base  # Import all models to register them

    _ensure_engine_and_session_factory(settings)
    Base.metadata.drop_all(bind=_engine)


def get_engine(settings: Settings):
    """Get the SQLAlchemy engine instance.

    Args:
        settings: Application settings containing database URL

    Returns:
        SQLAlchemy engine instance
    """
    _ensure_engine_and_session_factory(settings)
    return _engine
