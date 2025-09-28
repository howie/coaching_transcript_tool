"""Test coaching sessions API with transcription_session_id field."""

from datetime import date
from uuid import uuid4

from coaching_assistant.models.client import Client
from coaching_assistant.models.coaching_session import (
    CoachingSession,
    SessionSource,
)
from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.user import User, UserPlan


class TestCoachingSessionsAPI:
    """Test API models and database operations for coaching sessions with transcription_session_id."""

    def test_create_coaching_session_with_transcription_session_id(self, db_session):
        """Test creating a coaching session and linking it to a transcription session."""

        # Create a user
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="123456789",
            plan=UserPlan.FREE,
        )
        db_session.add(user)
        db_session.flush()

        # Create a client
        client = Client(user_id=user.id, name="Test Client")
        db_session.add(client)
        db_session.flush()

        # Create a transcription session first
        transcription_session = Session(
            id=uuid4(),
            user_id=user.id,
            title="Test Transcription Session",
            status=SessionStatus.COMPLETED,
            language="cmn-Hant-TW",
            duration_seconds=3600,
            audio_filename="test_audio.wav",
        )
        db_session.add(transcription_session)
        db_session.flush()

        # Create coaching session linked to transcription
        coaching_session = CoachingSession(
            user_id=user.id,
            session_date=date(2025, 8, 14),
            client_id=client.id,
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000,
            transcription_session_id=transcription_session.id,
            notes="Test session with transcription",
        )
        db_session.add(coaching_session)
        db_session.commit()

        # Verify the coaching session was created correctly
        assert coaching_session.transcription_session_id == transcription_session.id
        assert coaching_session.user_id == user.id
        assert coaching_session.client_id == client.id

    def test_coaching_session_with_transcription_session_id_relationship(
        self, db_session
    ):
        """Test that coaching sessions correctly link to transcription sessions."""

        # Create a user
        user = User(
            email="test2@example.com",
            name="Test User 2",
            google_id="987654321",
            plan=UserPlan.PRO,
        )
        db_session.add(user)
        db_session.flush()

        # Create a client
        client = Client(user_id=user.id, name="Test Client 2")
        db_session.add(client)
        db_session.flush()

        # Create a transcription session
        transcription_session = Session(
            id=uuid4(),
            user_id=user.id,
            title="Test Transcription",
            status=SessionStatus.COMPLETED,
            language="en-US",
            duration_seconds=1800,
        )
        db_session.add(transcription_session)
        db_session.flush()

        # Create a coaching session with transcription_session_id
        coaching_session = CoachingSession(
            user_id=user.id,
            session_date=date(2025, 8, 14),
            client_id=client.id,
            source=SessionSource.CLIENT,
            duration_min=30,
            fee_currency="USD",
            fee_amount=100,
            transcription_session_id=transcription_session.id,
            notes="Linked session",
        )
        db_session.add(coaching_session)
        db_session.commit()

        # Verify the relationship
        assert coaching_session.transcription_session_id == transcription_session.id
        assert coaching_session.notes == "Linked session"
        assert not hasattr(
            coaching_session, "audio_timeseq_id"
        )  # Old field should not exist

    def test_multiple_sessions_with_mixed_transcription_links(self, db_session):
        """Test multiple coaching sessions, some with and some without transcription links."""

        # Create a user
        user = User(
            email="test3@example.com",
            name="Test User 3",
            google_id="111222333",
            plan=UserPlan.FREE,
        )
        db_session.add(user)
        db_session.flush()

        # Create a client
        client = Client(user_id=user.id, name="Test Client 3")
        db_session.add(client)
        db_session.flush()

        # Create a transcription session
        transcription_session = Session(
            id=uuid4(),
            user_id=user.id,
            title="Linked Transcription",
            status=SessionStatus.COMPLETED,
            language="cmn-Hant-TW",
            duration_seconds=2400,
        )
        db_session.add(transcription_session)
        db_session.flush()

        # Session with transcription
        session_with_transcription = CoachingSession(
            user_id=user.id,
            session_date=date(2025, 8, 14),
            client_id=client.id,
            source=SessionSource.CLIENT,
            duration_min=40,
            fee_currency="TWD",
            fee_amount=1600,
            transcription_session_id=transcription_session.id,
        )

        # Session without transcription
        session_without_transcription = CoachingSession(
            user_id=user.id,
            session_date=date(2025, 8, 15),
            client_id=client.id,
            source=SessionSource.FRIEND,
            duration_min=50,
            fee_currency="TWD",
            fee_amount=2000,
        )

        db_session.add_all([session_with_transcription, session_without_transcription])
        db_session.commit()

        # Verify session with transcription
        assert (
            session_with_transcription.transcription_session_id
            == transcription_session.id
        )

        # Verify session without transcription
        assert session_without_transcription.transcription_session_id is None

    def test_coaching_session_model_consistency(self, db_session):
        """Test that the database model uses the correct field name."""

        # Create a user
        user = User(
            email="test4@example.com",
            name="Test User 4",
            google_id="444555666",
            plan=UserPlan.PRO,
        )
        db_session.add(user)
        db_session.flush()

        # Create a client
        client = Client(user_id=user.id, name="Test Client 4")
        db_session.add(client)
        db_session.flush()

        # Create a session directly with the model
        transcription_session_id = uuid4()

        coaching_session = CoachingSession(
            user_id=user.id,
            session_date=date(2025, 8, 14),
            client_id=client.id,
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000,
            transcription_session_id=transcription_session_id,
        )

        db_session.add(coaching_session)
        db_session.commit()
        db_session.refresh(coaching_session)

        # Verify the field is correctly stored and retrieved
        assert coaching_session.transcription_session_id == transcription_session_id

        # Verify that the old field name doesn't exist in the model
        assert not hasattr(coaching_session, "audio_timeseq_id")

    def test_list_endpoint_returns_transcription_summary_with_segments_count(
        self, db_session, authenticated_client, test_user
    ):
        """Ensure list API includes transcription summary without crashing."""

        client = Client(user_id=test_user.id, name="List Test Client")
        db_session.add(client)
        db_session.flush()

        transcription_session = Session(
            user_id=test_user.id,
            title="Linked transcription",
            status=SessionStatus.COMPLETED,
            language="en-US",
            duration_seconds=900,
        )
        db_session.add(transcription_session)
        db_session.flush()

        coaching_session = CoachingSession(
            user_id=test_user.id,
            client_id=client.id,
            session_date=date(2025, 9, 24),
            source=SessionSource.CLIENT,
            duration_min=45,
            fee_currency="USD",
            fee_amount=150,
            transcription_session_id=transcription_session.id,
        )
        db_session.add(coaching_session)
        db_session.commit()

        response = authenticated_client.get(
            "/api/v1/coaching-sessions?page=1&page_size=20&sort=-session_date"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        transcription_summary = data["items"][0]["transcription_session"]
        assert transcription_summary is not None
        assert transcription_summary["segments_count"] == 0
