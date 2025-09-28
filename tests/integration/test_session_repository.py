"""Integration tests for session repository.

This module tests the SQLAlchemySessionRepository with real database operations,
ensuring proper domain ↔ ORM conversion and transaction integrity.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.coaching_assistant.core.models.session import Session, SessionStatus
from src.coaching_assistant.infrastructure.db.repositories.session_repository import (
    SQLAlchemySessionRepository,
    create_session_repository,
)


@pytest.mark.integration
class TestSessionRepositoryIntegration:
    """Integration tests for SQLAlchemySessionRepository with real database."""

    def test_save_and_get_session(self, db_session, sample_user):
        """Test saving and retrieving a session."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Integration Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Act
        saved_session = repo.save(session)
        db_session.commit()

        # Assert
        assert saved_session.id is not None

        # Retrieve and verify
        retrieved_session = repo.get_by_id(saved_session.id)
        assert retrieved_session is not None
        assert retrieved_session.user_id == sample_user.id
        assert retrieved_session.title == "Integration Test Session"
        assert retrieved_session.language == "cmn-Hant-TW"
        assert retrieved_session.status == SessionStatus.UPLOADING

    def test_get_by_user_id_with_filtering(self, db_session, sample_user):
        """Test getting sessions by user ID with status filtering."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Create multiple sessions with different statuses
        session1 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Session 1",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session2 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Session 2",
            status=SessionStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow() - timedelta(hours=1),
        )

        session3 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Session 3",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=2),
        )

        repo.save(session1)
        repo.save(session2)
        repo.save(session3)
        db_session.commit()

        # Act - Get all sessions
        all_sessions = repo.get_by_user_id(sample_user.id)

        # Act - Get only UPLOADING sessions
        uploading_sessions = repo.get_by_user_id(
            sample_user.id, status=SessionStatus.UPLOADING
        )

        # Act - Get with limit
        limited_sessions = repo.get_by_user_id(sample_user.id, limit=2)

        # Assert
        assert len(all_sessions) == 3
        assert len(uploading_sessions) == 2  # session1 and session3
        assert len(limited_sessions) == 2

        # Verify ordering (most recent first)
        assert all_sessions[0].title == "Session 1"  # Most recent
        assert all_sessions[2].title == "Session 3"  # Oldest

        # Verify filtering
        for session in uploading_sessions:
            assert session.status == SessionStatus.UPLOADING

    def test_update_status(self, db_session, sample_user):
        """Test updating session status."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Status Update Test",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        saved_session = repo.save(session)
        db_session.commit()

        # Act
        updated_session = repo.update_status(saved_session.id, SessionStatus.PENDING)
        db_session.commit()

        # Assert
        assert updated_session.status == SessionStatus.PENDING
        assert updated_session.updated_at > saved_session.updated_at

        # Verify in database
        retrieved_session = repo.get_by_id(saved_session.id)
        assert retrieved_session.status == SessionStatus.PENDING

    def test_count_user_sessions(self, db_session, sample_user):
        """Test counting user sessions."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Create sessions
        for i in range(3):
            session = Session(
                id=uuid4(),
                user_id=sample_user.id,
                title=f"Count Test Session {i + 1}",
                status=SessionStatus.UPLOADING,
                created_at=datetime.utcnow() - timedelta(hours=i),
                updated_at=datetime.utcnow() - timedelta(hours=i),
            )
            repo.save(session)

        db_session.commit()

        # Act
        total_count = repo.count_user_sessions(sample_user.id)
        recent_count = repo.count_user_sessions(
            sample_user.id, since=datetime.utcnow() - timedelta(minutes=30)
        )

        # Assert
        assert total_count == 3
        assert recent_count == 1  # Only the most recent session

    def test_get_total_duration_minutes(self, db_session, sample_user):
        """Test calculating total duration in minutes."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Create sessions with different durations
        session1 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Duration Test 1",
            duration_seconds=300,  # 5 minutes
            status=SessionStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session2 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Duration Test 2",
            duration_seconds=600,  # 10 minutes
            status=SessionStatus.COMPLETED,
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow() - timedelta(hours=1),
        )

        session3 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Duration Test 3",
            duration_seconds=None,  # No duration
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=2),
        )

        repo.save(session1)
        repo.save(session2)
        repo.save(session3)
        db_session.commit()

        # Act
        total_minutes = repo.get_total_duration_minutes(sample_user.id)
        recent_minutes = repo.get_total_duration_minutes(
            sample_user.id, since=datetime.utcnow() - timedelta(minutes=30)
        )

        # Assert
        assert total_minutes == 15  # 5 + 10 minutes (session3 has no duration)
        assert recent_minutes == 5  # Only session1 is recent

    def test_get_sessions_by_date_range(self, db_session, sample_user):
        """Test getting sessions within date range."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)
        base_time = datetime.utcnow()

        # Create sessions at different times
        session1 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Date Range Test 1",
            status=SessionStatus.UPLOADING,
            created_at=base_time - timedelta(days=3),
            updated_at=base_time - timedelta(days=3),
        )

        session2 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Date Range Test 2",
            status=SessionStatus.COMPLETED,
            created_at=base_time - timedelta(days=1),
            updated_at=base_time - timedelta(days=1),
        )

        session3 = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Date Range Test 3",
            status=SessionStatus.PENDING,
            created_at=base_time,
            updated_at=base_time,
        )

        repo.save(session1)
        repo.save(session2)
        repo.save(session3)
        db_session.commit()

        # Act
        recent_sessions = repo.get_sessions_by_date_range(
            sample_user.id,
            start_date=base_time - timedelta(days=2),
            end_date=base_time + timedelta(hours=1),
        )

        # Assert
        assert len(recent_sessions) == 2  # session2 and session3
        # Verify ordering by created_at
        assert recent_sessions[0].created_at <= recent_sessions[1].created_at

    def test_save_updates_existing_session(self, db_session, sample_user):
        """Test that save() updates existing session instead of creating duplicate."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Original Title",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        saved_session = repo.save(session)
        db_session.commit()

        # Act - Update the same session
        updated_session = Session(
            id=saved_session.id,
            user_id=sample_user.id,
            title="Updated Title",
            status=SessionStatus.PENDING,
            created_at=saved_session.created_at,
            updated_at=datetime.utcnow(),
        )
        final_session = repo.save(updated_session)
        db_session.commit()

        # Assert
        assert final_session.id == saved_session.id  # Same ID
        assert final_session.title == "Updated Title"
        assert final_session.status == SessionStatus.PENDING

        # Verify only one record exists
        all_sessions = repo.get_by_user_id(sample_user.id)
        assert len(all_sessions) == 1
        assert all_sessions[0].title == "Updated Title"

    def test_database_error_handling(self, db_session):
        """Test database error handling."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Act & Assert - should handle non-existent session gracefully
        result = repo.get_by_id(uuid4())
        assert result is None

        # Test with invalid session ID for update_status
        with pytest.raises(ValueError, match="Session .* not found"):
            repo.update_status(uuid4(), SessionStatus.PENDING)

    def test_session_state_validation(self, db_session, sample_user):
        """Test session state validation."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Close session to simulate inactive state
        db_session.close()

        # Act - should handle inactive session gracefully
        with pytest.raises(RuntimeError, match="Database error"):
            repo.get_by_id(uuid4())

    def test_domain_to_orm_conversion_accuracy(self, db_session, sample_user):
        """Test accuracy of domain ↔ ORM conversion."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        original_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Conversion Test Session",
            language="en-US",
            audio_filename="test.mp3",
            duration_seconds=450,
            status=SessionStatus.PROCESSING,
            error_message="Test error",
            gcs_audio_path="gs://bucket/audio.mp3",
            stt_provider="google",
            transcription_job_id="job-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Act
        saved_session = repo.save(original_session)
        db_session.commit()

        retrieved_session = repo.get_by_id(saved_session.id)

        # Assert - All fields should be preserved
        assert retrieved_session.id == original_session.id
        assert retrieved_session.user_id == original_session.user_id
        assert retrieved_session.title == original_session.title
        assert retrieved_session.language == original_session.language
        assert retrieved_session.audio_filename == original_session.audio_filename
        assert retrieved_session.duration_seconds == original_session.duration_seconds
        assert retrieved_session.status == original_session.status
        assert retrieved_session.error_message == original_session.error_message
        assert retrieved_session.gcs_audio_path == original_session.gcs_audio_path
        assert retrieved_session.stt_provider == original_session.stt_provider
        assert (
            retrieved_session.transcription_job_id
            == original_session.transcription_job_id
        )

    def test_repository_factory_function(self, db_session):
        """Test the repository factory function."""
        # Act
        repo = create_session_repository(db_session)

        # Assert
        assert isinstance(repo, SQLAlchemySessionRepository)
        assert repo.session is db_session

    def test_concurrent_session_updates(self, db_session, sample_user):
        """Test handling of concurrent session updates."""
        # Arrange
        repo1 = SQLAlchemySessionRepository(db_session)
        repo2 = SQLAlchemySessionRepository(db_session)

        session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Concurrency Test",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        saved_session = repo1.save(session)
        db_session.commit()

        # Act - Simulate concurrent updates
        repo1.update_status(saved_session.id, SessionStatus.PENDING)
        repo2.update_status(saved_session.id, SessionStatus.PROCESSING)

        db_session.commit()

        # Assert - Last update should win
        final_session = repo1.get_by_id(saved_session.id)
        assert final_session.status == SessionStatus.PROCESSING

    def test_session_filtering_performance(self, db_session, sample_user):
        """Test performance of session filtering operations."""
        # Arrange
        repo = SQLAlchemySessionRepository(db_session)

        # Create many sessions
        sessions = []
        for i in range(50):
            session = Session(
                id=uuid4(),
                user_id=sample_user.id,
                title=f"Performance Test Session {i + 1}",
                status=(
                    SessionStatus.UPLOADING if i % 2 == 0 else SessionStatus.COMPLETED
                ),
                created_at=datetime.utcnow() - timedelta(hours=i),
                updated_at=datetime.utcnow() - timedelta(hours=i),
            )
            sessions.append(repo.save(session))

        db_session.commit()

        # Act - Test various filtering operations
        import time

        start_time = time.time()
        all_sessions = repo.get_by_user_id(sample_user.id, limit=20)
        end_time = time.time()

        # Assert - Operations should complete reasonably quickly
        assert len(all_sessions) == 20
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

        # Test status filtering
        uploading_sessions = repo.get_by_user_id(
            sample_user.id, status=SessionStatus.UPLOADING
        )
        assert len(uploading_sessions) == 25  # Half should be UPLOADING
