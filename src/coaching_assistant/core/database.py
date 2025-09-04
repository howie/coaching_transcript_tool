"""
Database connection and session management.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings


def create_database_engine(database_url: str, **kwargs):
    """
    Create a database engine with appropriate SSL configuration.
    
    This helper ensures consistent SSL configuration across all database connections.
    """
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_timeout": 20,    # Timeout for getting connection from pool
        "connect_args": {},
        **kwargs
    }
    
    # For production environments using SSL (like Render), add SSL configuration
    if database_url and ("render.com" in database_url or "dpg-" in database_url):
        connect_args = engine_kwargs.get("connect_args", {})
        
        # Different SSL configuration for internal vs external Render connections
        if ".singapore-postgres.render.com" in database_url:
            # External connection - requires SSL
            connect_args.update({
                "sslmode": "require",
                "connect_timeout": 30,
                "application_name": "coaching-assistant-api",
            })
        else:
            # Internal connection (dpg-xxx format) - SSL may not be required/available
            connect_args.update({
                "sslmode": "disable",  # Internal connections may not support SSL
                "connect_timeout": 30,
                "application_name": "coaching-assistant-api",
            })
        
        engine_kwargs["connect_args"] = connect_args
    
    return create_engine(database_url, **engine_kwargs)

# Create the SQLAlchemy engine using the helper function
engine = create_database_engine(settings.DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
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
