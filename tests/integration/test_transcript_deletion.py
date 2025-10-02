"""Integration tests for transcript deletion flow.

Tests the complete flow through use cases and repositories to ensure
transcript deletion properly preserves coaching session data and statistics.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.coaching_assistant.core.models.coaching_session import (
    CoachingSession as DomainCoachingSession,
)
from src.coaching_assistant.core.models.coaching_session import SessionSource
from src.coaching_assistant.core.services.coaching_session_management_use_case import (
    CoachingSessionManagementUseCase,
)
from src.coaching_assistant.infrastructure.db.repositories.client_repository import (
    SQLAlchemyClientRepository,
)
from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
    SQLAlchemyCoachingSessionRepository,
)
from src.coaching_assistant.infrastructure.db.repositories.transcription_session_repository import (
    SQLAlchemyTranscriptionSessionRepository,
)
from src.coaching_assistant.models import Base, Client, User
from src.coaching_assistant.models.coaching_session import (
    CoachingSession as ORMCoachingSession,
)
from src.coaching_assistant.models.session import Session as TranscriptionSession
from src.coaching_assistant.models.session import SessionStatus


@pytest.fixture
def db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        id=uuid4(),
        email="coach@test.com",
        hashed_password="hashed",
        name="Test Coach",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_client(db_session, test_user):
    """Create test client."""
    client = Client(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Client",
        email="client@test.com",
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture
def repositories(db_session):
    """Create repository instances."""
    return {
        "coaching_session": SQLAlchemyCoachingSessionRepository(db_session),
        "client": SQLAlchemyClientRepository(db_session),
        "transcription": SQLAlchemyTranscriptionSessionRepository(db_session),
    }


@pytest.fixture
def use_case(repositories):
    """Create use case with repositories."""
    retrieval_use_case = CoachingSessionManagementUseCase.CoachingSessionRetrievalUseCase(
        repositories["coaching_session"],
        repositories["client"],
        repositories["transcription"],
    )
    return retrieval_use_case


class TestTranscriptDeletionIntegration:
    """Integration tests for transcript deletion functionality."""

    def test_deletion_preserves_session_and_saves_statistics(
        self, db_session, test_user, test_client, repositories
    ):
        """Test that deleting transcript preserves coaching session with statistics."""
        # Arrange - Create coaching session with transcript
        transcription_id = uuid4()
        coaching_session_id = uuid4()

        # Create transcription session
        transcription = TranscriptionSession(
            id=transcription_id,
            user_id=test_user.id,
            title="Test Session",
            audio_filename="test.mp3",
            duration_seconds=3600,
            language="zh-TW",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(transcription)

        # Create coaching session linked to transcript
        coaching_session = ORMCoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source="CLIENT",
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=transcription_id,
            transcript_deleted_at=None,
            saved_speaking_stats=None,
        )
        db_session.add(coaching_session)
        db_session.commit()

        # Act - Simulate deletion with statistics
        speaking_stats = {
            "coach_speaking_time": 2400.0,
            "client_speaking_time": 1200.0,
            "total_speaking_time": 3600.0,
            "coach_percentage": 66.67,
            "client_percentage": 33.33,
            "silence_time": 0.0,
        }

        # Delete transcript and save statistics
        coaching_session.transcription_session_id = None
        coaching_session.transcript_deleted_at = datetime.now(timezone.utc)
        coaching_session.saved_speaking_stats = speaking_stats
        db_session.commit()

        # Delete the actual transcription record
        db_session.delete(transcription)
        db_session.commit()

        # Assert - Verify through repository
        repo = repositories["coaching_session"]
        retrieved = repo.get_by_id(coaching_session_id)

        assert retrieved is not None
        assert retrieved.transcription_session_id is None
        assert retrieved.transcript_deleted_at is not None
        assert retrieved.saved_speaking_stats == speaking_stats
        assert retrieved.saved_speaking_stats["coach_percentage"] == 66.67

        # Verify coaching session details are preserved
        assert retrieved.duration_min == 60
        assert retrieved.fee_amount == 3000
        assert retrieved.client_id == test_client.id

    def test_get_session_with_response_data_includes_deletion_info(
        self, db_session, test_user, test_client, repositories, use_case
    ):
        """Test that get_session_with_response_data returns deletion tracking fields."""
        # Arrange - Create deleted session
        coaching_session_id = uuid4()
        deletion_time = datetime.now(timezone.utc)
        stats = {
            "coach_speaking_time": 1800,
            "client_speaking_time": 1200,
            "coach_percentage": 60,
            "client_percentage": 40,
        }

        coaching_session = ORMCoachingSession(
            id=coaching_session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source="FRIEND",
            duration_min=50,
            fee_currency="USD",
            fee_amount=100,
            transcription_session_id=None,
            transcript_deleted_at=deletion_time,
            saved_speaking_stats=stats,
        )
        db_session.add(coaching_session)
        db_session.commit()

        # Act - Get session with response data
        response_data = use_case.get_session_with_response_data(
            coaching_session_id, test_user.id
        )

        # Assert
        assert response_data is not None
        session = response_data["session"]
        assert session.transcript_deleted_at == deletion_time
        assert session.saved_speaking_stats == stats
        assert session.saved_speaking_stats["coach_percentage"] == 60

    def test_can_distinguish_never_uploaded_from_deleted(
        self, db_session, test_user, test_client, repositories
    ):
        """Test distinguishing between never uploaded and deleted transcripts."""
        # Arrange
        never_uploaded_id = uuid4()
        deleted_id = uuid4()

        # Session never had transcript
        never_uploaded = ORMCoachingSession(
            id=never_uploaded_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source="CLIENT",
            duration_min=30,
            fee_currency="TWD",
            fee_amount=1500,
            transcription_session_id=None,
            transcript_deleted_at=None,
            saved_speaking_stats=None,
        )

        # Session with deleted transcript
        deleted = ORMCoachingSession(
            id=deleted_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source="CLIENT",
            duration_min=45,
            fee_currency="TWD",
            fee_amount=2250,
            transcription_session_id=None,
            transcript_deleted_at=datetime.now(timezone.utc),
            saved_speaking_stats={"coach_percentage": 55},
        )

        db_session.add(never_uploaded)
        db_session.add(deleted)
        db_session.commit()

        # Act
        repo = repositories["coaching_session"]
        retrieved_never = repo.get_by_id(never_uploaded_id)
        retrieved_deleted = repo.get_by_id(deleted_id)

        # Assert - Different states
        # Never uploaded: both fields are None
        assert retrieved_never.transcript_deleted_at is None
        assert retrieved_never.saved_speaking_stats is None

        # Deleted: has deletion timestamp and stats
        assert retrieved_deleted.transcript_deleted_at is not None
        assert retrieved_deleted.saved_speaking_stats is not None
        assert "coach_percentage" in retrieved_deleted.saved_speaking_stats

    def test_deletion_workflow_through_repositories(
        self, db_session, test_user, test_client, repositories
    ):
        """Test complete deletion workflow using repositories."""
        # Arrange - Create and save session with transcript
        session_id = uuid4()
        transcription_id = uuid4()

        # Create transcription
        transcription = TranscriptionSession(
            id=transcription_id,
            user_id=test_user.id,
            title="Recording",
            audio_filename="session.wav",
            duration_seconds=2700,
            language="en-US",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(transcription)

        domain_session = DomainCoachingSession(
            id=session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLASSMATE,
            duration_min=45,
            fee_currency="EUR",
            fee_amount=80,
            transcription_session_id=transcription_id,
        )

        repo = repositories["coaching_session"]
        saved = repo.save(domain_session)
        db_session.commit()

        # Act - Perform deletion
        saved.transcription_session_id = None
        saved.transcript_deleted_at = datetime.now(timezone.utc)
        saved.saved_speaking_stats = {
            "coach_speaking_time": 1620,  # 27 minutes
            "client_speaking_time": 1080,  # 18 minutes
            "total_speaking_time": 2700,
            "coach_percentage": 60,
            "client_percentage": 40,
            "silence_time": 0,
        }
        updated = repo.save(saved)
        db_session.commit()

        # Clean up transcription
        db_session.delete(transcription)
        db_session.commit()

        # Assert - Verify final state
        final = repo.get_by_id(session_id)
        assert final.transcription_session_id is None
        assert final.transcript_deleted_at is not None
        assert final.saved_speaking_stats["total_speaking_time"] == 2700
        assert final.duration_min == 45  # Original duration preserved
        assert final.fee_amount == 80  # Original fee preserved


class TestDeletionEdgeCases:
    """Test edge cases in transcript deletion."""

    def test_multiple_deletions_preserve_latest_stats(
        self, db_session, test_user, test_client, repositories
    ):
        """Test that multiple deletions preserve the latest statistics."""
        # Arrange
        session_id = uuid4()
        repo = repositories["coaching_session"]

        domain_session = DomainCoachingSession(
            id=session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
        )
        repo.save(domain_session)
        db_session.commit()

        # First deletion
        first_stats = {"coach_percentage": 70}
        domain_session.transcript_deleted_at = datetime.now(timezone.utc)
        domain_session.saved_speaking_stats = first_stats
        repo.save(domain_session)
        db_session.commit()

        # Second deletion (re-upload and delete again)
        second_stats = {"coach_percentage": 65, "version": 2}
        domain_session.transcript_deleted_at = datetime.now(timezone.utc)
        domain_session.saved_speaking_stats = second_stats
        repo.save(domain_session)
        db_session.commit()

        # Assert - Latest stats are preserved
        final = repo.get_by_id(session_id)
        assert final.saved_speaking_stats == second_stats
        assert final.saved_speaking_stats.get("version") == 2