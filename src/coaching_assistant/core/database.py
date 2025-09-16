"""
Database connection and session management.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings


def create_database_engine(database_url: str, **kwargs):
    """
    Create a database engine with appropriate SSL configuration.

    This helper ensures consistent SSL configuration across all database connections.
    """
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_timeout": 20,  # Timeout for getting connection from pool
        "pool_size": 10,       # Number of connections to maintain
        "max_overflow": 20,    # Additional connections allowed
        "echo": settings.DEBUG,  # Log SQL queries in debug mode
        "connect_args": {},
        **kwargs,
    }

    # For production environments using SSL (like Render), add SSL configuration
    if database_url and (
        "render.com" in database_url or "dpg-" in database_url
    ):
        connect_args = engine_kwargs.get("connect_args", {})

        # Render PostgreSQL SSL configuration
        connect_args.update(
            {
                "connect_timeout": 30,
                "application_name": "coaching-assistant-api",
            }
        )

        # Render database SSL configuration - require SSL but disable certificate verification
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
