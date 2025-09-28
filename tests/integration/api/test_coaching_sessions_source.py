"""Test coaching sessions API with SessionSource field."""

from datetime import date
from uuid import uuid4

import pytest

from coaching_assistant.api.coaching_sessions import (
    CoachingSessionCreate,
    SessionSource,
)


class TestCoachingSessionsAPIModels:
    """Test API models for coaching sessions with SessionSource."""

    def test_coaching_session_create_with_source(self):
        """Test creating CoachingSessionCreate with explicit source."""
        session_data = CoachingSessionCreate(
            session_date=date.today(),
            client_id=uuid4(),
            source=SessionSource.FRIEND,
            duration_min=60,
            fee_currency="USD",
            fee_amount=100,
            notes="Test session",
        )

        assert session_data.source == SessionSource.FRIEND
        assert session_data.source.value == "FRIEND"

    def test_coaching_session_create_default_source(self):
        """Test that CoachingSessionCreate defaults to CLIENT source."""
        session_data = CoachingSessionCreate(
            session_date=date.today(),
            client_id=uuid4(),
            duration_min=45,
            fee_currency="EUR",
            fee_amount=75,
        )

        assert session_data.source == SessionSource.CLIENT
        assert session_data.source.value == "CLIENT"

    def test_all_session_source_values(self):
        """Test that all SessionSource enum values work."""
        sources = [
            SessionSource.CLIENT,
            SessionSource.FRIEND,
            SessionSource.CLASSMATE,
            SessionSource.SUBORDINATE,
        ]

        for source in sources:
            session_data = CoachingSessionCreate(
                session_date=date.today(),
                client_id=uuid4(),
                source=source,
                duration_min=30,
                fee_currency="GBP",
                fee_amount=50,
            )

            assert session_data.source == source
            assert session_data.source.value in [
                "CLIENT",
                "FRIEND",
                "CLASSMATE",
                "SUBORDINATE",
            ]

    def test_coaching_session_create_validation(self):
        """Test that validation still works with source field."""
        # Test invalid duration
        with pytest.raises(Exception):  # ValidationError from pydantic
            CoachingSessionCreate(
                session_date=date.today(),
                client_id=uuid4(),
                source=SessionSource.CLIENT,
                duration_min=0,  # Invalid: must be > 0
                fee_currency="USD",
                fee_amount=100,
            )

        # Test invalid currency
        with pytest.raises(Exception):  # ValidationError from pydantic
            CoachingSessionCreate(
                session_date=date.today(),
                client_id=uuid4(),
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="INVALID",  # Invalid: must be 3 chars
                fee_amount=100,
            )

    def test_coaching_session_create_serialization(self):
        """Test that CoachingSessionCreate can be serialized properly."""
        session_data = CoachingSessionCreate(
            session_date=date(2025, 8, 10),
            client_id=uuid4(),
            source=SessionSource.CLASSMATE,
            duration_min=90,
            fee_currency="TWD",
            fee_amount=2000,
            notes="Important session",
        )

        # Test dict conversion
        session_dict = session_data.model_dump()

        assert session_dict["source"] == SessionSource.CLASSMATE  # Enum in dict
        assert session_dict["duration_min"] == 90
        assert session_dict["fee_currency"] == "TWD"
        assert session_dict["notes"] == "Important session"
