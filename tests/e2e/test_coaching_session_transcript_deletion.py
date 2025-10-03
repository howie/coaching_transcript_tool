"""End-to-end API tests for coaching session transcript deletion.

Tests the complete API flow for deleting transcripts while preserving
coaching session data and speaking statistics.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.coaching_assistant.models.transcript_segment import TranscriptSegment

from src.coaching_assistant.api.v1.auth import create_access_token
from src.coaching_assistant.config import get_settings
from src.coaching_assistant.models import Base, Client, User
from src.coaching_assistant.models.coaching_session import (
    CoachingSession,
    SessionSource,
)
from src.coaching_assistant.models.session import Session as TranscriptionSession
from src.coaching_assistant.models.session import SessionStatus


# Test database setup
@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db):
    """Create test user."""
    user = User(
        id=uuid4(),
        email="coach@example.com",
        hashed_password="$2b$12$test",
        name="Test Coach",
        plan="premium",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_client(test_db, test_user):
    """Create test client."""
    client = Client(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Client",
        email="client@example.com",
    )
    test_db.add(client)
    test_db.commit()
    test_db.refresh(client)
    return client


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers."""
    settings = get_settings()
    token = create_access_token(
        data={"sub": test_user.email, "user_id": str(test_user.id)},
        secret_key=settings.SECRET_KEY,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_app(test_db):
    """Create test FastAPI app."""
    from src.coaching_assistant.api.main import app
    from src.coaching_assistant.database import get_db

    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestTranscriptDeletionAPI:
    """E2E tests for transcript deletion API endpoints."""

    def test_delete_transcript_saves_statistics_and_timestamp(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test DELETE /api/v1/coaching-sessions/{id}/transcript endpoint."""
        # Arrange - Create coaching session with transcript
        transcription_id = uuid4()
        coaching_session_id = uuid4()

        # Create transcription session
        transcription = TranscriptionSession(
            id=transcription_id,
            user_id=test_user.id,
            title="Test Recording",
            audio_filename="test.mp3",
            duration_seconds=3600,
            language="zh-TW",
            status=SessionStatus.COMPLETED,
        )
        test_db.add(transcription)

        # Create coaching session
        coaching_session = CoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=transcription_id,
        )
        test_db.add(coaching_session)

        # Add some transcript segments
        for i in range(5):
            segment = TranscriptSegment(
                id=uuid4(),
                session_id=transcription_id,
                speaker_id=i % 2,
                start_seconds=i * 10.0,
                end_seconds=(i + 1) * 10.0,
                content=f"Segment {i} content",
            )
            test_db.add(segment)

        test_db.commit()

        # Prepare speaking statistics
        speaking_stats = {
            "coach_speaking_time": 2100.5,
            "client_speaking_time": 1499.5,
            "total_speaking_time": 3600.0,
            "coach_percentage": 58.35,
            "client_percentage": 41.65,
            "silence_time": 0.0,
        }

        # Act - Delete transcript with statistics
        response = client.delete(
            f"/api/v1/coaching-sessions/{coaching_session_id}/transcript",
            headers=auth_headers,
            json={"speaking_stats": speaking_stats},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transcript deleted successfully"

        # Verify coaching session is preserved with deletion info
        get_response = client.get(
            f"/api/v1/coaching-sessions/{coaching_session_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        session_data = get_response.json()

        # Check deletion tracking fields
        assert session_data["transcript_deleted_at"] is not None
        assert session_data["saved_speaking_stats"] is not None
        assert session_data["saved_speaking_stats"]["coach_percentage"] == 58.35
        assert session_data["transcription_session_id"] is None

        # Check original session data is preserved
        assert session_data["duration_min"] == 60
        assert session_data["fee_amount"] == 3000
        assert session_data["client_id"] == str(test_client.id)

    def test_delete_transcript_without_statistics(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test deleting transcript without providing statistics."""
        # Arrange
        transcription_id = uuid4()
        coaching_session_id = uuid4()

        transcription = TranscriptionSession(
            id=transcription_id,
            user_id=test_user.id,
            title="Recording",
            audio_filename="audio.wav",
            duration_seconds=1800,
            language="en-US",
            status=SessionStatus.COMPLETED,
        )
        test_db.add(transcription)

        coaching_session = CoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.FRIEND,
            duration_min=30,
            fee_currency="USD",
            fee_amount=50,
            transcription_session_id=transcription_id,
        )
        test_db.add(coaching_session)
        test_db.commit()

        # Act - Delete without statistics
        response = client.delete(
            f"/api/v1/coaching-sessions/{coaching_session_id}/transcript",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200

        # Verify deletion timestamp is set but no statistics
        get_response = client.get(
            f"/api/v1/coaching-sessions/{coaching_session_id}",
            headers=auth_headers,
        )
        session_data = get_response.json()
        assert session_data["transcript_deleted_at"] is not None
        assert session_data["saved_speaking_stats"] is None

    def test_delete_nonexistent_transcript_returns_404(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test deleting transcript from session without transcript."""
        # Arrange - Session without transcript
        coaching_session_id = uuid4()
        coaching_session = CoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=45,
            fee_currency="TWD",
            fee_amount=2250,
            transcription_session_id=None,  # No transcript
        )
        test_db.add(coaching_session)
        test_db.commit()

        # Act
        response = client.delete(
            f"/api/v1/coaching-sessions/{coaching_session_id}/transcript",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404
        assert "No transcript found" in response.json()["detail"]

    def test_get_session_shows_deletion_state(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test that GET endpoint correctly returns deletion state."""
        # Arrange - Create session with deleted transcript
        coaching_session_id = uuid4()
        deletion_time = datetime.now(timezone.utc)
        saved_stats = {
            "coach_speaking_time": 1500,
            "client_speaking_time": 900,
            "coach_percentage": 62.5,
            "client_percentage": 37.5,
        }

        coaching_session = CoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLASSMATE,
            duration_min=40,
            fee_currency="EUR",
            fee_amount=60,
            transcription_session_id=None,
            transcript_deleted_at=deletion_time,
            saved_speaking_stats=saved_stats,
        )
        test_db.add(coaching_session)
        test_db.commit()

        # Act
        response = client.get(
            f"/api/v1/coaching-sessions/{coaching_session_id}",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["transcript_deleted_at"] is not None
        assert data["saved_speaking_stats"]["coach_percentage"] == 62.5
        assert data["transcription_session_id"] is None

    def test_list_sessions_includes_deletion_fields(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test that list endpoint includes deletion tracking fields."""
        # Arrange - Mix of sessions
        sessions = []

        # Session with transcript
        with_transcript = CoachingSession(
            id=uuid4(),
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=uuid4(),
        )
        sessions.append(with_transcript)

        # Session with deleted transcript
        deleted_transcript = CoachingSession(
            id=uuid4(),
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=45,
            fee_currency="TWD",
            fee_amount=2250,
            transcription_session_id=None,
            transcript_deleted_at=datetime.now(timezone.utc),
            saved_speaking_stats={"coach_percentage": 70},
        )
        sessions.append(deleted_transcript)

        # Session never had transcript
        no_transcript = CoachingSession(
            id=uuid4(),
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=30,
            fee_currency="TWD",
            fee_amount=1500,
            transcription_session_id=None,
        )
        sessions.append(no_transcript)

        for session in sessions:
            test_db.add(session)
        test_db.commit()

        # Act
        response = client.get(
            "/api/v1/coaching-sessions",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

        # Find each session type
        items_by_duration = {item["duration_min"]: item for item in data["items"]}

        # Session with transcript
        assert items_by_duration[60]["transcription_session_id"] is not None
        assert items_by_duration[60]["transcript_deleted_at"] is None
        assert items_by_duration[60]["saved_speaking_stats"] is None

        # Session with deleted transcript
        assert items_by_duration[45]["transcription_session_id"] is None
        assert items_by_duration[45]["transcript_deleted_at"] is not None
        assert items_by_duration[45]["saved_speaking_stats"] is not None

        # Session never had transcript
        assert items_by_duration[30]["transcription_session_id"] is None
        assert items_by_duration[30]["transcript_deleted_at"] is None
        assert items_by_duration[30]["saved_speaking_stats"] is None


class TestDeletionAuthorization:
    """Test authorization for transcript deletion."""

    def test_cannot_delete_other_users_transcript(
        self, client, test_db, test_user, test_client, auth_headers
    ):
        """Test that users cannot delete transcripts from other users' sessions."""
        # Arrange - Create another user's session
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            hashed_password="$2b$12$other",
            name="Other Coach",
        )
        test_db.add(other_user)

        other_session_id = uuid4()
        other_session = CoachingSession(
            id=other_session_id,
            user_id=other_user.id,  # Different user
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=uuid4(),
        )
        test_db.add(other_session)
        test_db.commit()

        # Act - Try to delete with test_user's auth
        response = client.delete(
            f"/api/v1/coaching-sessions/{other_session_id}/transcript",
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 404
        assert "not found or you don't have permission" in response.json()["detail"]

    def test_requires_authentication(self, client, test_db):
        """Test that deletion requires authentication."""
        # Act - No auth headers
        response = client.delete(f"/api/v1/coaching-sessions/{uuid4()}/transcript")

        # Assert
        assert response.status_code == 401
