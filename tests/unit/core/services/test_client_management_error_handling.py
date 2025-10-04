"""Error handling tests for client management use cases.

Tests focus on error paths, edge cases, and exception handling to improve
coverage from 20% toward 60%+.
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from coaching_assistant.core.models.client import Client
from coaching_assistant.core.models.user import User, UserPlan
from coaching_assistant.core.services.client_management_use_case import (
    ClientCreationUseCase,
    ClientDeletionUseCase,
    ClientOptionsUseCase,
    ClientRetrievalUseCase,
    ClientUpdateUseCase,
)


class TestClientRetrievalErrorHandling:
    """Test error handling in ClientRetrievalUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "client_repo": Mock(),
            "user_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return ClientRetrievalUseCase(
            client_repo=mock_repos["client_repo"],
            user_repo=mock_repos["user_repo"],
        )

    def test_get_client_by_id_returns_none_when_not_found(self, use_case, mock_repos):
        """Test that None is returned when client not found."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_repos["client_repo"].get_client_with_ownership_check.return_value = None

        # Act
        result = use_case.get_client_by_id(client_id, coach_id)

        # Assert
        assert result is None
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.assert_called_once_with(client_id, coach_id)

    def test_get_client_by_id_handles_database_error(self, use_case, mock_repos):
        """Test handling of database errors."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.side_effect = OperationalError(
            "Database connection failed", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.get_client_by_id(client_id, coach_id)

    def test_list_clients_raises_error_when_coach_not_found(self, use_case, mock_repos):
        """Test that ValueError is raised when coach doesn't exist."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.list_clients_paginated(coach_id)

        assert "Coach with ID" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_list_clients_handles_database_error_on_user_fetch(
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
            use_case.list_clients_paginated(coach_id)

    def test_list_clients_handles_database_error_on_client_fetch(
        self, use_case, mock_repos
    ):
        """Test handling of database errors when fetching clients."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_clients_paginated.side_effect = OperationalError(
            "Query timeout", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.list_clients_paginated(coach_id)

    def test_list_clients_handles_empty_results(self, use_case, mock_repos):
        """Test handling of no clients found."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_clients_paginated.return_value = ([], 0)

        # Act
        clients, total, total_pages = use_case.list_clients_paginated(coach_id)

        # Assert
        assert clients == []
        assert total == 0
        assert total_pages == 0

    def test_list_clients_calculates_total_pages_correctly(self, use_case, mock_repos):
        """Test correct calculation of total pages."""
        # Arrange
        coach_id = uuid4()
        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_clients = [Mock(spec=Client) for _ in range(5)]
        mock_repos["client_repo"].get_clients_paginated.return_value = (
            mock_clients,
            23,  # 23 total clients
        )

        # Act
        clients, total, total_pages = use_case.list_clients_paginated(
            coach_id, page_size=10
        )

        # Assert
        assert total == 23
        assert total_pages == 3  # ceil(23/10) = 3

    def test_list_clients_with_search_query(self, use_case, mock_repos):
        """Test list with search query parameter."""
        # Arrange
        coach_id = uuid4()
        search_query = "John"

        mock_coach = Mock(spec=User)
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].get_clients_paginated.return_value = ([], 0)

        # Act
        use_case.list_clients_paginated(
            coach_id, query=search_query, page=2, page_size=15
        )

        # Assert
        mock_repos["client_repo"].get_clients_paginated.assert_called_once_with(
            coach_id, search_query, 2, 15
        )

    def test_get_client_statistics_raises_error_when_coach_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when coach doesn't exist."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            use_case.get_client_statistics(coach_id)


class TestClientCreationErrorHandling:
    """Test error handling in ClientCreationUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "client_repo": Mock(),
            "user_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return ClientCreationUseCase(
            client_repo=mock_repos["client_repo"],
            user_repo=mock_repos["user_repo"],
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

    def test_create_client_raises_error_when_coach_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when coach doesn't exist."""
        # Arrange
        coach_id = uuid4()
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_client(coach_id=coach_id, name="John Doe")

        assert "Coach with ID" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_create_client_raises_error_when_email_already_exists(
        self, use_case, mock_repos, mock_coach
    ):
        """Test that ValueError is raised when email already exists."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].check_email_exists_for_coach.return_value = True

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.create_client(
                coach_id=mock_coach.id, name="John Doe", email="existing@example.com"
            )

        assert "email already exists" in str(exc_info.value)

    def test_create_client_handles_database_error_on_save(
        self, use_case, mock_repos, mock_coach
    ):
        """Test handling of database errors when saving client."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].check_email_exists_for_coach.return_value = False
        mock_repos["client_repo"].save.side_effect = IntegrityError(
            "Duplicate key", None, None
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            use_case.create_client(coach_id=mock_coach.id, name="John Doe")

    def test_create_client_with_only_required_fields(
        self, use_case, mock_repos, mock_coach
    ):
        """Test creating client with only name (required field)."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].check_email_exists_for_coach.return_value = False
        mock_saved_client = Mock(spec=Client)
        mock_repos["client_repo"].save.return_value = mock_saved_client

        # Act
        result = use_case.create_client(coach_id=mock_coach.id, name="John Doe")

        # Assert
        assert result == mock_saved_client
        save_call_args = mock_repos["client_repo"].save.call_args[0][0]
        assert save_call_args.name == "John Doe"
        assert save_call_args.user_id == mock_coach.id

    def test_create_client_with_all_fields(self, use_case, mock_repos, mock_coach):
        """Test creating client with all optional fields."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].check_email_exists_for_coach.return_value = False
        mock_saved_client = Mock(spec=Client)
        mock_repos["client_repo"].save.return_value = mock_saved_client

        # Act
        result = use_case.create_client(
            coach_id=mock_coach.id,
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            memo="Initial notes",
            source="referral",
            client_type="paid",
            issue_types="anxiety,stress",
            status="in_progress",
        )

        # Assert
        assert result == mock_saved_client
        save_call_args = mock_repos["client_repo"].save.call_args[0][0]
        assert save_call_args.name == "John Doe"
        assert save_call_args.email == "john@example.com"
        assert save_call_args.phone == "+1234567890"
        assert save_call_args.source == "referral"

    def test_create_client_without_email_skips_duplicate_check(
        self, use_case, mock_repos, mock_coach
    ):
        """Test that email duplicate check is skipped when no email provided."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = mock_coach
        mock_repos["client_repo"].save.return_value = Mock(spec=Client)

        # Act
        use_case.create_client(coach_id=mock_coach.id, name="John Doe")

        # Assert
        mock_repos["client_repo"].check_email_exists_for_coach.assert_not_called()


class TestClientUpdateErrorHandling:
    """Test error handling in ClientUpdateUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "client_repo": Mock(),
            "user_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return ClientUpdateUseCase(
            client_repo=mock_repos["client_repo"],
            user_repo=mock_repos["user_repo"],
        )

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        return Client(
            id=uuid4(),
            user_id=uuid4(),
            name="John Doe",
            email="john@example.com",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_update_client_raises_error_when_client_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when client doesn't exist."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_repos["client_repo"].get_client_with_ownership_check.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_client(client_id, coach_id, name="New Name")

        assert "Client not found" in str(exc_info.value)

    def test_update_client_raises_error_when_new_email_exists(
        self, use_case, mock_repos, mock_client
    ):
        """Test that ValueError is raised when new email already exists."""
        # Arrange
        new_email = "newemail@example.com"
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].check_email_exists_for_coach.return_value = True

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.update_client(mock_client.id, mock_client.user_id, email=new_email)

        assert "email already exists" in str(exc_info.value)

    def test_update_client_handles_database_error(
        self, use_case, mock_repos, mock_client
    ):
        """Test handling of database errors when saving."""
        # Arrange
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].save.side_effect = OperationalError(
            "Database error", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.update_client(mock_client.id, mock_client.user_id, name="New Name")

    def test_update_client_only_updates_provided_fields(
        self, use_case, mock_repos, mock_client
    ):
        """Test that only provided fields are updated."""
        # Arrange
        original_email = mock_client.email
        original_phone = mock_client.phone

        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_updated_client = Mock(spec=Client)
        mock_repos["client_repo"].save.return_value = mock_updated_client

        # Act
        use_case.update_client(
            mock_client.id,
            mock_client.user_id,
            name="New Name",  # Only update name
        )

        # Assert
        assert mock_client.name == "New Name"
        assert mock_client.email == original_email
        assert mock_client.phone == original_phone

    def test_update_client_updates_timestamp(self, use_case, mock_repos, mock_client):
        """Test that updated_at timestamp is refreshed."""
        # Arrange
        original_updated_at = mock_client.updated_at
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].save.return_value = Mock(spec=Client)

        # Act
        use_case.update_client(mock_client.id, mock_client.user_id, name="New Name")

        # Assert
        assert mock_client.updated_at > original_updated_at

    def test_update_client_does_not_check_email_if_unchanged(
        self, use_case, mock_repos, mock_client
    ):
        """Test that email duplicate check is skipped if email unchanged."""
        # Arrange
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].save.return_value = Mock(spec=Client)

        # Act
        use_case.update_client(
            mock_client.id,
            mock_client.user_id,
            email=mock_client.email,  # Same email
            name="New Name",
        )

        # Assert
        mock_repos["client_repo"].check_email_exists_for_coach.assert_not_called()


class TestClientDeletionErrorHandling:
    """Test error handling in ClientDeletionUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {
            "client_repo": Mock(),
            "user_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return ClientDeletionUseCase(
            client_repo=mock_repos["client_repo"],
            user_repo=mock_repos["user_repo"],
        )

    def test_delete_client_raises_error_when_client_not_found(
        self, use_case, mock_repos
    ):
        """Test that ValueError is raised when client doesn't exist."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_repos["client_repo"].get_client_with_ownership_check.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.delete_client(client_id, coach_id)

        assert "Client not found" in str(exc_info.value)

    def test_delete_client_handles_database_error_on_get(self, use_case, mock_repos):
        """Test handling of database errors when fetching client."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.side_effect = OperationalError(
            "Database error", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.delete_client(client_id, coach_id)

    def test_delete_client_handles_database_error_on_delete(self, use_case, mock_repos):
        """Test handling of database errors when deleting."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_client = Mock(spec=Client)
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].delete.side_effect = OperationalError(
            "Delete failed", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.delete_client(client_id, coach_id)

    def test_delete_client_returns_true_on_success(self, use_case, mock_repos):
        """Test that delete returns True on success."""
        # Arrange
        client_id = uuid4()
        coach_id = uuid4()
        mock_client = Mock(spec=Client)
        mock_repos[
            "client_repo"
        ].get_client_with_ownership_check.return_value = mock_client
        mock_repos["client_repo"].delete.return_value = True

        # Act
        result = use_case.delete_client(client_id, coach_id)

        # Assert
        assert result is True
        mock_repos["client_repo"].delete.assert_called_once_with(client_id)


class TestClientOptionsUseCase:
    """Test ClientOptionsUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create use case instance."""
        return ClientOptionsUseCase()

    def test_get_source_options_returns_list(self, use_case):
        """Test that source options returns a non-empty list."""
        # Act
        result = use_case.get_source_options()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_source_options_has_correct_structure(self, use_case):
        """Test that each option has value and labelKey keys."""
        # Act
        result = use_case.get_source_options()

        # Assert
        for option in result:
            assert "value" in option
            assert "labelKey" in option

    def test_get_type_options_returns_list(self, use_case):
        """Test that client type options returns a non-empty list."""
        # Act
        result = use_case.get_type_options()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_status_options_returns_list(self, use_case):
        """Test that status options returns a non-empty list."""
        # Act
        result = use_case.get_status_options()

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
