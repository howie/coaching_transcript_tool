#!/usr/bin/env python3
import os
import sys
import pytest
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

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
from coaching_assistant.main import app


# Database fixtures
@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite database for testing."""
    # Setup SQLite compatibility for PostgreSQL types
    from tests.unit.utils.test_helpers import setup_sqlite_compatibility
    setup_sqlite_compatibility()
    
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


# API testing fixtures
@pytest.fixture
def client(db_session):
    """Create a FastAPI test client."""
    from coaching_assistant.core.database import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client, test_user, db_session):
    """Create an authenticated test client."""
    from coaching_assistant.api.auth import get_current_user_dependency
    
    def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user_dependency] = override_get_current_user
    
    yield client
    
    del app.dependency_overrides[get_current_user_dependency]


@pytest.fixture
def test_user(db_session):
    """Create a test user for API testing."""
    import uuid
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        google_id="google-test-123",
        plan=UserPlan.FREE,
        usage_minutes=0,
        session_count=0,
        transcription_count=0,
        current_month_start=datetime.now().replace(day=1),
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for testing."""
    # In a real app, this would generate a proper JWT token
    # For testing, we'll mock the authentication
    return {"Authorization": f"Bearer test-token-{test_user.id}"}


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    import uuid
    admin = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        name="Admin User",
        google_id="google-admin-123",
        is_admin=True,
        plan=UserPlan.ENTERPRISE,
        usage_minutes=0,
        session_count=0,
        transcription_count=0,
        current_month_start=datetime.now().replace(day=1),
        created_at=datetime.now()
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def admin_headers(admin_user):
    """Create authentication headers for admin user."""
    return {"Authorization": f"Bearer admin-token-{admin_user.id}"}
