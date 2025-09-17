"""Unit tests for session management use cases.

This module contains comprehensive unit tests for all session management use cases,
following Clean Architecture principles with proper mocking of dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

# Import use cases to test
from src.coaching_assistant.core.services.session_management_use_case import (
    SessionCreationUseCase,
    SessionRetrievalUseCase,
    SessionStatusUpdateUseCase,
    SessionTranscriptUpdateUseCase,
    SessionUploadManagementUseCase,
    SessionTranscriptionManagementUseCase,
    SessionExportUseCase,
    SessionStatusRetrievalUseCase,
    SessionTranscriptUploadUseCase,
)

# Import domain models
from src.coaching_assistant.core.models.session import Session, SessionStatus
from src.coaching_assistant.core.models.user import User, UserPlan
from src.coaching_assistant.core.models.usage_log import UsageLog, TranscriptionType
from src.coaching_assistant.core.models.transcript import TranscriptSegment
from src.coaching_assistant.core.models.plan_configuration import (
    PlanConfiguration, PlanLimits, PlanFeatures, PlanPricing
)

# Import exceptions
from src.coaching_assistant.exceptions import DomainException


@pytest.fixture
def mock_session_repo():
    """Create a mock session repository."""
    return Mock()


@pytest.fixture
def mock_user_repo():
    """Create a mock user repository."""
    return Mock()


@pytest.fixture
def mock_usage_log_repo():
    """Create a mock usage log repository."""
    return Mock()


@pytest.fixture
def mock_transcript_repo():
    """Create a mock transcript repository."""
    return Mock()


@pytest.fixture
def mock_plan_config_repo():
    """Create a mock plan configuration repository."""
    return Mock()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        plan=UserPlan.FREE,
        current_month_start=datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_session(sample_user):
    """Create a sample session for testing."""
    return Session(
        id=uuid4(),
        user_id=sample_user.id,
        title="Test Session",
        language="cmn-Hant-TW",
        status=SessionStatus.UPLOADING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_plan_config():
    """Create a sample plan configuration for testing."""
    return PlanConfiguration(
        id=uuid4(),
        plan_type=UserPlan.FREE,
        plan_name="Free Plan",
        display_name="Free Plan",
        limits=PlanLimits(
            max_sessions=5,
            max_total_minutes=60,
            max_file_size_mb=60,
        ),
        features=PlanFeatures(),
        pricing=PlanPricing(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestSessionCreationUseCase:
    """Test cases for SessionCreationUseCase."""

    def test_execute_creates_session_successfully(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_plan_config
    ):
        """Test successful session creation."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.count_user_sessions.return_value = 0
        mock_session_repo.get_total_duration_minutes.return_value = 0

        expected_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = expected_session

        # Act
        result = use_case.execute(
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            stt_provider="auto",
        )

        # Assert
        assert result == expected_session
        mock_user_repo.get_by_id.assert_called_once_with(sample_user.id)
        mock_plan_config_repo.get_by_plan_type.assert_called_once_with(sample_user.plan)
        mock_session_repo.save.assert_called_once()

    def test_execute_raises_error_for_invalid_user(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo
    ):
        """Test session creation fails for invalid user."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = None
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            use_case.execute(
                user_id=user_id,
                title="Test Session",
                language="cmn-Hant-TW",
            )

    def test_execute_raises_error_for_session_limit_exceeded(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_plan_config
    ):
        """Test session creation fails when session limit exceeded."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.count_user_sessions.return_value = 10  # Exceeds limit of 5

        # Act & Assert
        with pytest.raises(DomainException, match="Session limit exceeded"):
            use_case.execute(
                user_id=sample_user.id,
                title="Test Session",
                language="cmn-Hant-TW",
            )

        # Verify billing period is used for session count
        mock_session_repo.count_user_sessions.assert_called_with(
            sample_user.id, since=sample_user.current_month_start
        )

    def test_execute_raises_error_for_minutes_limit_exceeded(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_plan_config
    ):
        """Test session creation fails when minutes limit exceeded."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.count_user_sessions.return_value = 2  # Within session limit
        mock_session_repo.get_total_duration_minutes.return_value = 120  # Exceeds 60 minute limit

        # Act & Assert
        with pytest.raises(DomainException, match="Total minutes limit exceeded"):
            use_case.execute(
                user_id=sample_user.id,
                title="Test Session",
                language="cmn-Hant-TW",
            )

        # Verify billing period is used for both session count and duration
        mock_session_repo.count_user_sessions.assert_called_with(
            sample_user.id, since=sample_user.current_month_start
        )
        mock_session_repo.get_total_duration_minutes.assert_called_with(
            sample_user.id, since=sample_user.current_month_start
        )

    def test_execute_with_none_limits_object(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user
    ):
        """Test session creation with None limits object - should allow creation."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user

        # Create plan config with None limits
        plan_config_with_none_limits = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.FREE,
            plan_name="Free Plan",
            display_name="Free Plan",
            limits=None,  # Test None case
            features=PlanFeatures(),
            pricing=PlanPricing(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_plan_config_repo.get_by_plan_type.return_value = plan_config_with_none_limits

        expected_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = expected_session

        # Act - should not raise any errors with None limits
        result = use_case.execute(
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
        )

        # Assert
        assert result == expected_session
        mock_session_repo.save.assert_called_once()

    def test_execute_with_zero_limits_allows_creation(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user
    ):
        """Test session creation with zero limits (unlimited) - should allow creation."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user

        # Create plan config with zero limits (meaning unlimited)
        unlimited_plan_config = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.PRO,
            plan_name="Pro Plan",
            display_name="Pro Plan",
            limits=PlanLimits(
                max_sessions=0,  # 0 means unlimited
                max_total_minutes=0,  # 0 means unlimited
                max_file_size_mb=100,
            ),
            features=PlanFeatures(),
            pricing=PlanPricing(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_plan_config_repo.get_by_plan_type.return_value = unlimited_plan_config
        mock_session_repo.count_user_sessions.return_value = 100  # High usage
        mock_session_repo.get_total_duration_minutes.return_value = 1000  # High usage

        expected_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = expected_session

        # Act - should not raise any errors with zero limits
        result = use_case.execute(
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
        )

        # Assert
        assert result == expected_session
        mock_session_repo.save.assert_called_once()

    def test_execute_with_negative_one_limits_allows_creation(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user
    ):
        """Test session creation with -1 limits (unlimited) - should allow creation."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user

        # Create plan config with -1 limits (meaning unlimited)
        unlimited_plan_config = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.ENTERPRISE,
            plan_name="Enterprise Plan",
            display_name="Enterprise Plan",
            limits=PlanLimits(
                max_sessions=-1,  # -1 means unlimited
                max_total_minutes=-1,  # -1 means unlimited
                max_file_size_mb=1000,
            ),
            features=PlanFeatures(),
            pricing=PlanPricing(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_plan_config_repo.get_by_plan_type.return_value = unlimited_plan_config
        mock_session_repo.count_user_sessions.return_value = 500  # Very high usage
        mock_session_repo.get_total_duration_minutes.return_value = 5000  # Very high usage

        expected_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = expected_session

        # Act - should not raise any errors with -1 limits
        result = use_case.execute(
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
        )

        # Assert
        assert result == expected_session
        mock_session_repo.save.assert_called_once()


class TestSessionCreationUseCasePlanLimitsDataclassAccess:
    """Specific tests for PlanLimits dataclass attribute access to prevent regression."""

    def test_plan_limits_dataclass_attribute_access(self):
        """Test that PlanLimits dataclass attributes are accessed correctly."""
        # This test specifically guards against the AttributeError: 'PlanLimits' object has no attribute 'get'
        limits = PlanLimits(
            max_sessions=10,
            max_total_minutes=120,
            max_file_size_mb=100,
        )

        # Test direct attribute access (correct way)
        assert limits.max_sessions == 10
        assert limits.max_total_minutes == 120
        assert limits.max_file_size_mb == 100

        # Test the pattern used in the use case
        max_sessions = limits.max_sessions if limits else -1
        max_minutes = limits.max_total_minutes if limits else -1

        assert max_sessions == 10
        assert max_minutes == 120

    def test_plan_limits_none_handling(self):
        """Test handling of None limits object."""
        limits = None

        # Test the pattern used in the use case with None
        max_sessions = limits.max_sessions if limits else -1
        max_minutes = limits.max_total_minutes if limits else -1

        assert max_sessions == -1
        assert max_minutes == -1

    def test_billing_period_filtering_with_historical_usage(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_plan_config
    ):
        """Test that historical usage outside billing period doesn't count towards limits."""
        # Arrange
        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        # Simulate current billing period usage is within limits
        mock_session_repo.count_user_sessions.return_value = 2  # Within 5 session limit
        mock_session_repo.get_total_duration_minutes.return_value = 30  # Within 60 minute limit

        # Mock successful session creation
        created_session = Session(
            id=uuid4(),
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = created_session

        # Act
        result = use_case.execute(
            user_id=sample_user.id,
            title="Test Session",
            language="cmn-Hant-TW",
        )

        # Assert - session should be created successfully
        assert result.id == created_session.id

        # Verify billing period was used in both limit checks
        mock_session_repo.count_user_sessions.assert_called_with(
            sample_user.id, since=sample_user.current_month_start
        )
        mock_session_repo.get_total_duration_minutes.assert_called_with(
            sample_user.id, since=sample_user.current_month_start
        )

    def test_billing_period_none_handling(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_plan_config
    ):
        """Test that None billing period still allows session creation with proper parameter passing."""
        # Arrange
        user_with_no_billing_period = User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            plan=UserPlan.FREE,
            current_month_start=None,  # No billing period set
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        use_case = SessionCreationUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = user_with_no_billing_period
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        # Simulate usage within limits
        mock_session_repo.count_user_sessions.return_value = 2
        mock_session_repo.get_total_duration_minutes.return_value = 30

        # Mock successful session creation
        created_session = Session(
            id=uuid4(),
            user_id=user_with_no_billing_period.id,
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_session_repo.save.return_value = created_session

        # Act
        result = use_case.execute(
            user_id=user_with_no_billing_period.id,
            title="Test Session",
            language="cmn-Hant-TW",
        )

        # Assert - session should be created successfully
        assert result.id == created_session.id

        # Verify None was passed as the since parameter
        mock_session_repo.count_user_sessions.assert_called_with(
            user_with_no_billing_period.id, since=None
        )
        mock_session_repo.get_total_duration_minutes.assert_called_with(
            user_with_no_billing_period.id, since=None
        )

    def test_upload_url_generation_with_plan_limits_dataclass(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_session, sample_plan_config
    ):
        """Test upload URL generation with PlanLimits dataclass (not dictionary)."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.get_by_id.return_value = sample_session

        # Mock successful URL generation
        mock_session_repo.save.return_value = sample_session

        # Act - file size within limits
        result = use_case.generate_upload_url(
            session_id=sample_session.id,
            user_id=sample_user.id,
            filename="test.mp3",
            file_size_mb=50.0  # Within 60MB limit
        )

        # Assert - should succeed
        assert result is not None
        # Verify plan config was retrieved and limits checked
        mock_plan_config_repo.get_by_plan_type.assert_called_with(sample_user.plan)

    def test_upload_url_generation_exceeds_file_size_limit(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_session, sample_plan_config
    ):
        """Test upload URL generation fails when file size exceeds plan limits."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert - file size exceeds limits
        with pytest.raises(DomainException, match="File size.*exceeds plan limit"):
            use_case.generate_upload_url(
                session_id=sample_session.id,
                user_id=sample_user.id,
                filename="large_file.mp4",
                file_size_mb=100.0  # Exceeds 60MB limit
            )

    def test_upload_url_generation_with_none_plan_limits(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_user, sample_session
    ):
        """Test upload URL generation with None plan limits (no validation)."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user

        # Mock plan config with None limits
        plan_config_no_limits = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.FREE,
            plan_name="Free Plan",
            display_name="Free Plan",
            limits=None,  # No limits object
            features=PlanFeatures(),
            pricing=PlanPricing(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_plan_config_repo.get_by_plan_type.return_value = plan_config_no_limits
        mock_session_repo.get_by_id.return_value = sample_session
        mock_session_repo.save.return_value = sample_session

        # Act - should not raise exception when no limits
        result = use_case.generate_upload_url(
            session_id=sample_session.id,
            user_id=sample_user.id,
            filename="any_size.mp4",
            file_size_mb=1000.0  # Large file but no limits to check
        )

        # Assert - should succeed
        assert result is not None

    def test_plan_configuration_with_plan_limits_dataclass(self):
        """Test that PlanConfiguration correctly uses PlanLimits dataclass."""
        plan_config = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.STUDENT,
            plan_name="Student Plan",
            display_name="Student Plan",
            limits=PlanLimits(
                max_sessions=15,
                max_total_minutes=300,
                max_file_size_mb=150,
            ),
            features=PlanFeatures(priority_support=True),
            pricing=PlanPricing(monthly_price_cents=999),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Test that limits is a PlanLimits object, not a dict
        assert isinstance(plan_config.limits, PlanLimits)
        assert not hasattr(plan_config.limits, 'get')  # Should NOT have dict methods

        # Test correct attribute access
        assert plan_config.limits.max_sessions == 15
        assert plan_config.limits.max_total_minutes == 300
        assert plan_config.limits.max_file_size_mb == 150


class TestSessionRetrievalUseCase:
    """Test cases for SessionRetrievalUseCase."""

    def test_get_session_by_id_returns_session_for_owner(
        self, mock_session_repo, mock_user_repo, mock_transcript_repo, sample_session
    ):
        """Test getting session by ID for session owner."""
        # Arrange
        use_case = SessionRetrievalUseCase(mock_session_repo, mock_user_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session

        # Act
        result = use_case.get_session_by_id(sample_session.id, sample_session.user_id)

        # Assert
        assert result == sample_session
        mock_session_repo.get_by_id.assert_called_once_with(sample_session.id)

    def test_get_session_by_id_returns_none_for_non_owner(
        self, mock_session_repo, mock_user_repo, mock_transcript_repo, sample_session
    ):
        """Test getting session by ID returns None for non-owner."""
        # Arrange
        use_case = SessionRetrievalUseCase(mock_session_repo, mock_user_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session
        different_user_id = uuid4()

        # Act
        result = use_case.get_session_by_id(sample_session.id, different_user_id)

        # Assert
        assert result is None

    def test_get_user_sessions_returns_filtered_sessions(
        self, mock_session_repo, mock_user_repo, mock_transcript_repo, sample_session
    ):
        """Test getting user sessions with filtering."""
        # Arrange
        use_case = SessionRetrievalUseCase(mock_session_repo, mock_user_repo, mock_transcript_repo)
        expected_sessions = [sample_session]
        mock_session_repo.get_by_user_id.return_value = expected_sessions

        # Act
        result = use_case.get_user_sessions(
            user_id=sample_session.user_id,
            status=SessionStatus.UPLOADING,
            limit=10,
            offset=0,
        )

        # Assert
        assert result == expected_sessions
        mock_session_repo.get_by_user_id.assert_called_once_with(
            sample_session.user_id, SessionStatus.UPLOADING, 10, 0
        )

    def test_get_session_with_transcript_returns_complete_data(
        self, mock_session_repo, mock_user_repo, mock_transcript_repo, sample_session
    ):
        """Test getting session with transcript segments."""
        # Arrange
        use_case = SessionRetrievalUseCase(mock_session_repo, mock_user_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session

        transcript_segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=sample_session.id,
                speaker_id=1,
                start_seconds=0.0,
                end_seconds=5.0,
                content="Test transcript content",
                confidence=0.95,
            )
        ]
        mock_transcript_repo.get_by_session_id.return_value = transcript_segments

        # Act
        result = use_case.get_session_with_transcript(sample_session.id, sample_session.user_id)

        # Assert
        assert result is not None
        assert result["session"] == sample_session
        assert result["transcript_segments"] == transcript_segments
        assert result["segments_count"] == 1


class TestSessionStatusUpdateUseCase:
    """Test cases for SessionStatusUpdateUseCase."""

    def test_update_session_status_successful_transition(
        self, mock_session_repo, mock_user_repo, mock_usage_log_repo, sample_session
    ):
        """Test successful session status update."""
        # Arrange
        use_case = SessionStatusUpdateUseCase(mock_session_repo, mock_user_repo, mock_usage_log_repo)
        mock_session_repo.get_by_id.return_value = sample_session
        updated_session = Session(
            **{**sample_session.__dict__, "status": SessionStatus.PENDING}
        )
        mock_session_repo.update_status.return_value = updated_session

        # Act
        result = use_case.update_session_status(
            sample_session.id, SessionStatus.PENDING, sample_session.user_id
        )

        # Assert
        assert result.status == SessionStatus.PENDING
        mock_session_repo.update_status.assert_called_once_with(sample_session.id, SessionStatus.PENDING)

    def test_update_session_status_invalid_transition(
        self, mock_session_repo, mock_user_repo, mock_usage_log_repo, sample_session
    ):
        """Test session status update with invalid transition."""
        # Arrange
        use_case = SessionStatusUpdateUseCase(mock_session_repo, mock_user_repo, mock_usage_log_repo)
        sample_session.status = SessionStatus.COMPLETED  # Cannot go to UPLOADING from COMPLETED
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="Invalid status transition"):
            use_case.update_session_status(
                sample_session.id, SessionStatus.UPLOADING, sample_session.user_id
            )

    def test_update_session_status_creates_usage_log_on_completion(
        self, mock_session_repo, mock_user_repo, mock_usage_log_repo, sample_session
    ):
        """Test usage log creation when session completes."""
        # Arrange
        use_case = SessionStatusUpdateUseCase(mock_session_repo, mock_user_repo, mock_usage_log_repo)
        sample_session.duration_seconds = 300  # 5 minutes
        mock_session_repo.get_by_id.return_value = sample_session

        completed_session = Session(
            **{**sample_session.__dict__, "status": SessionStatus.COMPLETED}
        )
        mock_session_repo.update_status.return_value = completed_session

        # Act
        result = use_case.update_session_status(
            sample_session.id, SessionStatus.COMPLETED, sample_session.user_id
        )

        # Assert
        assert result.status == SessionStatus.COMPLETED
        mock_usage_log_repo.save.assert_called_once()
        # Verify the usage log was created with correct values
        usage_log_call = mock_usage_log_repo.save.call_args[0][0]
        assert usage_log_call.user_id == sample_session.user_id
        assert usage_log_call.session_id == sample_session.id
        assert usage_log_call.duration_minutes == 5  # 300 seconds / 60


class TestSessionUploadManagementUseCase:
    """Test cases for SessionUploadManagementUseCase."""

    def test_generate_upload_url_successful(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_session, sample_user, sample_plan_config
    ):
        """Test successful upload URL generation."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        mock_session_repo.get_by_id.return_value = sample_session

        # Act
        result = use_case.generate_upload_url(
            session_id=sample_session.id,
            user_id=sample_user.id,
            filename="test.mp3",
            file_size_mb=30.0,  # Within limit
        )

        # Assert
        assert result["session"] == sample_session
        assert result["filename"] == "test.mp3"
        assert result["file_size_mb"] == 30.0
        assert result["user_plan"] == sample_user.plan

    def test_generate_upload_url_file_size_exceeds_limit(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_session, sample_user, sample_plan_config
    ):
        """Test upload URL generation fails when file size exceeds plan limit."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        # Act & Assert
        with pytest.raises(DomainException, match="File size.*exceeds plan limit"):
            use_case.generate_upload_url(
                session_id=sample_session.id,
                user_id=sample_user.id,
                filename="test.mp3",
                file_size_mb=100.0,  # Exceeds 60MB limit
            )

    def test_generate_upload_url_invalid_session_status(
        self, mock_session_repo, mock_user_repo, mock_plan_config_repo, sample_session, sample_user, sample_plan_config
    ):
        """Test upload URL generation fails for invalid session status."""
        # Arrange
        use_case = SessionUploadManagementUseCase(mock_session_repo, mock_user_repo, mock_plan_config_repo)
        mock_user_repo.get_by_id.return_value = sample_user
        mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        # Set session status to COMPLETED (invalid for upload)
        sample_session.status = SessionStatus.COMPLETED
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="Cannot upload to session"):
            use_case.generate_upload_url(
                session_id=sample_session.id,
                user_id=sample_user.id,
                filename="test.mp3",
                file_size_mb=30.0,
            )


class TestSessionTranscriptionManagementUseCase:
    """Test cases for SessionTranscriptionManagementUseCase."""

    def test_start_transcription_successful(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test successful transcription start."""
        # Arrange
        use_case = SessionTranscriptionManagementUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.PENDING
        sample_session.gcs_audio_path = "gs://bucket/audio.mp3"
        mock_session_repo.get_by_id.return_value = sample_session

        processing_session = Session(
            **{**sample_session.__dict__, "status": SessionStatus.PROCESSING}
        )
        mock_session_repo.save.return_value = processing_session

        # Act
        result = use_case.start_transcription(sample_session.id, sample_session.user_id)

        # Assert
        assert result["session_id"] == str(sample_session.id)
        assert result["gcs_uri"] == sample_session.gcs_audio_path
        assert result["language"] == sample_session.language
        mock_session_repo.save.assert_called_once()

    def test_start_transcription_invalid_status(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test transcription start fails for invalid session status."""
        # Arrange
        use_case = SessionTranscriptionManagementUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.COMPLETED  # Invalid for starting transcription
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="Cannot start transcription"):
            use_case.start_transcription(sample_session.id, sample_session.user_id)

    def test_start_transcription_no_audio_file(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test transcription start fails when no audio file uploaded."""
        # Arrange
        use_case = SessionTranscriptionManagementUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.PENDING
        sample_session.gcs_audio_path = None  # No audio file
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="No audio file uploaded"):
            use_case.start_transcription(sample_session.id, sample_session.user_id)


class TestSessionStatusRetrievalUseCase:
    """Test cases for SessionStatusRetrievalUseCase."""

    def test_get_detailed_status_for_uploading_session(
        self, mock_session_repo, sample_session
    ):
        """Test detailed status retrieval for uploading session."""
        # Arrange
        use_case = SessionStatusRetrievalUseCase(mock_session_repo)
        sample_session.status = SessionStatus.UPLOADING
        mock_session_repo.get_by_id.return_value = sample_session

        # Act
        result = use_case.get_detailed_status(sample_session.id, sample_session.user_id)

        # Assert
        assert result["session"] == sample_session
        processing_status = result["processing_status"]
        assert processing_status["progress_percentage"] == 0
        assert processing_status["message"] == "Waiting for file upload"
        assert processing_status["started_at"] is None

    def test_get_detailed_status_for_processing_session(
        self, mock_session_repo, sample_session
    ):
        """Test detailed status retrieval for processing session."""
        # Arrange
        use_case = SessionStatusRetrievalUseCase(mock_session_repo)
        sample_session.status = SessionStatus.PROCESSING
        sample_session.duration_seconds = 600  # 10 minutes
        sample_session.transcription_started_at = datetime.utcnow() - timedelta(minutes=1)
        mock_session_repo.get_by_id.return_value = sample_session

        # Act
        result = use_case.get_detailed_status(sample_session.id, sample_session.user_id)

        # Assert
        assert result["session"] == sample_session
        processing_status = result["processing_status"]
        assert processing_status["progress_percentage"] > 0  # Should have some progress
        assert "processing" in processing_status["message"].lower()
        assert processing_status["started_at"] == sample_session.transcription_started_at

    def test_get_detailed_status_for_completed_session(
        self, mock_session_repo, sample_session
    ):
        """Test detailed status retrieval for completed session."""
        # Arrange
        use_case = SessionStatusRetrievalUseCase(mock_session_repo)
        sample_session.status = SessionStatus.COMPLETED
        sample_session.duration_seconds = 300
        mock_session_repo.get_by_id.return_value = sample_session

        # Act
        result = use_case.get_detailed_status(sample_session.id, sample_session.user_id)

        # Assert
        assert result["session"] == sample_session
        processing_status = result["processing_status"]
        assert processing_status["progress_percentage"] == 100
        assert processing_status["message"] == "Transcription complete!"
        assert processing_status["duration_processed"] == sample_session.duration_seconds


class TestSessionExportUseCase:
    """Test cases for SessionExportUseCase."""

    def test_export_transcript_successful(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test successful transcript export."""
        # Arrange
        use_case = SessionExportUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.COMPLETED
        mock_session_repo.get_by_id.return_value = sample_session

        transcript_segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=sample_session.id,
                speaker_id=1,
                start_seconds=0.0,
                end_seconds=5.0,
                content="Test content",
                confidence=0.95,
            )
        ]
        mock_transcript_repo.get_by_session_id.return_value = transcript_segments

        # Act
        result = use_case.export_transcript(
            sample_session.id, sample_session.user_id, "json"
        )

        # Assert
        assert result["session"] == sample_session
        assert result["segments"] == transcript_segments
        assert result["format"] == "json"

    def test_export_transcript_session_not_completed(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test transcript export fails for non-completed session."""
        # Arrange
        use_case = SessionExportUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.PROCESSING  # Not completed
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="Transcript not available"):
            use_case.export_transcript(
                sample_session.id, sample_session.user_id, "json"
            )

    def test_export_transcript_invalid_format(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test transcript export fails for invalid format."""
        # Arrange
        use_case = SessionExportUseCase(mock_session_repo, mock_transcript_repo)
        sample_session.status = SessionStatus.COMPLETED
        mock_session_repo.get_by_id.return_value = sample_session
        mock_transcript_repo.get_by_session_id.return_value = []

        # Act & Assert
        with pytest.raises(DomainException, match="Invalid format"):
            use_case.export_transcript(
                sample_session.id, sample_session.user_id, "invalid_format"
            )


class TestSessionTranscriptUploadUseCase:
    """Test cases for SessionTranscriptUploadUseCase."""

    def test_upload_transcript_file_vtt_successful(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test successful VTT transcript file upload."""
        # Arrange
        use_case = SessionTranscriptUploadUseCase(mock_session_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session

        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v Speaker 1>Test transcript content
"""

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.vtt", vtt_content
        )

        # Assert
        assert result["session"] == sample_session
        assert len(result["segments_data"]) == 1
        assert result["file_extension"] == "vtt"
        assert result["segments_data"][0]["content"] == "Test transcript content"

    def test_upload_transcript_file_invalid_format(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test transcript upload fails for invalid file format."""
        # Arrange
        use_case = SessionTranscriptUploadUseCase(mock_session_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="Invalid file format"):
            use_case.upload_transcript_file(
                sample_session.id, sample_session.user_id, "transcript.txt", "content"
            )

    def test_save_transcript_segments_successful(
        self, mock_session_repo, mock_transcript_repo, sample_session
    ):
        """Test successful transcript segments save."""
        # Arrange
        use_case = SessionTranscriptUploadUseCase(mock_session_repo, mock_transcript_repo)
        mock_session_repo.get_by_id.return_value = sample_session

        segments_data = [
            {
                "start_seconds": 0.0,
                "end_seconds": 5.0,
                "content": "Test content",
                "speaker_id": 1,
            }
        ]

        saved_segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=sample_session.id,
                speaker_id=1,
                start_seconds=0.0,
                end_seconds=5.0,
                content="Test content",
                confidence=1.0,
            )
        ]
        mock_transcript_repo.save_segments.return_value = saved_segments

        updated_session = Session(
            **{**sample_session.__dict__, "status": SessionStatus.COMPLETED}
        )
        mock_session_repo.save.return_value = updated_session

        # Act
        result = use_case.save_transcript_segments(
            sample_session.id, sample_session.user_id, segments_data
        )

        # Assert
        assert result["segments_count"] == 1
        assert result["duration_seconds"] == 5.0
        mock_transcript_repo.save_segments.assert_called_once()
        mock_session_repo.save.assert_called_once()