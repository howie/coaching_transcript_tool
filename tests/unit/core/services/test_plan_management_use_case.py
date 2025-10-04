"""Tests for plan management use cases - Clean Architecture.

This test module focuses on error handling and edge cases for plan management
business logic, following the test coverage improvement plan Day 3.

Target coverage: 29% → 60%
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from src.coaching_assistant.core.models.plan_configuration import (
    PlanConfiguration,
    PlanFeatures,
    PlanLimits,
    PlanPricing,
)
from src.coaching_assistant.core.models.user import User, UserPlan
from src.coaching_assistant.core.repositories.ports import (
    PlanConfigurationRepoPort,
    SessionRepoPort,
    SubscriptionRepoPort,
    UsageLogRepoPort,
    UserRepoPort,
)
from src.coaching_assistant.core.services.plan_management_use_case import (
    PlanRetrievalUseCase,
    PlanValidationUseCase,
)
from src.coaching_assistant.exceptions import DomainException

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def user_id() -> UUID:
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def free_plan_config() -> PlanConfiguration:
    """Sample FREE plan configuration."""
    return PlanConfiguration(
        id=uuid4(),
        plan_type=UserPlan.FREE,
        plan_name="free",
        display_name="Free Plan",
        description="Basic plan for testing",
        tagline="Get started",
        limits=PlanLimits(
            max_sessions=10,
            max_total_minutes=120,
            max_transcription_count=-1,
            max_file_size_mb=60,
            export_formats=["json", "txt"],
            concurrent_processing=1,
            retention_days=30,
        ),
        features=PlanFeatures(priority_support=False),
        pricing=PlanPricing(
            monthly_price_cents=0,
            annual_price_cents=0,
            monthly_price_twd_cents=0,
            annual_price_twd_cents=0,
            currency="TWD",
        ),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        sort_order=1,
    )


@pytest.fixture
def pro_plan_config() -> PlanConfiguration:
    """Sample PRO plan configuration."""
    return PlanConfiguration(
        id=uuid4(),
        plan_type=UserPlan.PRO,
        plan_name="pro",
        display_name="Pro Plan",
        description="Professional plan",
        tagline="For professionals",
        limits=PlanLimits(
            max_sessions=-1,
            max_total_minutes=1000,
            max_transcription_count=-1,
            max_file_size_mb=200,
            export_formats=["json", "txt", "excel"],
            concurrent_processing=3,
            retention_days=90,
        ),
        features=PlanFeatures(priority_support=True),
        pricing=PlanPricing(
            monthly_price_cents=9900,
            annual_price_cents=99000,
            monthly_price_twd_cents=29900,
            annual_price_twd_cents=299000,
            currency="TWD",
        ),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        sort_order=2,
    )


@pytest.fixture
def free_user(user_id: UUID) -> User:
    """Sample user with FREE plan."""
    return User(
        id=user_id,
        email="test@example.com",
        name="Test User",
        plan=UserPlan.FREE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_plan_config_repo() -> Mock:
    """Mock plan configuration repository."""
    return Mock(spec=PlanConfigurationRepoPort)


@pytest.fixture
def mock_user_repo() -> Mock:
    """Mock user repository."""
    return Mock(spec=UserRepoPort)


@pytest.fixture
def mock_subscription_repo() -> Mock:
    """Mock subscription repository."""
    return Mock(spec=SubscriptionRepoPort)


@pytest.fixture
def mock_session_repo() -> Mock:
    """Mock session repository."""
    return Mock(spec=SessionRepoPort)


@pytest.fixture
def mock_usage_log_repo() -> Mock:
    """Mock usage log repository."""
    return Mock(spec=UsageLogRepoPort)


# ============================================================================
# PlanRetrievalUseCase Tests
# ============================================================================


class TestPlanRetrievalUseCase:
    """Tests for plan retrieval operations."""

    @pytest.fixture
    def retrieval_use_case(
        self,
        mock_plan_config_repo: Mock,
        mock_user_repo: Mock,
        mock_subscription_repo: Mock,
    ) -> PlanRetrievalUseCase:
        """Create PlanRetrievalUseCase instance."""
        return PlanRetrievalUseCase(
            plan_config_repo=mock_plan_config_repo,
            user_repo=mock_user_repo,
            subscription_repo=mock_subscription_repo,
        )

    def test_get_all_plans_success(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_plan_config_repo: Mock,
        free_plan_config: PlanConfiguration,
        pro_plan_config: PlanConfiguration,
    ):
        """Test successful retrieval of all plans."""
        mock_plan_config_repo.get_all_active_plans.return_value = [
            free_plan_config,
            pro_plan_config,
        ]

        result = retrieval_use_case.get_all_plans()

        assert len(result) == 2
        assert result[0]["id"] == "free"
        assert result[1]["id"] == "pro"
        assert result[0]["limits"]["maxSessions"] == 10
        assert result[1]["limits"]["maxSessions"] == "unlimited"

    def test_get_all_plans_empty_repository(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_plan_config_repo: Mock,
    ):
        """Test get_all_plans when repository returns empty list."""
        mock_plan_config_repo.get_all_active_plans.return_value = []

        result = retrieval_use_case.get_all_plans()

        assert result == []

    def test_get_user_current_plan_user_not_found(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_user_repo: Mock,
        user_id: UUID,
    ):
        """Test get_user_current_plan raises error when user not found."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(DomainException) as exc_info:
            retrieval_use_case.get_user_current_plan(user_id)

        assert f"User not found: {user_id}" in str(exc_info.value)

    def test_get_user_current_plan_no_config_found(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        user_id: UUID,
        free_user: User,
    ):
        """Test fallback when plan configuration not found in database."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = None

        result = retrieval_use_case.get_user_current_plan(user_id)

        # Should return fallback plan info (without is_current_plan field)
        assert result["id"] == "FREE"
        assert result["name"] == "Free Plan"
        assert result["limits"]["maxTotalMinutes"] == 120
        # Note: fallback doesn't include is_current_plan field

    def test_get_user_current_plan_success(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test successful retrieval of user's current plan."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        result = retrieval_use_case.get_user_current_plan(user_id)

        assert result["user_plan"] == "free"
        assert result["is_current_plan"] is True
        assert result["limits"]["maxSessions"] == 10

    def test_compare_plans_all_plans(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_plan_config_repo: Mock,
        free_plan_config: PlanConfiguration,
        pro_plan_config: PlanConfiguration,
    ):
        """Test plan comparison with all available plans."""
        mock_plan_config_repo.get_all_active_plans.return_value = [
            free_plan_config,
            pro_plan_config,
        ]

        result = retrieval_use_case.compare_plans()

        assert result["total_plans"] == 2
        assert len(result["plans"]) == 2
        assert "comparison_features" in result
        assert "maxTotalMinutes" in result["comparison_features"]

    def test_compare_plans_specific_plans(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_plan_config_repo: Mock,
        free_plan_config: PlanConfiguration,
    ):
        """Test plan comparison with specific plan types."""
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        result = retrieval_use_case.compare_plans(plan_types=[UserPlan.FREE])

        assert result["total_plans"] == 1
        assert len(result["plans"]) == 1
        assert result["plans"][0]["id"] == "free"

    def test_compare_plans_filters_none_configs(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        mock_plan_config_repo: Mock,
        free_plan_config: PlanConfiguration,
    ):
        """Test that compare_plans filters out None configs when plans not found."""
        # First call returns config, second returns None
        mock_plan_config_repo.get_by_plan_type.side_effect = [
            free_plan_config,
            None,
        ]

        result = retrieval_use_case.compare_plans(
            plan_types=[UserPlan.FREE, UserPlan.PRO]
        )

        # Should only include the FREE plan, PRO filtered out
        assert result["total_plans"] == 1
        assert result["plans"][0]["id"] == "free"

    def test_format_plan_config_unlimited_limits(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
        pro_plan_config: PlanConfiguration,
    ):
        """Test formatting of unlimited limits (-1 values)."""
        result = retrieval_use_case._format_plan_config(pro_plan_config)

        assert result["limits"]["maxSessions"] == "unlimited"
        assert result["limits"]["maxTotalMinutes"] == 1000  # Not unlimited
        assert result["limits"]["retentionDays"] == 90  # Not permanent

    def test_format_plan_config_permanent_retention(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
    ):
        """Test formatting of permanent retention (-1 days)."""
        enterprise_config = PlanConfiguration(
            id=uuid4(),
            plan_type=UserPlan.ENTERPRISE,
            plan_name="enterprise",
            display_name="Enterprise",
            description="Enterprise plan",
            tagline="Unlimited",
            limits=PlanLimits(
                max_sessions=-1,
                max_total_minutes=-1,
                max_transcription_count=-1,
                max_file_size_mb=500,
                export_formats=["json", "txt", "excel"],
                concurrent_processing=10,
                retention_days=-1,  # Permanent
            ),
            features=PlanFeatures(priority_support=True),
            pricing=PlanPricing(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        result = retrieval_use_case._format_plan_config(enterprise_config)

        assert result["limits"]["retentionDays"] == "permanent"

    def test_get_fallback_plan_info_pro_plan(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
    ):
        """Test fallback plan info for PRO plan."""
        result = retrieval_use_case._get_fallback_plan_info(UserPlan.PRO)

        assert result["id"] == "PRO"
        assert result["display_name"] == "Pro"
        assert result["limits"]["maxTotalMinutes"] == 1000
        assert result["features"]["prioritySupport"] is True

    def test_get_fallback_plan_info_enterprise_plan(
        self,
        retrieval_use_case: PlanRetrievalUseCase,
    ):
        """Test fallback plan info for ENTERPRISE plan."""
        result = retrieval_use_case._get_fallback_plan_info(UserPlan.ENTERPRISE)

        assert result["id"] == "ENTERPRISE"
        assert result["limits"]["maxTotalMinutes"] == "unlimited"
        assert result["limits"]["retentionDays"] == "permanent"


# ============================================================================
# PlanValidationUseCase Tests
# ============================================================================


class TestPlanValidationUseCase:
    """Tests for plan validation operations."""

    @pytest.fixture
    def validation_use_case(
        self,
        mock_plan_config_repo: Mock,
        mock_user_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
    ) -> PlanValidationUseCase:
        """Create PlanValidationUseCase instance."""
        return PlanValidationUseCase(
            plan_config_repo=mock_plan_config_repo,
            user_repo=mock_user_repo,
            session_repo=mock_session_repo,
            usage_log_repo=mock_usage_log_repo,
        )

    def test_validate_user_limits_user_not_found(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        user_id: UUID,
    ):
        """Test validate_user_limits raises error when user not found."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(DomainException) as exc_info:
            validation_use_case.validate_user_limits(user_id)

        assert f"User not found: {user_id}" in str(exc_info.value)

    def test_validate_user_limits_no_plan_config(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
    ):
        """Test validation when no plan configuration found."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = None
        mock_session_repo.count_user_sessions.return_value = 5
        mock_session_repo.get_total_duration_minutes.return_value = 60
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is True
        assert result["message"] == "No plan limits configured"
        assert result["current_usage"]["session_count"] == 5

    def test_validate_user_limits_within_limits(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test validation when usage is within plan limits."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 5  # Under 10 limit
        mock_session_repo.get_total_duration_minutes.return_value = (
            60  # Under 120 limit
        )
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is True
        assert len(result["violations"]) == 0
        assert result["current_usage"]["session_count"] == 5
        assert result["current_usage"]["total_minutes"] == 60

    def test_validate_user_limits_session_count_exceeded(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test validation when session count limit is exceeded."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 10  # At limit
        mock_session_repo.get_total_duration_minutes.return_value = 60
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is False
        assert len(result["violations"]) == 1
        assert result["violations"][0]["type"] == "session_count"
        assert result["violations"][0]["limit"] == 10
        assert result["violations"][0]["current"] == 10

    def test_validate_user_limits_minutes_exceeded(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test validation when total minutes limit is exceeded."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 5
        mock_session_repo.get_total_duration_minutes.return_value = 120  # At limit
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is False
        assert len(result["violations"]) == 1
        assert result["violations"][0]["type"] == "total_minutes"
        assert result["violations"][0]["limit"] == 120
        assert result["violations"][0]["current"] == 120

    def test_validate_user_limits_multiple_violations(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test validation with multiple limit violations."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 15  # Exceeded
        mock_session_repo.get_total_duration_minutes.return_value = 150  # Exceeded
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is False
        assert len(result["violations"]) == 2
        violation_types = {v["type"] for v in result["violations"]}
        assert "session_count" in violation_types
        assert "total_minutes" in violation_types

    def test_validate_user_limits_approaching_session_limit_warning(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test warning when approaching session count limit (80%)."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 9  # 90% of 10
        mock_session_repo.get_total_duration_minutes.return_value = 60
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is True
        assert len(result["warnings"]) >= 1
        warning_types = {w["type"] for w in result["warnings"]}
        assert "session_count_warning" in warning_types

    def test_validate_user_limits_approaching_minutes_limit_warning(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test warning when approaching minutes limit (80%)."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config
        mock_session_repo.count_user_sessions.return_value = 5
        mock_session_repo.get_total_duration_minutes.return_value = 100  # 83% of 120
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        assert result["valid"] is True
        assert len(result["warnings"]) >= 1
        warning_types = {w["type"] for w in result["warnings"]}
        assert "minutes_warning" in warning_types

    def test_validate_file_size_user_not_found(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        user_id: UUID,
    ):
        """Test validate_file_size raises error when user not found."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(DomainException) as exc_info:
            validation_use_case.validate_file_size(user_id, 50.0)

        assert f"User not found: {user_id}" in str(exc_info.value)

    def test_validate_file_size_no_plan_config(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        user_id: UUID,
        free_user: User,
    ):
        """Test file size validation when no plan config found."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = None

        result = validation_use_case.validate_file_size(user_id, 100.0)

        assert result["valid"] is True
        assert result["message"] == "No file size limits configured"

    def test_validate_file_size_within_limit(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test file size validation within plan limit."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        result = validation_use_case.validate_file_size(user_id, 50.0)

        assert result["valid"] is True
        assert result["limit"] == 60
        assert result["actual"] == 50.0
        assert "within limits" in result["message"]

    def test_validate_file_size_exceeds_limit(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        user_id: UUID,
        free_user: User,
        free_plan_config: PlanConfiguration,
    ):
        """Test file size validation when exceeding plan limit."""
        mock_user_repo.get_by_id.return_value = free_user
        mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        result = validation_use_case.validate_file_size(user_id, 80.0)

        assert result["valid"] is False
        assert result["limit"] == 60
        assert result["actual"] == 80.0
        assert "exceeds plan limit" in result["message"]

    def test_get_current_usage_with_repository_methods(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
    ):
        """Test _get_current_usage using repository methods (Clean Architecture)."""
        mock_session_repo.count_user_sessions.return_value = 7
        mock_session_repo.get_total_duration_minutes.return_value = 85

        # Create mock usage logs with cost_usd attribute
        mock_log1 = Mock()
        mock_log1.cost_usd = 5.50
        mock_log2 = Mock()
        mock_log2.cost_usd = 3.25
        mock_usage_log_repo.get_by_user_id.return_value = [mock_log1, mock_log2]

        result = validation_use_case._get_current_usage(user_id)

        assert result["session_count"] == 7
        assert result["total_minutes"] == 85
        assert result["total_cost_usd"] == 8.75
        assert "period_start" in result
        assert "period_end" in result

    def test_get_current_usage_fallback_to_user_model(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_session_repo: Mock,
        mock_user_repo: Mock,
        user_id: UUID,
        free_user: User,
    ):
        """Test _get_current_usage falls back to user model on repository error."""
        # Simulate repository method not available (AttributeError)
        mock_session_repo.count_user_sessions.side_effect = AttributeError(
            "Method not implemented"
        )

        # Add usage attributes to user model
        free_user.session_count = 3
        free_user.usage_minutes = 45
        mock_user_repo.get_by_id.return_value = free_user

        result = validation_use_case._get_current_usage(user_id)

        # Should fallback to user model attributes
        assert result["session_count"] == 3
        assert result["total_minutes"] == 45
        assert result["total_cost_usd"] == 0.0

    def test_validate_user_limits_unlimited_plan_no_violations(
        self,
        validation_use_case: PlanValidationUseCase,
        mock_user_repo: Mock,
        mock_plan_config_repo: Mock,
        mock_session_repo: Mock,
        mock_usage_log_repo: Mock,
        user_id: UUID,
        pro_plan_config: PlanConfiguration,
    ):
        """Test that unlimited limits (-1) never trigger violations."""
        pro_user = User(
            id=user_id,
            email="pro@example.com",
            name="Pro User",
            plan=UserPlan.PRO,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_user_repo.get_by_id.return_value = pro_user
        mock_plan_config_repo.get_by_plan_type.return_value = pro_plan_config
        mock_session_repo.count_user_sessions.return_value = 999  # Very high
        mock_session_repo.get_total_duration_minutes.return_value = 500
        mock_usage_log_repo.get_by_user_id.return_value = []

        result = validation_use_case.validate_user_limits(user_id)

        # max_sessions is -1 (unlimited), so no session_count violation
        # max_total_minutes is 1000, so 500 is within limit
        assert result["valid"] is True
        assert len(result["violations"]) == 0
