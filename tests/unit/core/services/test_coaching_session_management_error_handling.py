"""Error handling tests for coaching session management use cases.

Tests focus on error paths, edge cases, and exception handling to improve
coverage from 20% toward 60%+.
"""

from datetime import UTC, date, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from coaching_assistant.core.models.client import Client
from coaching_assistant.core.models.coaching_session import (
    CoachingSession,
    SessionSource,
)
from coaching_assistant.core.models.user import User, UserPlan
from coaching_assistant.core.services.coaching_session_management_use_case import (
    CoachingSessionCreationUseCase,
    CoachingSessionDeletionUseCase,
    CoachingSessionOptionsUseCase,
    CoachingSessionRetrievalUseCase,
    CoachingSessionUpdateUseCase,
)


class TestCoachingSessionRetrievalErrorHandling:
    """Test error handling in CoachingSessionRetrievalUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "session_repo": Mock(),
            "user_repo": Mock(),
            "client_repo": Mock(),
            "transcription_session_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return CoachingSessionRetrievalUseCase(
            session_repo=mock_repos["session_repo"],
            user_repo=mock_repos["user_repo"],
            client_repo=mock_repos["client_repo"],
            transcription_session_repo=mock_repos["transcription_session_repo"],
        )

    def test_get_session_by_id_returns_none_when_not_found(self, use_case, mock_repos):
        """Test that None is returned when session not found."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_repos["session_repo"].get_with_ownership_check.return_value = None

        # Act
        result = use_case.get_session_by_id(session_id, coach_id)

        # Assert
        assert result is None
        mock_repos["session_repo"].get_with_ownership_check.assert_called_once_with(
            session_id, coach_id
        )

    def test_get_session_by_id_handles_database_error(self, use_case, mock_repos):
        """Test handling of database errors."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_repos[
            "session_repo"
        ].get_with_ownership_check.side_effect = OperationalError(
            "Database connection failed", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.get_session_by_id(session_id, coach_id)

    def test_list_sessions_raises_error_when_coach_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when coach doesn't exist."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.list_sessions_paginated(coach_id)

        assert "Coach with ID" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_list_sessions_handles_database_error_on_user_fetch(
        self, use_case, mock_repos
    ):
        """Test handling of database errors when fetching user."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.side_effect = OperationalError(
            "Connection timeout", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.list_sessions_paginated(coach_id)

    def test_list_sessions_handles_database_error_on_session_fetch(
        self, use_case, mock_repos
    ):
        """Test handling of database errors when fetching sessions."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos[
            "session_repo"
        ].get_paginated_with_filters.side_effect = OperationalError(
            "Query timeout", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.list_sessions_paginated(coach_id)

    def test_list_sessions_handles_empty_results(self, use_case, mock_repos):
        """Test handling of no sessions found."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["session_repo"].get_paginated_with_filters.return_value = ([], 0)

        # Act
        sessions, total, total_pages = use_case.list_sessions_paginated(coach_id)

        # Assert
        assert sessions == []
        assert total == 0
        assert total_pages == 0

    def test_list_sessions_with_invalid_page_number(self, use_case, mock_repos):
        """Test handling of invalid page numbers (edge case)."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["session_repo"].get_paginated_with_filters.return_value = ([], 0)

        # Act - Zero and negative pages should be handled by repository
        sessions, total, total_pages = use_case.list_sessions_paginated(
            coach_id, page=0
        )

        # Assert - Use case passes through to repository
        assert mock_repos["session_repo"].get_paginated_with_filters.called

    def test_list_sessions_calculates_total_pages_correctly(self, use_case, mock_repos):
        """Test correct calculation of total pages."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_sessions = [Mock(spec=CoachingSession) for _ in range(5)]
        mock_repos["session_repo"].get_paginated_with_filters.return_value = (
            mock_sessions,
            25,  # 25 total sessions
        )

        # Act
        sessions, total, total_pages = use_case.list_sessions_paginated(
            coach_id, page_size=10
        )

        # Assert
        assert total == 25
        assert total_pages == 3  # ceil(25/10) = 3

    def test_list_sessions_with_all_filters(self, use_case, mock_repos):
        """Test list with all filter parameters."""
        # Arrange
        coach_id = uuid4()
        client_id = uuid4()
        from_date = date(2025, 1, 1)
        to_date = date(2025, 1, 31)
        currency = "TWD"

        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["session_repo"].get_paginated_with_filters.return_value = ([], 0)

        # Act
        use_case.list_sessions_paginated(
            coach_id,
            from_date=from_date,
            to_date=to_date,
            client_id=client_id,
            currency=currency,
            sort="-session_date",
            page=2,
            page_size=15,
        )

        # Assert
        mock_repos["session_repo"].get_paginated_with_filters.assert_called_once_with(
            coach_id, from_date, to_date, client_id, currency, "-session_date", 2, 15
        )


class TestCoachingSessionCreationErrorHandling:
    """Test error handling in CoachingSessionCreationUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "session_repo": Mock(),
            "user_repo": Mock(),
            "client_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return CoachingSessionCreationUseCase(
            session_repo=mock_repos["session_repo"],
            user_repo=mock_repos["user_repo"],
            client_repo=mock_repos["client_repo"],
        )

    @pytest.fixture
    def mock_coach(self):
        """Create mock coach user."""
        return User(
            id=uuid4(),
            email="coach@example.com",
            plan=UserPlan.PRO,
            created_at=datetime.now(UTC),
        )

    @pytest.fixture
    def mock_client(self, mock_coach):
        """Create mock client."""
        return Client(
            id=uuid4(),
            user_id=mock_coach.id,
            name="Test Client",
            email="client@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_create_session_raises_error_when_coach_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when coach doesn't exist."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_session(
                coach_id=coach_id,
                session_date=date(2025, 1, 15),
                client_id=uuid4(),
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=2000,
            )

        assert "Coach with ID" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_create_session_raises_error_when_client_not_found(
        self, use_case, mock_repos, mock_coach
    ):
        """Test that ValueError is raised when client doesn't exist."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_session(
                coach_id=mock_coach.id,
                session_date=date(2025, 1, 15),
                client_id=uuid4(),
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=2000,
            )

        assert "Client with ID" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_create_session_raises_error_when_client_belongs_to_different_coach(
        self, use_case, mock_repos, mock_coach
    ):
        """Test that ValueError is raised when client doesn't belong to coach."""
        # Arrange
        different_coach_id = uuid4()
        mock_client = Client(
            id=uuid4(),
            user_id=different_coach_id,  # Different coach
            name="Test Client",
            email="client@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_session(
                coach_id=mock_coach.id,
                session_date=date(2025, 1, 15),
                client_id=mock_client.id,
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=2000,
            )

        assert "does not belong to coach" in str(exc_info.value)

    def test_create_session_raises_error_on_negative_duration(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test that ValueError is raised for negative duration."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_session(
                coach_id=mock_coach.id,
                session_date=date(2025, 1, 15),
                client_id=mock_client.id,
                source=SessionSource.CLIENT,
                duration_min=-60,  # Negative duration
                fee_currency="TWD",
                fee_amount=2000,
            )

        assert "Invalid session data" in str(exc_info.value)

    def test_create_session_raises_error_on_negative_fee(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test that ValueError is raised for negative fee."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_session(
                coach_id=mock_coach.id,
                session_date=date(2025, 1, 15),
                client_id=mock_client.id,
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=-2000,  # Negative fee
            )

        assert "Invalid session data" in str(exc_info.value)

    def test_create_session_handles_database_error_on_save(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test handling of database errors when saving session."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client
        mock_repos["session_repo"].save.side_effect = IntegrityError(
            "Duplicate key", None, None
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            use_case.create_session(
                coach_id=mock_coach.id,
                session_date=date(2025, 1, 15),
                client_id=mock_client.id,
                source=SessionSource.CLIENT,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=2000,
            )

    def test_create_session_normalizes_currency_to_uppercase(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test that currency is normalized to uppercase."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client
        mock_saved_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].save.return_value = mock_saved_session

        # Act
        result = use_case.create_session(
            coach_id=mock_coach.id,
            session_date=date(2025, 1, 15),
            client_id=mock_client.id,
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="usd",  # lowercase
            fee_amount=50,
        )

        # Assert
        assert result == mock_saved_session
        # Verify the session passed to save has uppercase currency
        save_call_args = mock_repos["session_repo"].save.call_args[0][0]
        assert save_call_args.fee_currency == "USD"

    def test_create_session_with_zero_fee_is_allowed(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test that zero fee is allowed (pro bono sessions)."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client
        mock_saved_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].save.return_value = mock_saved_session

        # Act
        result = use_case.create_session(
            coach_id=mock_coach.id,
            session_date=date(2025, 1, 15),
            client_id=mock_client.id,
            source=SessionSource.FRIEND,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=0,  # Zero fee
        )

        # Assert
        assert result == mock_saved_session

    def test_create_session_with_optional_notes(
        self, use_case, mock_repos, mock_coach, mock_client
    ):
        """Test creating session with optional notes."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_by_id.return_value = mock_client
        mock_saved_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].save.return_value = mock_saved_session

        # Act
        result = use_case.create_session(
            coach_id=mock_coach.id,
            session_date=date(2025, 1, 15),
            client_id=mock_client.id,
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000,
            notes="Initial consultation session",
        )

        # Assert
        assert result == mock_saved_session
        save_call_args = mock_repos["session_repo"].save.call_args[0][0]
        assert save_call_args.notes == "Initial consultation session"


class TestCoachingSessionUpdateErrorHandling:
    """Test error handling in CoachingSessionUpdateUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "session_repo": Mock(),
            "user_repo": Mock(),
            "client_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return CoachingSessionUpdateUseCase(
            session_repo=mock_repos["session_repo"],
            user_repo=mock_repos["user_repo"],
            client_repo=mock_repos["client_repo"],
        )

    @pytest.fixture
    def mock_session(self):
        """Create mock coaching session."""
        return CoachingSession(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date(2025, 1, 15),
            source=SessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_update_session_raises_error_when_session_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when session doesn't exist."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_repos["session_repo"].get_with_ownership_check.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_session(session_id, coach_id, duration_min=90)

        assert "Coaching session not found" in str(exc_info.value)

    def test_update_session_raises_error_when_new_client_not_found(
        self, use_case, mock_repos, mock_session
    ):
        """Test that ValueError is raised when new client doesn't exist."""
        # Arrange
        new_client_id = uuid4()
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["client_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_session(
                mock_session.id, mock_session.user_id, client_id=new_client_id
            )

        assert f"Client with ID {new_client_id} not found" in str(exc_info.value)

    def test_update_session_raises_error_when_new_client_belongs_to_different_coach(
        self, use_case, mock_repos, mock_session
    ):
        """Test that ValueError is raised when new client doesn't belong to coach."""
        # Arrange
        new_client_id = uuid4()
        different_coach_id = uuid4()
        mock_client = Client(
            id=new_client_id,
            user_id=different_coach_id,
            name="Test Client",
            email="client@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["client_repo"].get_by_id.return_value = mock_client

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_session(
                mock_session.id, mock_session.user_id, client_id=new_client_id
            )

        assert "does not belong to coach" in str(exc_info.value)

    def test_update_session_raises_error_on_negative_duration(
        self, use_case, mock_repos, mock_session
    ):
        """Test that ValueError is raised for negative duration."""
        # Arrange
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_session(
                mock_session.id, mock_session.user_id, duration_min=-30
            )

        assert "Invalid session data" in str(exc_info.value)

    def test_update_session_raises_error_on_negative_fee(
        self, use_case, mock_repos, mock_session
    ):
        """Test that ValueError is raised for negative fee."""
        # Arrange
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_session(
                mock_session.id, mock_session.user_id, fee_amount=-1000
            )

        assert "Invalid session data" in str(exc_info.value)

    def test_update_session_handles_database_error(
        self, use_case, mock_repos, mock_session
    ):
        """Test handling of database errors when saving."""
        # Arrange
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["session_repo"].save.side_effect = OperationalError(
            "Database error", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.update_session(
                mock_session.id, mock_session.user_id, duration_min=90
            )

    def test_update_session_normalizes_currency_to_uppercase(
        self, use_case, mock_repos, mock_session
    ):
        """Test that currency is normalized to uppercase."""
        # Arrange
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_updated_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].save.return_value = mock_updated_session

        # Act
        result = use_case.update_session(
            mock_session.id, mock_session.user_id, fee_currency="usd"
        )

        # Assert
        assert result == mock_updated_session
        assert mock_session.fee_currency == "USD"

    def test_update_session_only_updates_provided_fields(
        self, use_case, mock_repos, mock_session
    ):
        """Test that only provided fields are updated."""
        # Arrange
        original_date = mock_session.session_date
        original_client_id = mock_session.client_id

        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_updated_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].save.return_value = mock_updated_session

        # Act
        use_case.update_session(
            mock_session.id,
            mock_session.user_id,
            duration_min=90,  # Only update duration
        )

        # Assert
        assert mock_session.duration_min == 90
        assert mock_session.session_date == original_date
        assert mock_session.client_id == original_client_id

    def test_update_session_updates_timestamp(self, use_case, mock_repos, mock_session):
        """Test that updated_at timestamp is refreshed."""
        # Arrange
        original_updated_at = mock_session.updated_at
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["session_repo"].save.return_value = Mock(spec=CoachingSession)

        # Act
        use_case.update_session(mock_session.id, mock_session.user_id, duration_min=90)

        # Assert
        assert mock_session.updated_at > original_updated_at

    def test_update_session_does_not_check_client_if_not_changing(
        self, use_case, mock_repos, mock_session
    ):
        """Test that client validation is skipped if client_id unchanged."""
        # Arrange
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["session_repo"].save.return_value = Mock(spec=CoachingSession)

        # Act
        use_case.update_session(
            mock_session.id,
            mock_session.user_id,
            client_id=mock_session.client_id,  # Same client
            duration_min=90,
        )

        # Assert - client_repo should not be called
        mock_repos["client_repo"].get_by_id.assert_not_called()


class TestCoachingSessionDeletionErrorHandling:
    """Test error handling in CoachingSessionDeletionUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "session_repo": Mock(),
            "user_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return CoachingSessionDeletionUseCase(
            session_repo=mock_repos["session_repo"],
            user_repo=mock_repos["user_repo"],
        )

    def test_delete_session_raises_error_when_session_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when session doesn't exist."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_repos["session_repo"].get_with_ownership_check.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.delete_session(session_id, coach_id)

        assert "Coaching session not found" in str(exc_info.value)

    def test_delete_session_handles_database_error_on_get(self, use_case, mock_repos):
        """Test handling of database errors when fetching session."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_repos[
            "session_repo"
        ].get_with_ownership_check.side_effect = OperationalError(
            "Database error", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.delete_session(session_id, coach_id)

    def test_delete_session_handles_database_error_on_delete(
        self, use_case, mock_repos
    ):
        """Test handling of database errors when deleting."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["session_repo"].delete.side_effect = OperationalError(
            "Delete failed", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.delete_session(session_id, coach_id)

    def test_delete_session_returns_true_on_success(self, use_case, mock_repos):
        """Test that delete returns True on success."""
        # Arrange
        session_id = uuid4()
        coach_id = uuid4()
        mock_session = Mock(spec=CoachingSession)
        mock_repos["session_repo"].get_with_ownership_check.return_value = mock_session
        mock_repos["session_repo"].delete.return_value = True

        # Act
        result = use_case.delete_session(session_id, coach_id)

        # Assert
        assert result is True
        mock_repos["session_repo"].delete.assert_called_once_with(session_id)


class TestCoachingSessionOptionsUseCase:
    """Test CoachingSessionOptionsUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create use case instance."""
        return CoachingSessionOptionsUseCase()

    def test_get_currency_options_returns_list(self, use_case):
        """Test that currency options returns a non-empty list."""
        # Act
        result = use_case.get_currency_options()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_currency_options_includes_twd(self, use_case):
        """Test that TWD is included in currency options."""
        # Act
        result = use_case.get_currency_options()

        # Assert
        twd_option = next((opt for opt in result if opt["value"] == "TWD"), None)
        assert twd_option is not None
        assert "Taiwan Dollar" in twd_option["label"]

    def test_get_currency_options_has_correct_structure(self, use_case):
        """Test that each option has value and label keys."""
        # Act
        result = use_case.get_currency_options()

        # Assert
        for option in result:
            assert "value" in option
            assert "label" in option
            assert isinstance(option["value"], str)
            assert isinstance(option["label"], str)
