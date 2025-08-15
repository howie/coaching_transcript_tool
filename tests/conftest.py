#!/usr/bin/env python3
import os
import sys
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from coaching_assistant.models import (
    Base,
    User,
    Session,
    TranscriptSegment,
    SessionRole,
)
from coaching_assistant.models.user import UserPlan
from coaching_assistant.models.session import SessionStatus
from coaching_assistant.models.transcript import SpeakerRole


# Database fixtures
@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        name="Test User",
        google_id="123456789",
        plan=UserPlan.FREE,
        usage_minutes=0,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_session(db_session, sample_user):
    """Create a sample session for testing."""
    session = Session(
        title="Test Coaching Session",
        user_id=sample_user.id,
        audio_filename="test_audio.mp3",
        language="zh-TW",
        status=SessionStatus.PENDING,
    )
    db_session.add(session)
    db_session.commit()
    return session


# Original fixtures
@pytest.fixture
def data_dir():
    """Return the path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def sample_vtt_path(data_dir):
    """Return the path to the sample VTT file."""
    return os.path.join(data_dir, "sample_1.vtt")
