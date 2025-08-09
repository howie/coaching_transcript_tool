"""Tests for CoachingSession with SessionSource field."""

import pytest
from datetime import date
from coaching_assistant.models import CoachingSession, SessionSource, User, Client


class TestCoachingSessionSource:
    """Test CoachingSession with SessionSource field."""

    def test_create_coaching_session_with_source(self, db_session):
        """Test creating a coaching session with all SessionSource values."""
        # Create a coach user
        coach = User(
            email="coach@example.com",
            name="Test Coach",
            google_id="coach123"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client"
        )
        db_session.add(client)
        db_session.flush()

        # Test each SessionSource enum value
        sources = [SessionSource.CLIENT, SessionSource.FRIEND, SessionSource.CLASSMATE, SessionSource.SUBORDINATE]
        
        for source in sources:
            session = CoachingSession(
                coach_id=coach.id,
                client_id=client.id,
                session_date=date.today(),
                source=source,
                duration_min=60,
                fee_currency="USD",
                fee_amount=100
            )
            db_session.add(session)
            db_session.flush()
            
            # Verify the source was set correctly
            assert session.source == source
            assert session.source.value in ["CLIENT", "FRIEND", "CLASSMATE", "SUBORDINATE"]

        db_session.commit()

    def test_coaching_session_source_required(self, db_session):
        """Test that source field is required."""
        # Create a coach user
        coach = User(
            email="coach2@example.com",
            name="Test Coach 2",
            google_id="coach456"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client 2"
        )
        db_session.add(client)
        db_session.flush()

        # Try to create a coaching session without source - should fail
        session = CoachingSession(
            coach_id=coach.id,
            client_id=client.id,
            session_date=date.today(),
            # source=... # Missing required field
            duration_min=60,
            fee_currency="USD",
            fee_amount=100
        )
        db_session.add(session)
        
        with pytest.raises(Exception):  # Should raise an integrity constraint error
            db_session.commit()

    def test_coaching_session_source_enum_validation(self, db_session):
        """Test that only valid SessionSource enum values are accepted."""
        # Create a coach user
        coach = User(
            email="coach3@example.com",
            name="Test Coach 3",
            google_id="coach789"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client 3"
        )
        db_session.add(client)
        db_session.flush()

        # Test that we can't assign invalid enum values
        session = CoachingSession(
            coach_id=coach.id,
            client_id=client.id,
            session_date=date.today(),
            source=SessionSource.CLIENT,  # Valid value
            duration_min=60,
            fee_currency="USD",
            fee_amount=100
        )
        
        # This should work fine
        db_session.add(session)
        db_session.commit()
        
        # Verify the session was created successfully
        assert session.source == SessionSource.CLIENT

    def test_session_source_enum_values(self):
        """Test that SessionSource enum has correct values."""
        assert SessionSource.CLIENT.value == "CLIENT"
        assert SessionSource.FRIEND.value == "FRIEND"
        assert SessionSource.CLASSMATE.value == "CLASSMATE"
        assert SessionSource.SUBORDINATE.value == "SUBORDINATE"
        
        # Test that all expected enum values exist
        expected_values = {"CLIENT", "FRIEND", "CLASSMATE", "SUBORDINATE"}
        actual_values = {source.value for source in SessionSource}
        assert actual_values == expected_values

    def test_coaching_session_repr_with_source(self, db_session):
        """Test that CoachingSession __repr__ works correctly with source field."""
        # Create a coach user
        coach = User(
            email="coach4@example.com",
            name="Test Coach 4",
            google_id="coach999"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client 4"
        )
        db_session.add(client)
        db_session.flush()

        # Create a coaching session
        session = CoachingSession(
            coach_id=coach.id,
            client_id=client.id,
            session_date=date.today(),
            source=SessionSource.FRIEND,
            duration_min=90,
            fee_currency="EUR",
            fee_amount=150
        )
        db_session.add(session)
        db_session.commit()

        # Test that repr() works without errors
        repr_str = repr(session)
        assert "CoachingSession" in repr_str
        assert str(session.session_date) in repr_str
        assert str(session.client_id) in repr_str
        assert "90min" in repr_str

    def test_coaching_session_relationships_with_source(self, db_session):
        """Test that relationships still work correctly with source field added."""
        # Create a coach user
        coach = User(
            email="coach5@example.com",
            name="Test Coach 5",
            google_id="coach555"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client 5"
        )
        db_session.add(client)
        db_session.flush()

        # Create a coaching session
        session = CoachingSession(
            coach_id=coach.id,
            client_id=client.id,
            session_date=date.today(),
            source=SessionSource.CLASSMATE,
            duration_min=45,
            fee_currency="GBP",
            fee_amount=75
        )
        db_session.add(session)
        db_session.commit()

        # Test relationships work correctly
        assert session.coach == coach
        assert session.client == client
        assert session in coach.coaching_sessions
        assert session in client.coaching_sessions

    def test_multiple_sessions_different_sources(self, db_session):
        """Test creating multiple sessions with different sources for same client."""
        # Create a coach user
        coach = User(
            email="coach6@example.com",
            name="Test Coach 6",
            google_id="coach666"
        )
        db_session.add(coach)
        db_session.flush()

        # Create a client
        client = Client(
            coach_id=coach.id,
            name="Test Client 6"
        )
        db_session.add(client)
        db_session.flush()

        # Create multiple sessions with different sources
        sessions = []
        sources_and_dates = [
            (SessionSource.CLIENT, date(2024, 1, 15)),
            (SessionSource.FRIEND, date(2024, 2, 15)),
            (SessionSource.CLASSMATE, date(2024, 3, 15)),
            (SessionSource.SUBORDINATE, date(2024, 4, 15))
        ]

        for source, session_date in sources_and_dates:
            session = CoachingSession(
                coach_id=coach.id,
                client_id=client.id,
                session_date=session_date,
                source=source,
                duration_min=60,
                fee_currency="USD",
                fee_amount=100
            )
            sessions.append(session)
            db_session.add(session)

        db_session.commit()

        # Verify all sessions were created with correct sources
        for session, (expected_source, expected_date) in zip(sessions, sources_and_dates):
            assert session.source == expected_source
            assert session.session_date == expected_date

        # Verify client has all sessions
        assert len(list(client.coaching_sessions)) == 4