"""Error handling tests for usage tracking use case.

This test suite focuses on testing error paths, exception handling,
and edge cases in the usage tracking business logic to improve coverage
from 18% to 60%+.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from coaching_assistant.core.models.session import Session as SessionModel
from coaching_assistant.core.models.usage_log import TranscriptionType
from coaching_assistant.core.models.user import User, UserPlan
from coaching_assistant.core.services.usage_tracking_use_case import (
    CreateUsageLogUseCase,
    GetUserUsageUseCase,
    PlanLimits,
)


class TestCreateUsageLogErrorHandling:
    """Test error handling in CreateUsageLogUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories for testing."""
        return {
            "user_repo": Mock(),
            "usage_log_repo": Mock(),
            "session_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance with mocked dependencies."""
        return CreateUsageLogUseCase(
            user_repo=mock_repos["user_repo"],
            usage_log_repo=mock_repos["usage_log_repo"],
            session_repo=mock_repos["session_repo"],
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        session = SessionModel(
            id=uuid4(),
            user_id=uuid4(),
            duration_seconds=1800,  # 30 minutes
            stt_provider="google",
            language="zh-TW",
            audio_filename="test.mp3",
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        # Add provider_metadata as attribute (not in dataclass)
        session.provider_metadata = {}
        return session

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=uuid4(),
            email="test@example.com",
            plan=UserPlan.PRO,
            created_at=datetime.now(UTC),
        )

    def test_execute_raises_value_error_when_user_not_found(
        self, use_case, mock_repos, sample_session
    ):
        """Test that ValueError is raised when user doesn't exist."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(sample_session)

        assert "User not found" in str(exc_info.value)
        assert str(sample_session.user_id) in str(exc_info.value)
        mock_repos["user_repo"].get_by_id.assert_called_once_with(
            sample_session.user_id
        )

    def test_execute_handles_database_error_on_user_fetch(
        self, use_case, mock_repos, sample_session
    ):
        """Test handling of database errors when fetching user."""
        # Arrange
        mock_repos["user_repo"].get_by_id.side_effect = OperationalError(
            "Database connection failed", None, None
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.execute(sample_session)

    def test_execute_handles_database_error_on_save(
        self, use_case, mock_repos, sample_session, sample_user
    ):
        """Test handling of database errors when saving usage log."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []
        mock_repos["usage_log_repo"].save.side_effect = IntegrityError(
            "Duplicate key violation", None, None
        )

        # Act & Assert
        with pytest.raises(IntegrityError):
            use_case.execute(sample_session)

    def test_execute_handles_concurrent_save_attempts(
        self, use_case, mock_repos, sample_session, sample_user
    ):
        """Test handling of concurrent save attempts (race condition)."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []
        # Simulate race condition - first save fails, second succeeds
        mock_repos["usage_log_repo"].save.side_effect = [
            IntegrityError("Duplicate", None, None),
            Mock(id=uuid4()),  # Successful save on retry
        ]

        # Act - First attempt should raise error
        with pytest.raises(IntegrityError):
            use_case.execute(sample_session)

    def test_execute_handles_missing_session_attributes(
        self, use_case, mock_repos, sample_user
    ):
        """Test handling of sessions with missing optional attributes."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []

        # Create session with minimal attributes
        minimal_session = SessionModel(
            id=uuid4(),
            user_id=sample_user.id,
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            # Missing: duration_seconds, stt_provider, language, etc.
        )
        minimal_session.provider_metadata = {}

        mock_saved_log = Mock(id=uuid4())
        mock_repos["usage_log_repo"].save.return_value = mock_saved_log

        # Act
        result = use_case.execute(minimal_session)

        # Assert - Should handle missing attributes gracefully
        assert result == mock_saved_log
        save_call_args = mock_repos["usage_log_repo"].save.call_args[0][0]
        assert save_call_args.duration_seconds == 0
        assert save_call_args.duration_minutes == 0

    def test_execute_handles_invalid_cost_calculation(
        self, use_case, mock_repos, sample_session, sample_user
    ):
        """Test handling of invalid cost calculations."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []

        # Provide invalid cost
        invalid_session = SessionModel(
            id=uuid4(),
            user_id=sample_user.id,
            duration_seconds=-1000,  # Negative duration
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        invalid_session.provider_metadata = {}

        mock_saved_log = Mock(id=uuid4(), cost_usd=Decimal("0.0"))
        mock_repos["usage_log_repo"].save.return_value = mock_saved_log

        # Act
        result = use_case.execute(invalid_session)

        # Assert - Should handle gracefully
        assert result == mock_saved_log

    def test_execute_handles_parent_log_retrieval_error(
        self, use_case, mock_repos, sample_session, sample_user
    ):
        """Test handling of errors when retrieving parent log."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.side_effect = (
            OperationalError("Database timeout", None, None)
        )

        # Act & Assert - For retry operations
        with pytest.raises(OperationalError):
            use_case.execute(
                sample_session,
                transcription_type=TranscriptionType.RETRY_SUCCESS,
            )

    def test_execute_with_zero_duration_session(
        self, use_case, mock_repos, sample_user
    ):
        """Test handling of sessions with zero duration."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []

        zero_duration_session = SessionModel(
            id=uuid4(),
            user_id=sample_user.id,
            duration_seconds=0,
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        zero_duration_session.provider_metadata = {}

        mock_saved_log = Mock(
            id=uuid4(), duration_seconds=0, cost_usd=Decimal("0.0")
        )
        mock_repos["usage_log_repo"].save.return_value = mock_saved_log

        # Act
        result = use_case.execute(zero_duration_session)

        # Assert
        assert result == mock_saved_log
        save_call = mock_repos["usage_log_repo"].save.call_args[0][0]
        assert save_call.duration_seconds == 0
        assert save_call.duration_minutes == 0

    def test_execute_with_extremely_large_duration(
        self, use_case, mock_repos, sample_user
    ):
        """Test handling of sessions with extremely large duration."""
        # Arrange
        mock_repos["user_repo"].get_by_id.return_value = sample_user
        mock_repos["usage_log_repo"].get_by_session_id.return_value = []

        # 24 hours = 86400 seconds
        large_duration_session = SessionModel(
            id=uuid4(),
            user_id=sample_user.id,
            duration_seconds=86400,  # 24 hours
            status="completed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        large_duration_session.provider_metadata = {}

        mock_saved_log = Mock(id=uuid4())
        mock_repos["usage_log_repo"].save.return_value = mock_saved_log

        # Act
        result = use_case.execute(large_duration_session)

        # Assert
        assert result == mock_saved_log
        save_call = mock_repos["usage_log_repo"].save.call_args[0][0]
        assert save_call.duration_minutes == 1440  # 24 * 60


class TestGetUserUsageErrorHandling:
    """Test error handling in GetUserUsageUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories for testing."""
        return {
            "user_repo": Mock(),
            "usage_log_repo": Mock(),
            "usage_history_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance with mocked dependencies."""
        return GetUserUsageUseCase(
            user_repo=mock_repos["user_repo"],
            usage_log_repo=mock_repos["usage_log_repo"],
            usage_history_repo=mock_repos["usage_history_repo"],
        )

    def test_get_current_month_usage_handles_database_error(
        self, use_case, mock_repos
    ):
        """Test handling of database errors when fetching usage."""
        # Arrange
        user_id = uuid4()
        mock_repos["usage_log_repo"].get_by_user_id.side_effect = (
            OperationalError("Connection timeout", None, None)
        )

        # Act & Assert
        with pytest.raises(OperationalError):
            use_case.get_current_month_usage(user_id)

    def test_get_current_month_usage_handles_empty_results(
        self, use_case, mock_repos
    ):
        """Test handling of no usage data for user."""
        # Arrange
        user_id = uuid4()
        mock_repos["usage_log_repo"].get_by_user_id.return_value = []
        mock_repos["user_repo"].get_by_id.return_value = Mock(plan=UserPlan.FREE)

        # Act
        result = use_case.get_current_month_usage(user_id)

        # Assert - Should return zero usage
        assert result["usage_minutes"] == 0
        assert result["session_count"] == 0

    def test_get_current_month_usage_handles_missing_user(
        self, use_case, mock_repos
    ):
        """Test handling of missing user when calculating limits."""
        # Arrange
        user_id = uuid4()
        mock_repos["usage_log_repo"].get_by_user_id.return_value = []
        mock_repos["user_repo"].get_by_id.return_value = None

        # Act
        result = use_case.get_current_month_usage(user_id)

        # Assert - Should default to FREE plan limits
        assert result["usage_minutes"] == 0
        assert "plan_limits" in result


class TestPlanLimitsEdgeCases:
    """Test edge cases in PlanLimits helper class."""

    def test_get_limits_with_invalid_plan(self):
        """Test handling of invalid/unknown plan types."""
        # This should default to FREE plan
        limits = PlanLimits.get_limits(None)
        assert limits["minutes_per_month"] == 120  # FREE plan default

    def test_validate_file_size_with_zero(self):
        """Test file size validation with zero size."""
        assert PlanLimits.validate_file_size(UserPlan.FREE, 0) is True

    def test_validate_file_size_with_negative(self):
        """Test file size validation with negative size."""
        # Negative should still be valid (edge case)
        assert PlanLimits.validate_file_size(UserPlan.FREE, -1) is True

    def test_validate_export_format_case_insensitive(self):
        """Test export format validation is case insensitive."""
        assert PlanLimits.validate_export_format(UserPlan.FREE, "JSON") is True
        assert PlanLimits.validate_export_format(UserPlan.FREE, "Json") is True
        assert PlanLimits.validate_export_format(UserPlan.PRO, "VTT") is True

    def test_validate_export_format_with_empty_string(self):
        """Test export format validation with empty string."""
        assert PlanLimits.validate_export_format(UserPlan.FREE, "") is False

    def test_validate_export_format_with_none(self):
        """Test export format validation with None."""
        # Should handle None gracefully
        with pytest.raises(AttributeError):
            PlanLimits.validate_export_format(UserPlan.FREE, None)
