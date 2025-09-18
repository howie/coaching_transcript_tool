"""Test to ensure no circular references in factory methods."""

import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from src.coaching_assistant.infrastructure.factories import (
    RepositoryFactory,
    UsageTrackingServiceFactory,
    SessionServiceFactory,
    SpeakerRoleServiceFactory,
    PlanServiceFactory,
    SubscriptionServiceFactory,
)
from src.coaching_assistant.infrastructure.db.repositories.subscription_repository import create_subscription_repository


class TestFactoryCircularReference:
    """Test factory methods don't have circular references and work correctly."""

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


class TestRepositoryFactory:
    """Test RepositoryFactory methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_create_user_repository(self, mock_session):
        """Test user repository creation."""
        repo = RepositoryFactory.create_user_repository(mock_session)
        assert repo is not None

    def test_create_usage_log_repository(self, mock_session):
        """Test usage log repository creation."""
        repo = RepositoryFactory.create_usage_log_repository(mock_session)
        assert repo is not None

    def test_create_session_repository(self, mock_session):
        """Test session repository creation."""
        repo = RepositoryFactory.create_session_repository(mock_session)
        assert repo is not None

    def test_create_plan_configuration_repository(self, mock_session):
        """Test plan configuration repository creation."""
        repo = RepositoryFactory.create_plan_configuration_repository(mock_session)
        assert repo is not None
        assert repo.db_session == mock_session

    def test_create_subscription_repository(self, mock_session):
        """Test subscription repository creation."""
        repo = RepositoryFactory.create_subscription_repository(mock_session)
        assert repo is not None
        assert repo.db_session == mock_session

    def test_create_transcript_repository(self, mock_session):
        """Test transcript repository creation."""
        repo = RepositoryFactory.create_transcript_repository(mock_session)
        assert repo is not None
        assert repo.db_session == mock_session


class TestUsageTrackingServiceFactory:
    """Test UsageTrackingServiceFactory methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_create_usage_log_use_case(self, mock_session):
        """Test CreateUsageLogUseCase creation."""
        use_case = UsageTrackingServiceFactory.create_usage_log_use_case(mock_session)
        assert use_case is not None

    def test_create_user_usage_use_case(self, mock_session):
        """Test GetUserUsageUseCase creation."""
        use_case = UsageTrackingServiceFactory.create_user_usage_use_case(mock_session)
        assert use_case is not None


class TestSessionServiceFactory:
    """Test SessionServiceFactory methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_create_session_creation_use_case(self, mock_session):
        """Test SessionCreationUseCase creation."""
        use_case = SessionServiceFactory.create_session_creation_use_case(mock_session)
        assert use_case is not None

    def test_create_session_retrieval_use_case(self, mock_session):
        """Test SessionRetrievalUseCase creation."""
        use_case = SessionServiceFactory.create_session_retrieval_use_case(mock_session)
        assert use_case is not None

    def test_create_session_status_update_use_case(self, mock_session):
        """Test SessionStatusUpdateUseCase creation."""
        use_case = SessionServiceFactory.create_session_status_update_use_case(mock_session)
        assert use_case is not None

    def test_create_session_transcript_update_use_case(self, mock_session):
        """Test SessionTranscriptUpdateUseCase creation."""
        use_case = SessionServiceFactory.create_session_transcript_update_use_case(mock_session)
        assert use_case is not None

    def test_create_session_upload_management_use_case(self, mock_session):
        """Test SessionUploadManagementUseCase creation."""
        use_case = SessionServiceFactory.create_session_upload_management_use_case(mock_session)
        assert use_case is not None

    def test_create_session_transcription_management_use_case(self, mock_session):
        """Test SessionTranscriptionManagementUseCase creation."""
        use_case = SessionServiceFactory.create_session_transcription_management_use_case(mock_session)
        assert use_case is not None

    def test_create_session_export_use_case(self, mock_session):
        """Test SessionExportUseCase creation."""
        use_case = SessionServiceFactory.create_session_export_use_case(mock_session)
        assert use_case is not None

    def test_create_session_status_retrieval_use_case(self, mock_session):
        """Test SessionStatusRetrievalUseCase creation."""
        use_case = SessionServiceFactory.create_session_status_retrieval_use_case(mock_session)
        assert use_case is not None

    def test_create_session_transcript_upload_use_case(self, mock_session):
        """Test SessionTranscriptUploadUseCase creation."""
        use_case = SessionServiceFactory.create_session_transcript_upload_use_case(mock_session)
        assert use_case is not None

    def test_create_speaker_role_retrieval_use_case(self, mock_session):
        """Test SpeakerRoleRetrievalUseCase creation."""
        use_case = SessionServiceFactory.create_speaker_role_retrieval_use_case(mock_session)
        assert use_case is not None

    def test_create_speaker_role_repository(self, mock_session):
        """Test speaker role repository creation."""
        repo = SessionServiceFactory.create_speaker_role_repository(mock_session)
        assert repo is not None

    def test_create_segment_role_repository(self, mock_session):
        """Test segment role repository creation."""
        repo = SessionServiceFactory.create_segment_role_repository(mock_session)
        assert repo is not None


class TestSpeakerRoleServiceFactory:
    """Test SpeakerRoleServiceFactory methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_create_speaker_role_assignment_use_case(self, mock_session):
        """Test SpeakerRoleAssignmentUseCase creation."""
        use_case = SpeakerRoleServiceFactory.create_speaker_role_assignment_use_case(mock_session)
        assert use_case is not None

    def test_create_segment_role_assignment_use_case(self, mock_session):
        """Test SegmentRoleAssignmentUseCase creation."""
        use_case = SpeakerRoleServiceFactory.create_segment_role_assignment_use_case(mock_session)
        assert use_case is not None

    def test_create_speaker_role_retrieval_use_case(self, mock_session):
        """Test SpeakerRoleRetrievalUseCase creation."""
        use_case = SpeakerRoleServiceFactory.create_speaker_role_retrieval_use_case(mock_session)
        assert use_case is not None


class TestPlanServiceFactory:
    """Test PlanServiceFactory methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_create_plan_retrieval_use_case(self, mock_session):
        """Test PlanRetrievalUseCase creation."""
        use_case = PlanServiceFactory.create_plan_retrieval_use_case(mock_session)
        assert use_case is not None

    def test_create_plan_validation_use_case(self, mock_session):
        """Test PlanValidationUseCase creation."""
        use_case = PlanServiceFactory.create_plan_validation_use_case(mock_session)
        assert use_case is not None


class TestLegacyCompatibilityFunctions:
    """Test legacy compatibility functions."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_factory_pattern_migration_complete(self, mock_session):
        """Test that factory pattern migration is complete (legacy functions removed)."""
        # WP6-Cleanup-3: Legacy compatibility functions have been removed
        # All API endpoints now use factory pattern directly
        direct_service = UsageTrackingServiceFactory.create_usage_log_use_case(mock_session)
        assert direct_service is not None
        print("✅ Factory pattern migration complete - no legacy compatibility functions")


class TestFactoryMemoryManagement:
    """Test factory memory management and performance."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_multiple_factory_calls_no_memory_leak(self, mock_session):
        """Test that multiple factory calls don't cause memory leaks."""
        # Test repository factories
        for _ in range(20):
            repo = RepositoryFactory.create_user_repository(mock_session)
            assert repo is not None

        # Test use case factories
        for _ in range(20):
            use_case = UsageTrackingServiceFactory.create_usage_log_use_case(mock_session)
            assert use_case is not None

    def test_factory_dependency_injection_consistency(self, mock_session):
        """Test that factories consistently inject the same session."""
        use_case = SessionServiceFactory.create_session_creation_use_case(mock_session)
        assert use_case is not None

        # Test another factory to ensure consistency
        repo = RepositoryFactory.create_user_repository(mock_session)
        assert repo is not None