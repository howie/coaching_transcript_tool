"""Test to ensure no circular references in factory methods."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from src.coaching_assistant.infrastructure.factories import SubscriptionServiceFactory
from src.coaching_assistant.infrastructure.db.repositories.subscription_repository import create_subscription_repository


class TestFactoryCircularReference:
    """Test factory methods don't have circular references."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_subscription_repository_creation_no_recursion(self, mock_session):
        """Ensure subscription repository creation doesn't recurse."""
        # This should not cause recursion error
        repo = create_subscription_repository(mock_session)

        # Verify it returns a SubscriptionRepository instance
        assert repo is not None
        assert hasattr(repo, 'get_subscription_by_user_id')
        assert hasattr(repo, 'save_subscription')
        assert hasattr(repo, 'save_credit_authorization')
        assert hasattr(repo, 'save_payment')
        assert hasattr(repo, 'update_subscription_status')

        # Verify it has the correct session
        assert repo.db_session == mock_session

    def test_subscription_retrieval_use_case_creation(self, mock_session):
        """Test that use case can be created without errors."""
        # This should work without recursion
        use_case = SubscriptionServiceFactory.create_subscription_retrieval_use_case(mock_session)

        assert use_case is not None
        assert hasattr(use_case, 'get_current_subscription')

    def test_subscription_creation_use_case_creation(self, mock_session):
        """Test that subscription creation use case can be created."""
        use_case = SubscriptionServiceFactory.create_subscription_creation_use_case(mock_session)

        assert use_case is not None

    def test_subscription_modification_use_case_creation(self, mock_session):
        """Test that subscription modification use case can be created."""
        use_case = SubscriptionServiceFactory.create_subscription_modification_use_case(mock_session)

        assert use_case is not None

    def test_multiple_repository_creation_no_memory_leak(self, mock_session):
        """Test creating multiple repositories doesn't cause memory issues."""
        # Create multiple instances to ensure no recursion stack buildup
        for i in range(10):
            repo = create_subscription_repository(mock_session)
            assert repo is not None
            assert repo.db_session == mock_session

    def test_repository_has_correct_transaction_management(self, mock_session):
        """Test that the repository uses flush() not commit()."""
        repo = create_subscription_repository(mock_session)

        # Create a mock subscription object
        mock_subscription = Mock()

        # Call save_subscription and verify it uses flush
        result = repo.save_subscription(mock_subscription)

        # Verify the session methods were called correctly
        mock_session.add.assert_called_once_with(mock_subscription)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()

        assert result == mock_subscription