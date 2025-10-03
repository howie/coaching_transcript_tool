"""Integration tests verifying that transcript deletion doesn't affect usage and revenue calculations.

This test suite ensures that deleting transcripts preserves all coaching session
financial and usage data, maintaining accurate plan usage tracking and revenue reports.
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
from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
    SQLAlchemyCoachingSessionRepository,
)
from src.coaching_assistant.models import Base, Client, User
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
        plan="PRO",
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
def repository(db_session):
    """Create coaching session repository."""
    return SQLAlchemyCoachingSessionRepository(db_session)


class TestUsageAfterTranscriptDeletion:
    """Test that usage and revenue calculations remain accurate after transcript deletion."""

    def test_total_minutes_unchanged_after_deletion(
        self, db_session, test_user, test_client, repository
    ):
        """Test that get_total_minutes_for_user returns same value after transcript deletion."""
        # Arrange - Create coaching sessions with various states
        sessions = []

        # Session with transcript
        with_transcript = DomainCoachingSession(
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

        # Session that will have transcript deleted
        to_delete = DomainCoachingSession(
            id=uuid4(),
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.FRIEND,
            duration_min=45,
            fee_currency="TWD",
            fee_amount=2250,
            transcription_session_id=uuid4(),
        )
        sessions.append(to_delete)

        # Session never had transcript
        no_transcript = DomainCoachingSession(
            id=uuid4(),
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=date.today(),
            source=SessionSource.CLASSMATE,
            duration_min=30,
            fee_currency="TWD",
            fee_amount=1500,
        )
        sessions.append(no_transcript)

        # Save all sessions
        for session in sessions:
            repository.save(session)
        db_session.commit()

        # Get total minutes before deletion
        total_before = repository.get_total_minutes_for_user(test_user.id)
        assert total_before == 60 + 45 + 30  # 135 minutes

        # Act - Delete transcript from second session
        to_delete.transcription_session_id = None
        to_delete.transcript_deleted_at = datetime.now(timezone.utc)
        to_delete.saved_speaking_stats = {"coach_percentage": 70}
        repository.save(to_delete)
        db_session.commit()

        # Assert - Total minutes unchanged
        total_after = repository.get_total_minutes_for_user(test_user.id)
        assert total_after == 135
        assert total_after == total_before

    def test_monthly_minutes_unchanged_after_deletion(
        self, db_session, test_user, test_client, repository
    ):
        """Test that monthly minutes calculation remains accurate after deletion."""
        # Arrange
        current_date = date.today()
        session_id = uuid4()

        session = DomainCoachingSession(
            id=session_id,
            user_id=test_user.id,
            client_id=test_client.id,
            session_date=current_date,
            source=SessionSource.CLIENT,
            duration_min=90,
            fee_currency="USD",
            fee_amount=150,
            transcription_session_id=uuid4(),
        )
        repository.save(session)
        db_session.commit()

        # Get monthly minutes before deletion
        monthly_before = repository.get_monthly_minutes_for_user(
            test_user.id, current_date.year, current_date.month
        )
        assert monthly_before == 90

        # Act - Delete transcript
        session.transcription_session_id = None
        session.transcript_deleted_at = datetime.now(timezone.utc)
        session.saved_speaking_stats = {
            "coach_speaking_time": 3600,
            "client_speaking_time": 1800,
        }
        repository.save(session)
        db_session.commit()

        # Assert - Monthly minutes unchanged
        monthly_after = repository.get_monthly_minutes_for_user(
            test_user.id, current_date.year, current_date.month
        )
        assert monthly_after == 90
        assert monthly_after == monthly_before

    def test_revenue_calculations_unchanged_after_deletion(
        self, db_session, test_user, test_client, repository
    ):
        """Test that revenue calculations remain accurate after transcript deletion."""
        # Arrange - Create sessions with different currencies
        current_date = date.today()

        sessions = [
            DomainCoachingSession(
                id=uuid4(),
                user_id=test_user.id,
                client_id=test_client.id,
                session_date=current_date,
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=3000,
                transcription_session_id=uuid4(),
            ),
            DomainCoachingSession(
                id=uuid4(),
                user_id=test_user.id,
                client_id=test_client.id,
                session_date=current_date,
                source=SessionSource.CLIENT,
                duration_min=45,
                fee_currency="TWD",
                fee_amount=2250,
                transcription_session_id=uuid4(),
            ),
            DomainCoachingSession(
                id=uuid4(),
                user_id=test_user.id,
                client_id=test_client.id,
                session_date=current_date,
                source=SessionSource.FRIEND,
                duration_min=30,
                fee_currency="USD",
                fee_amount=100,
                transcription_session_id=uuid4(),
            ),
        ]

        for session in sessions:
            repository.save(session)
        db_session.commit()

        # Get revenue before deletion
        revenue_before = repository.get_monthly_revenue_by_currency(
            test_user.id, current_date.year, current_date.month
        )
        assert revenue_before == {"TWD": 5250, "USD": 100}

        # Act - Delete transcripts from all sessions
        for session in sessions:
            session.transcription_session_id = None
            session.transcript_deleted_at = datetime.now(timezone.utc)
            session.saved_speaking_stats = {"deleted": True}
            repository.save(session)
        db_session.commit()

        # Assert - Revenue unchanged
        revenue_after = repository.get_monthly_revenue_by_currency(
            test_user.id, current_date.year, current_date.month
        )
        assert revenue_after == {"TWD": 5250, "USD": 100}
        assert revenue_after == revenue_before

    def test_unique_clients_count_unchanged_after_deletion(
        self, db_session, test_user, repository
    ):
        """Test that unique clients count remains accurate after transcript deletion."""
        # Arrange - Create sessions with different clients
        clients = []
        for i in range(3):
            client = Client(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Client {i}",
                email=f"client{i}@test.com",
            )
            db_session.add(client)
            clients.append(client)
        db_session.commit()

        # Create sessions with transcripts
        sessions = []
        for client in clients:
            session = DomainCoachingSession(
                id=uuid4(),
                user_id=test_user.id,
                client_id=client.id,
                session_date=date.today(),
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=3000,
                transcription_session_id=uuid4(),
            )
            sessions.append(session)
            repository.save(session)
        db_session.commit()

        # Get unique clients before deletion
        clients_before = repository.get_unique_clients_count_for_user(test_user.id)
        assert clients_before == 3

        # Act - Delete all transcripts
        for session in sessions:
            session.transcription_session_id = None
            session.transcript_deleted_at = datetime.now(timezone.utc)
            repository.save(session)
        db_session.commit()

        # Assert - Unique clients count unchanged
        clients_after = repository.get_unique_clients_count_for_user(test_user.id)
        assert clients_after == 3
        assert clients_after == clients_before

    def test_session_integrity_with_mixed_deletion_states(
        self, db_session, test_user, test_client, repository
    ):
        """Test that mixed deletion states don't affect overall usage calculations."""
        # Arrange - Complex scenario with various states
        current_date = date.today()

        # Create transcription record
        transcription_id = uuid4()
        transcription = TranscriptionSession(
            id=transcription_id,
            user_id=test_user.id,
            title="Session Recording",
            audio_filename="session.mp3",
            duration_seconds=3600,
            language="zh-TW",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(transcription)

        sessions_data = [
            # Session with active transcript
            {
                "duration_min": 60,
                "fee_amount": 3000,
                "transcription_session_id": transcription_id,
                "transcript_deleted_at": None,
                "saved_speaking_stats": None,
            },
            # Session with deleted transcript
            {
                "duration_min": 45,
                "fee_amount": 2250,
                "transcription_session_id": None,
                "transcript_deleted_at": datetime.now(timezone.utc),
                "saved_speaking_stats": {"coach_percentage": 65},
            },
            # Session never had transcript
            {
                "duration_min": 30,
                "fee_amount": 1500,
                "transcription_session_id": None,
                "transcript_deleted_at": None,
                "saved_speaking_stats": None,
            },
            # Session with deleted transcript but preserved stats
            {
                "duration_min": 90,
                "fee_amount": 4500,
                "transcription_session_id": None,
                "transcript_deleted_at": datetime.now(timezone.utc),
                "saved_speaking_stats": {
                    "coach_speaking_time": 3600,
                    "client_speaking_time": 1800,
                    "coach_percentage": 66.67,
                    "client_percentage": 33.33,
                },
            },
        ]

        for data in sessions_data:
            session = DomainCoachingSession(
                id=uuid4(),
                user_id=test_user.id,
                client_id=test_client.id,
                session_date=current_date,
                source=SessionSource.CLIENT,
                fee_currency="TWD",
                **data,
            )
            repository.save(session)
        db_session.commit()

        # Assert - All calculations work correctly
        total_minutes = repository.get_total_minutes_for_user(test_user.id)
        assert total_minutes == 60 + 45 + 30 + 90  # 225 minutes

        monthly_minutes = repository.get_monthly_minutes_for_user(
            test_user.id, current_date.year, current_date.month
        )
        assert monthly_minutes == 225

        revenue = repository.get_monthly_revenue_by_currency(
            test_user.id, current_date.year, current_date.month
        )
        assert revenue == {"TWD": 3000 + 2250 + 1500 + 4500}  # 11250

        # Verify speaking stats are preserved for deleted sessions
        sessions = repository.get_by_coach_id(test_user.id)
        deleted_sessions = [s for s in sessions if s.transcript_deleted_at is not None]
        assert len(deleted_sessions) == 2
        for session in deleted_sessions:
            assert session.saved_speaking_stats is not None
            assert session.duration_min in [45, 90]  # Original durations preserved
