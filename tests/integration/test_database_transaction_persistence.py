"""Integration tests for database transaction persistence.

This module tests that the updated get_db() function correctly commits transactions
to ensure data persistence, specifically for the coaching session transcription_session_id
update issue that was reported.
"""

import pytest
from uuid import uuid4
from datetime import datetime, date

from src.coaching_assistant.core.database import get_db
from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
    SQLAlchemyCoachingSessionRepository,
)
from coaching_assistant.models.coaching_session import CoachingSession, SessionSource
from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.client import Client
from coaching_assistant.models.user import User, UserPlan


@pytest.mark.integration
class TestDatabaseTransactionPersistence:
    """Integration tests for transaction persistence with Clean Architecture."""

    def test_get_db_commits_transactions_automatically(self, db_engine):
        """Test that get_db() automatically commits successful transactions."""
        # Simulate the FastAPI dependency injection pattern
        db_gen = get_db()
        db_session = next(db_gen)

        try:
            # Create test data
            user = User(
                email="transaction_test@example.com",
                name="Transaction Test User",
                google_id="txn_test_123",
                plan=UserPlan.PRO,
            )
            db_session.add(user)
            db_session.flush()  # Get user ID

            client = Client(user_id=user.id, name="Transaction Test Client")
            db_session.add(client)
            db_session.flush()

            # Create coaching session
            coaching_session = CoachingSession(
                user_id=user.id,
                session_date=date.today(),
                client_id=client.id,
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=2000,
                notes="Transaction persistence test",
            )
            db_session.add(coaching_session)
            db_session.flush()
            coaching_session_id = coaching_session.id

        finally:
            # Simulate FastAPI cleanup - this should automatically commit
            try:
                db_gen.close()  # This triggers get_db()'s finally block with commit
            except StopIteration:
                pass  # Expected when generator finishes

        # Verify data persisted by creating a new session
        db_gen2 = get_db()
        db_session2 = next(db_gen2)

        try:
            # Data should be persisted due to automatic commit
            persisted_session = db_session2.query(CoachingSession).filter_by(
                id=coaching_session_id
            ).first()

            assert persisted_session is not None
            assert persisted_session.notes == "Transaction persistence test"
            assert persisted_session.user_id == user.id

        finally:
            try:
                db_gen2.close()
            except StopIteration:
                pass

    def test_coaching_session_transcription_id_persistence(self, db_engine):
        """Test the specific bug: transcription_session_id updates persist correctly."""
        # Phase 1: Create initial coaching session (simulates frontend session creation)
        db_gen1 = get_db()
        db_session1 = next(db_gen1)

        try:
            user = User(
                email="persistence_test@example.com",
                name="Persistence Test User",
                google_id="persist_123",
                plan=UserPlan.FREE,
            )
            db_session1.add(user)
            db_session1.flush()

            client = Client(user_id=user.id, name="Persistence Test Client")
            db_session1.add(client)
            db_session1.flush()

            coaching_session = CoachingSession(
                user_id=user.id,
                session_date=date.today(),
                client_id=client.id,
                source=SessionSource.CLIENT,
                duration_min=45,
                transcription_session_id=None,  # Initially null
                notes="Initial session",
            )
            db_session1.add(coaching_session)
            db_session1.flush()
            coaching_session_id = coaching_session.id

        finally:
            try:
                db_gen1.close()  # Should commit automatically
            except StopIteration:
                pass

        # Phase 2: Create transcription session and update coaching session
        # (simulates audio upload and linking)
        db_gen2 = get_db()
        db_session2 = next(db_gen2)

        try:
            # Create transcription session
            transcription_session = Session(
                id=uuid4(),
                user_id=user.id,
                title="Audio Upload Session",
                status=SessionStatus.UPLOADING,
                language="cmn-Hant-TW",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session2.add(transcription_session)
            db_session2.flush()
            transcription_session_id = transcription_session.id

            # Update coaching session with transcription_session_id
            # This simulates the exact workflow from the bug report
            repo = SQLAlchemyCoachingSessionRepository(db_session2)
            retrieved_session = repo.get_by_id(coaching_session_id)

            assert retrieved_session is not None
            assert retrieved_session.transcription_session_id is None  # Initially null

            # Update with transcription session ID (this was failing to persist)
            updated_session = repo.update_transcription_session_id(
                coaching_session_id,
                transcription_session_id
            )

            assert updated_session.transcription_session_id == transcription_session_id

        finally:
            try:
                db_gen2.close()  # Should commit automatically - THIS WAS THE BUG
            except StopIteration:
                pass

        # Phase 3: Verify persistence in a new session (simulates page refresh)
        # This is where the bug was detected - transcription_session_id was null
        db_gen3 = get_db()
        db_session3 = next(db_gen3)

        try:
            # This simulates the frontend fetching the session after navigation
            repo = SQLAlchemyCoachingSessionRepository(db_session3)
            final_session = repo.get_by_id(coaching_session_id)

            # The critical assertion - this was failing before the fix
            assert final_session is not None
            assert final_session.transcription_session_id == transcription_session_id
            assert final_session.transcription_session_id is not None

            # Also verify the transcription session exists
            transcription = db_session3.query(Session).filter_by(
                id=transcription_session_id
            ).first()
            assert transcription is not None
            assert transcription.title == "Audio Upload Session"

        finally:
            try:
                db_gen3.close()
            except StopIteration:
                pass

    def test_transaction_rollback_on_error(self, db_engine):
        """Test that failed transactions are properly rolled back."""
        db_gen = get_db()
        db_session = next(db_gen)

        try:
            # Create a user
            user = User(
                email="rollback_test@example.com",
                name="Rollback Test User",
                google_id="rollback_123",
                plan=UserPlan.PRO,
            )
            db_session.add(user)
            db_session.flush()
            user_id = user.id

            # Force an error by violating a constraint
            # (creating duplicate user with same google_id)
            duplicate_user = User(
                email="duplicate@example.com",
                name="Duplicate User",
                google_id="rollback_123",  # Same google_id - should fail
                plan=UserPlan.FREE,
            )
            db_session.add(duplicate_user)

            # This should fail due to unique constraint on google_id
            with pytest.raises(Exception):
                db_session.flush()

        except Exception:
            # Expected exception
            pass
        finally:
            try:
                db_gen.close()  # Should rollback on error
            except StopIteration:
                pass

        # Verify rollback occurred - neither user should exist
        db_gen2 = get_db()
        db_session2 = next(db_gen2)

        try:
            users = db_session2.query(User).filter_by(google_id="rollback_123").all()
            assert len(users) == 0  # Both users should be rolled back

        finally:
            try:
                db_gen2.close()
            except StopIteration:
                pass

    def test_multiple_repository_operations_persist(self, db_engine):
        """Test that multiple repository operations within one request persist together."""
        db_gen = get_db()
        db_session = next(db_gen)

        try:
            # Use repository pattern like the real application
            from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
                SQLAlchemyCoachingSessionRepository,
            )

            user = User(
                email="multi_repo_test@example.com",
                name="Multi Repository Test",
                google_id="multi_repo_123",
                plan=UserPlan.STUDENT,
            )
            db_session.add(user)
            db_session.flush()

            client = Client(user_id=user.id, name="Multi Repo Client")
            db_session.add(client)
            db_session.flush()

            # Create multiple sessions using repository pattern
            repo = SQLAlchemyCoachingSessionRepository(db_session)

            session_ids = []
            for i in range(3):
                coaching_session = CoachingSession(
                    user_id=user.id,
                    session_date=date.today(),
                    client_id=client.id,
                    source=SessionSource.CLIENT,
                    duration_min=30 + i * 15,
                    fee_currency="USD",
                    fee_amount=100 + i * 50,
                    notes=f"Multi repo session {i+1}",
                )
                saved_session = repo.save(coaching_session)
                session_ids.append(saved_session.id)

        finally:
            try:
                db_gen.close()  # Should commit all operations
            except StopIteration:
                pass

        # Verify all operations persisted
        db_gen2 = get_db()
        db_session2 = next(db_gen2)

        try:
            repo2 = SQLAlchemyCoachingSessionRepository(db_session2)

            for i, session_id in enumerate(session_ids):
                session = repo2.get_by_id(session_id)
                assert session is not None
                assert session.notes == f"Multi repo session {i+1}"
                assert session.duration_min == 30 + i * 15
                assert session.fee_amount == 100 + i * 50

        finally:
            try:
                db_gen2.close()
            except StopIteration:
                pass

    def test_repository_flush_vs_commit_behavior(self, db_engine):
        """Test that repository flush() works correctly with automatic commit."""
        db_gen = get_db()
        db_session = next(db_gen)

        try:
            from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
                SQLAlchemyCoachingSessionRepository,
            )

            user = User(
                email="flush_test@example.com",
                name="Flush Test User",
                google_id="flush_123",
                plan=UserPlan.PRO,
            )
            db_session.add(user)
            db_session.flush()

            client = Client(user_id=user.id, name="Flush Test Client")
            db_session.add(client)
            db_session.flush()

            repo = SQLAlchemyCoachingSessionRepository(db_session)

            # Repository uses flush() internally - should work with our commit
            coaching_session = CoachingSession(
                user_id=user.id,
                session_date=date.today(),
                client_id=client.id,
                source=SessionSource.RESEARCH,
                duration_min=90,
                notes="Flush behavior test",
            )

            saved_session = repo.save(coaching_session)  # This calls flush() internally
            session_id = saved_session.id

            # Verify we can read it back in the same transaction
            retrieved = repo.get_by_id(session_id)
            assert retrieved is not None
            assert retrieved.notes == "Flush behavior test"

        finally:
            try:
                db_gen.close()  # Auto-commit should persist the flush
            except StopIteration:
                pass

        # Verify persistence across sessions
        db_gen2 = get_db()
        db_session2 = next(db_gen2)

        try:
            repo2 = SQLAlchemyCoachingSessionRepository(db_session2)
            persisted_session = repo2.get_by_id(session_id)

            assert persisted_session is not None
            assert persisted_session.notes == "Flush behavior test"
            assert persisted_session.duration_min == 90

        finally:
            try:
                db_gen2.close()
            except StopIteration:
                pass