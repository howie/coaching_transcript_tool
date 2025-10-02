"""Unit tests for CoachingSessionRepository mapping functions.

Tests focus on verifying that all fields are correctly mapped between
ORM models and domain models, especially the newly added transcript
deletion tracking fields.
"""

import json
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.coaching_assistant.core.models.coaching_session import (
    CoachingSession as DomainCoachingSession,
)
from src.coaching_assistant.core.models.coaching_session import SessionSource
from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
    SQLAlchemyCoachingSessionRepository,
)
from src.coaching_assistant.models import Base
from src.coaching_assistant.models.coaching_session import (
    CoachingSession as ORMCoachingSession,
)
from src.coaching_assistant.models.coaching_session import (
    SessionSource as ORMSessionSource,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def repository(db_session):
    """Create repository instance with test database session."""
    return SQLAlchemyCoachingSessionRepository(db_session)


class TestRepositoryMapping:
    """Test repository mapping between ORM and domain models."""

    def test_to_domain_maps_all_fields_including_deletion_tracking(
        self, repository, db_session
    ):
        """Test that _to_domain correctly maps ALL fields including transcript_deleted_at and saved_speaking_stats."""
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        client_id = uuid4()
        transcription_session_id = uuid4()
        deleted_at = datetime.now(timezone.utc)
        speaking_stats = {
            "coach_speaking_time": 1200.5,
            "client_speaking_time": 600.3,
            "total_speaking_time": 1800.8,
            "coach_percentage": 66.7,
            "client_percentage": 33.3,
            "silence_time": 100.2,
        }

        orm_session = ORMCoachingSession(
            id=session_id,
            user_id=user_id,
            client_id=client_id,
            session_date=date(2025, 10, 2),
            source=ORMSessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=transcription_session_id,
            transcript_deleted_at=deleted_at,
            saved_speaking_stats=speaking_stats,
            notes="Test session notes",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        domain_session = repository._to_domain(orm_session)

        # Assert - Verify ALL fields are mapped
        assert domain_session.id == session_id
        assert domain_session.user_id == user_id
        assert domain_session.client_id == client_id
        assert domain_session.session_date == date(2025, 10, 2)
        assert domain_session.source == SessionSource.CLIENT
        assert domain_session.duration_min == 60
        assert domain_session.fee_currency == "TWD"
        assert domain_session.fee_amount == 3000
        assert domain_session.transcription_session_id == transcription_session_id

        # Critical: Test the new fields that were missing
        assert domain_session.transcript_deleted_at == deleted_at
        assert domain_session.saved_speaking_stats == speaking_stats

        assert domain_session.notes == "Test session notes"
        assert domain_session.created_at is not None
        assert domain_session.updated_at is not None

    def test_to_domain_handles_null_deletion_fields(self, repository):
        """Test that _to_domain correctly handles null transcript_deleted_at and saved_speaking_stats."""
        # Arrange
        orm_session = ORMCoachingSession(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=ORMSessionSource.CLIENT,
            duration_min=30,
            fee_currency="USD",
            fee_amount=100,
            transcription_session_id=None,
            transcript_deleted_at=None,  # Null deletion timestamp
            saved_speaking_stats=None,  # Null statistics
            notes=None,
        )

        # Act
        domain_session = repository._to_domain(orm_session)

        # Assert
        assert domain_session.transcript_deleted_at is None
        assert domain_session.saved_speaking_stats is None

    def test_create_orm_session_maps_all_fields(self, repository):
        """Test that _create_orm_session correctly maps all fields from domain to ORM."""
        # Arrange
        session_id = uuid4()
        deleted_at = datetime.now(timezone.utc)
        speaking_stats = {"coach_percentage": 70, "client_percentage": 30}

        domain_session = DomainCoachingSession(
            id=session_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date(2025, 10, 2),
            source=SessionSource.FRIEND,
            duration_min=45,
            fee_currency="EUR",
            fee_amount=150,
            transcription_session_id=uuid4(),
            transcript_deleted_at=deleted_at,
            saved_speaking_stats=speaking_stats,
            notes="Domain notes",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Act
        orm_session = repository._create_orm_session(domain_session)

        # Assert
        assert orm_session.id == session_id
        assert orm_session.transcript_deleted_at == deleted_at
        assert orm_session.saved_speaking_stats == speaking_stats
        assert orm_session.source == ORMSessionSource.FRIEND

    def test_save_updates_deletion_fields(self, repository, db_session):
        """Test that save method correctly updates transcript deletion fields."""
        # Arrange - Create and save initial session
        session_id = uuid4()
        domain_session = DomainCoachingSession(
            id=session_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000,
            transcript_deleted_at=None,
            saved_speaking_stats=None,
        )

        # Save initial session
        saved = repository.save(domain_session)
        db_session.commit()

        # Update with deletion info
        deletion_time = datetime.now(timezone.utc)
        stats = {"coach_speaking_time": 1800}
        domain_session.transcript_deleted_at = deletion_time
        domain_session.saved_speaking_stats = stats

        # Act - Update session with deletion fields
        updated = repository.save(domain_session)
        db_session.commit()

        # Assert
        retrieved = repository.get_by_id(session_id)
        assert retrieved.transcript_deleted_at == deletion_time
        assert retrieved.saved_speaking_stats == stats

    def test_get_by_id_returns_all_fields(self, repository, db_session):
        """Integration test: Verify get_by_id returns complete domain object with all fields."""
        # Arrange
        session_id = uuid4()
        deleted_at = datetime.now(timezone.utc)
        stats = {"total_speaking_time": 2400}

        orm_session = ORMCoachingSession(
            id=session_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=ORMSessionSource.CLASSMATE,
            duration_min=90,
            fee_currency="JPY",
            fee_amount=10000,
            transcript_deleted_at=deleted_at,
            saved_speaking_stats=stats,
        )
        db_session.add(orm_session)
        db_session.commit()

        # Act
        result = repository.get_by_id(session_id)

        # Assert - All fields including deletion tracking
        assert result is not None
        assert result.id == session_id
        assert result.transcript_deleted_at == deleted_at
        assert result.saved_speaking_stats == stats
        assert result.source == SessionSource.CLASSMATE


class TestDeletionScenarios:
    """Test specific scenarios related to transcript deletion."""

    def test_deletion_preserves_session_with_tracking_info(
        self, repository, db_session
    ):
        """Test that deleting transcript preserves the coaching session with tracking info."""
        # Arrange - Create session with transcript
        session_id = uuid4()
        transcription_id = uuid4()

        session = DomainCoachingSession(
            id=session_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=3000,
            transcription_session_id=transcription_id,
            transcript_deleted_at=None,
            saved_speaking_stats=None,
        )
        repository.save(session)
        db_session.commit()

        # Act - Simulate transcript deletion
        session.transcription_session_id = None  # Clear transcript link
        session.transcript_deleted_at = datetime.now(timezone.utc)
        session.saved_speaking_stats = {
            "coach_speaking_time": 2100,
            "client_speaking_time": 900,
            "coach_percentage": 70,
            "client_percentage": 30,
        }
        updated = repository.save(session)
        db_session.commit()

        # Assert
        retrieved = repository.get_by_id(session_id)
        assert retrieved is not None
        assert retrieved.transcription_session_id is None
        assert retrieved.transcript_deleted_at is not None
        assert retrieved.saved_speaking_stats is not None
        assert retrieved.saved_speaking_stats["coach_percentage"] == 70
        # Session details preserved
        assert retrieved.duration_min == 60
        assert retrieved.fee_amount == 3000

    def test_can_distinguish_never_uploaded_vs_deleted(self, repository, db_session):
        """Test that we can distinguish between 'never uploaded' and 'deleted' states."""
        # Arrange
        never_uploaded_id = uuid4()
        deleted_id = uuid4()

        # Session that never had a transcript
        never_uploaded = DomainCoachingSession(
            id=never_uploaded_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=30,
            fee_currency="TWD",
            fee_amount=1500,
            transcription_session_id=None,
            transcript_deleted_at=None,
            saved_speaking_stats=None,
        )

        # Session that had transcript deleted
        deleted = DomainCoachingSession(
            id=deleted_id,
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=SessionSource.CLIENT,
            duration_min=45,
            fee_currency="TWD",
            fee_amount=2250,
            transcription_session_id=None,
            transcript_deleted_at=datetime.now(timezone.utc),
            saved_speaking_stats={"coach_percentage": 65},
        )

        repository.save(never_uploaded)
        repository.save(deleted)
        db_session.commit()

        # Act
        retrieved_never = repository.get_by_id(never_uploaded_id)
        retrieved_deleted = repository.get_by_id(deleted_id)

        # Assert - Can distinguish the two states
        assert retrieved_never.transcript_deleted_at is None
        assert retrieved_never.saved_speaking_stats is None

        assert retrieved_deleted.transcript_deleted_at is not None
        assert retrieved_deleted.saved_speaking_stats is not None