"""
Database connection and session management.
"""

import logging
from contextlib import contextmanager

# Aggressively suppress SQLAlchemy query logs at module import time
# This must be done BEFORE importing SQLAlchemy
for logger_name in [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)  # Only show errors
    logger.propagate = False  # Don't propagate to root logger
    logger.handlers = []  # Remove all handlers

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from .config import settings  # noqa: E402


def create_database_engine(database_url: str, **kwargs):
    """
    Create a database engine with appropriate SSL configuration.

    This helper ensures consistent SSL configuration across all database connections.
    """
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_timeout": 20,  # Timeout for getting connection from pool
        "pool_size": 10,  # Number of connections to maintain
        "max_overflow": 20,  # Additional connections allowed
        "echo": settings.SQL_ECHO,  # Log SQL queries when enabled
        "echo_pool": False,  # Disable connection pool logging
        "connect_args": {},
        **kwargs,
    }

    # For production environments using SSL (like Render), add SSL
    # configuration
    if database_url and ("render.com" in database_url or "dpg-" in database_url):
        connect_args = engine_kwargs.get("connect_args", {})

        # Render PostgreSQL SSL configuration
        connect_args.update(
            {
                "connect_timeout": 30,
                "application_name": "coaching-assistant-api",
            }
        )

        # Render database SSL configuration - require SSL but disable
        # certificate verification
        connect_args.update(
            {
                "sslmode": "require",
                "sslcert": "",  # No client certificate
                "sslkey": "",  # No client key
                "sslrootcert": "",  # Don't verify server certificate
            }
        )

        engine_kwargs["connect_args"] = connect_args

    return create_engine(database_url, **engine_kwargs)


# Create the SQLAlchemy engine using the helper function
engine = create_database_engine(settings.DATABASE_URL)

# Aggressively suppress SQLAlchemy logs AFTER engine creation
# SQLAlchemy adds its own handlers during engine creation, so we need to remove them
for logger_name in [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)  # Only show errors
    logger.propagate = False  # Don't propagate to root logger
    logger.handlers.clear()  # Remove all handlers that SQLAlchemy added

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency to get a database session.
    Ensures the session is closed after the request and rollback on errors.
    """
    db = SessionLocal()
    try:
        yield db
        # Commit any successful transactions
        db.commit()
    except Exception:
        # Rollback any failed transaction to clear the aborted state
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions in Celery tasks.
    Ensures proper session cleanup.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
