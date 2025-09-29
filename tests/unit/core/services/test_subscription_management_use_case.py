"""Unit tests for SubscriptionManagementUseCase."""

from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.coaching_assistant.core.models.subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionStatus,
)
from src.coaching_assistant.core.models.user import User, UserPlan
from src.coaching_assistant.core.services.subscription_management_use_case import (
    SubscriptionCreationUseCase,
    SubscriptionModificationUseCase,
    SubscriptionRetrievalUseCase,
)
from src.coaching_assistant.exceptions import DomainException


class TestSubscriptionModificationUseCase:
    """Test cases for SubscriptionModificationUseCase focusing on plan ID case handling."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_subscription_repo = Mock()
        self.mock_user_repo = Mock()
        self.mock_plan_config_repo = Mock()

        self.use_case = SubscriptionModificationUseCase(
            subscription_repo=self.mock_subscription_repo,
            user_repo=self.mock_user_repo,
            plan_config_repo=self.mock_plan_config_repo,
        )

        # Sample data
        self.user_id = uuid4()
        self.subscription_id = uuid4()

        self.sample_subscription = SaasSubscription(
            id=self.subscription_id,
            user_id=self.user_id,
            plan_id="free",
            plan_name="FREE Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=0,
            current_period_start=datetime.now(UTC).date(),
            current_period_end=datetime.now(UTC).date(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            currency="TWD",
            auth_id=uuid4(),
        )

        # Mock plan configuration
        self.mock_plan_config = SimpleNamespace(
            plan_type=UserPlan.PRO,
            pricing=SimpleNamespace(
                monthly_price_twd_cents=89900,
                annual_price_twd_cents=749900,
                monthly_price_cents=0,
                annual_price_cents=0,
            ),
        )

    def test_upgrade_subscription_uppercase_plan_id(self):
        """Test upgrade with uppercase plan ID (as sent by frontend)."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = self.mock_plan_config
        self.mock_subscription_repo.save_subscription.return_value = (
            self.sample_subscription
        )
        self.mock_user_repo.update_plan.return_value = None

        # Act
        result = self.use_case.upgrade_subscription(
            user_id=self.user_id,
            new_plan_id="PRO",  # Uppercase as sent by frontend
            new_billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert result["new_plan"] == UserPlan.PRO.value
        assert result["requested_plan"] == "PRO"
        assert result["old_plan"] == "free"
        assert result["operation"] == "upgrade"
        self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
            UserPlan.PRO
        )

    def test_upgrade_subscription_lowercase_plan_id(self):
        """Test upgrade with lowercase plan ID."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = self.mock_plan_config
        self.mock_subscription_repo.save_subscription.return_value = (
            self.sample_subscription
        )
        self.mock_user_repo.update_plan.return_value = None

        # Act
        result = self.use_case.upgrade_subscription(
            user_id=self.user_id,
            new_plan_id="pro",  # Lowercase
            new_billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert result["new_plan"] == UserPlan.PRO.value
        assert result["requested_plan"] == "pro"
        assert result["old_plan"] == "free"
        self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
            UserPlan.PRO
        )

    def test_upgrade_subscription_invalid_plan_id(self):
        """Test upgrade with invalid plan ID."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plan_id: INVALID"):
            self.use_case.upgrade_subscription(
                user_id=self.user_id,
                new_plan_id="INVALID",
                new_billing_cycle="monthly",
            )

    def test_downgrade_subscription_uppercase_plan_id(self):
        """Test downgrade with uppercase plan ID."""
        # Arrange - start with PRO subscription
        pro_subscription = self.sample_subscription
        pro_subscription.plan_id = "pro"
        pro_subscription.amount_twd = 89900

        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            pro_subscription
        )

        # Mock FREE plan config
        free_plan_config = SimpleNamespace(
            plan_type=UserPlan.FREE,
            pricing=SimpleNamespace(
                monthly_price_twd_cents=0,
                annual_price_twd_cents=0,
                monthly_price_cents=0,
                annual_price_cents=0,
            ),
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        self.mock_subscription_repo.save_subscription.return_value = pro_subscription
        self.mock_user_repo.update_plan.return_value = None

        # Act
        result = self.use_case.downgrade_subscription(
            user_id=self.user_id,
            new_plan_id="FREE",  # Uppercase as sent by frontend
            new_billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert result["new_plan"] == UserPlan.FREE.value
        assert result["requested_plan"] == "FREE"
        assert result["old_plan"] == "pro"
        assert result["operation"] == "downgrade"
        self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
            UserPlan.FREE
        )

    def test_calculate_proration_uppercase_plan_id(self):
        """Test proration calculation with uppercase plan ID."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = self.mock_plan_config

        # Act
        result = self.use_case.calculate_proration(
            user_id=self.user_id,
            new_plan_id="ENTERPRISE",  # Uppercase
            new_billing_cycle="monthly",
        )

        # Assert
        assert "current_plan_remaining_value" in result
        assert "new_plan_prorated_cost" in result
        assert "net_charge" in result
        self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
            UserPlan.ENTERPRISE
        )

    def test_upgrade_free_plan_pricing_validation(self):
        """Test that FREE plan pricing is handled correctly."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )

        # Mock FREE plan config with 0 pricing
        free_plan_config = SimpleNamespace(
            plan_type=UserPlan.FREE,
            pricing=SimpleNamespace(
                monthly_price_twd_cents=0,
                annual_price_twd_cents=0,
                monthly_price_cents=0,
                annual_price_cents=0,
            ),
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = free_plan_config

        self.mock_subscription_repo.save_subscription.return_value = (
            self.sample_subscription
        )
        self.mock_user_repo.update_plan.return_value = None

        # Act - upgrade from paid plan to FREE (downgrade scenario)
        result = self.use_case.downgrade_subscription(
            user_id=self.user_id,
            new_plan_id="FREE",
            new_billing_cycle="monthly",
        )

        # Assert - should succeed with FREE plan
        assert result["success"] is True
        assert result["new_plan"] == UserPlan.FREE.value
        assert result["requested_plan"] == "FREE"

    def test_paid_plan_zero_pricing_validation(self):
        """Test that paid plans with zero pricing are rejected."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )

        # Mock PRO plan config with invalid 0 pricing
        invalid_plan_config = SimpleNamespace(
            plan_type=UserPlan.PRO,
            pricing=SimpleNamespace(
                monthly_price_twd_cents=0,
                annual_price_twd_cents=0,
                monthly_price_cents=0,
                annual_price_cents=0,
            ),
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = invalid_plan_config

        # Act & Assert
        with pytest.raises(ValueError, match="Paid plan PRO cannot have zero pricing"):
            self.use_case.upgrade_subscription(
                user_id=self.user_id,
                new_plan_id="PRO",
                new_billing_cycle="monthly",
            )

    def test_upgrade_no_active_subscription(self):
        """Test upgrade when user has no active subscription."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="No active subscription found"):
            self.use_case.upgrade_subscription(
                user_id=self.user_id,
                new_plan_id="PRO",
                new_billing_cycle="monthly",
            )

    def test_upgrade_inactive_subscription(self):
        """Test upgrade when subscription is not active."""
        # Arrange
        inactive_subscription = self.sample_subscription
        inactive_subscription.status = SubscriptionStatus.CANCELLED
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            inactive_subscription
        )

        # Act & Assert
        with pytest.raises(DomainException, match="Subscription is not active"):
            self.use_case.upgrade_subscription(
                user_id=self.user_id,
                new_plan_id="PRO",
                new_billing_cycle="monthly",
            )

    def test_plan_id_case_variations(self):
        """Test all plan ID case variations are handled correctly."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            self.sample_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = self.mock_plan_config
        self.mock_subscription_repo.save_subscription.return_value = (
            self.sample_subscription
        )
        self.mock_user_repo.update_plan.return_value = None

        # Test cases: (input_plan_id, expected_enum)
        test_cases = [
            ("PRO", UserPlan.PRO),
            ("pro", UserPlan.PRO),
            ("Pro", UserPlan.PRO),
            ("ENTERPRISE", UserPlan.ENTERPRISE),
            ("enterprise", UserPlan.ENTERPRISE),
            ("FREE", UserPlan.FREE),
            ("free", UserPlan.FREE),
            ("STUDENT", UserPlan.STUDENT),
            ("student", UserPlan.STUDENT),
            ("COACHING_SCHOOL", UserPlan.COACHING_SCHOOL),
            ("coaching_school", UserPlan.COACHING_SCHOOL),
        ]

        for input_plan_id, expected_enum in test_cases:
            # Reset mock calls
            self.mock_plan_config_repo.reset_mock()
            self.mock_plan_config.plan_type = expected_enum

            # Act
            result = self.use_case.upgrade_subscription(
                user_id=self.user_id,
                new_plan_id=input_plan_id,
                new_billing_cycle="monthly",
            )

            # Assert
            assert result["success"] is True
            assert result["new_plan"] == expected_enum.value
            assert result["requested_plan"] == input_plan_id
            self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
                expected_enum
            )


class TestSubscriptionRetrievalUseCase:
    """Test cases for SubscriptionRetrievalUseCase."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_subscription_repo = Mock()
        self.mock_user_repo = Mock()

        self.use_case = SubscriptionRetrievalUseCase(
            subscription_repo=self.mock_subscription_repo,
            user_repo=self.mock_user_repo,
        )

        self.user_id = uuid4()
        self.sample_user = User(
            id=self.user_id,
            email="test@example.com",
            plan=UserPlan.FREE,
        )

    def test_get_current_subscription_no_subscription(self):
        """Test getting current subscription when user has none."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            None
        )

        # Act
        result = self.use_case.get_current_subscription(self.user_id)

        # Assert
        assert result["status"] == "no_subscription"
        assert result["subscription"] is None
        assert result["payment_method"] is None

    def test_get_current_subscription_with_subscription(self):
        """Test getting current subscription when user has one."""
        # Arrange
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=self.user_id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=89900,
            current_period_start=datetime.now(UTC).date(),
            current_period_end=datetime.now(UTC).date(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            currency="TWD",
            auth_id=uuid4(),
        )

        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            subscription
        )
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            None
        )

        # Act
        result = self.use_case.get_current_subscription(self.user_id)

        # Assert
        assert result["status"] == "active"
        assert result["subscription"]["plan_id"] == "pro"
        assert result["subscription"]["amount_cents"] == 89900


class TestSubscriptionCreationUseCase:
    """Test cases for SubscriptionCreationUseCase."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_subscription_repo = Mock()
        self.mock_user_repo = Mock()
        self.mock_plan_config_repo = Mock()

        self.use_case = SubscriptionCreationUseCase(
            subscription_repo=self.mock_subscription_repo,
            user_repo=self.mock_user_repo,
            plan_config_repo=self.mock_plan_config_repo,
        )

        self.user_id = uuid4()
        self.sample_user = User(
            id=self.user_id,
            email="test@example.com",
            plan=UserPlan.FREE,
        )

    def test_create_authorization_valid_plans(self):
        """Test creating authorization with valid plan IDs."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            None
        )

        mock_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=self.user_id,
            merchant_member_id=f"MEMBER_{self.user_id}",
            auth_amount=100,
            period_type="Month",
            frequency=1,
            period_amount=0,
            auth_status=ECPayAuthStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.save_credit_authorization.return_value = mock_auth

        # Test valid plan IDs
        valid_plans = [
            "STUDENT",
            "PRO",
            "ENTERPRISE",
            "COACHING_SCHOOL",
            "coaching_school",
        ]
        for plan_id in valid_plans:
            # Reset mock
            self.mock_subscription_repo.reset_mock()
            self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = None
            self.mock_subscription_repo.save_credit_authorization.return_value = (
                mock_auth
            )

            # Act
            result = self.use_case.create_authorization(
                user_id=self.user_id, plan_id=plan_id, billing_cycle="monthly"
            )

            # Assert
            assert result["success"] is True
            assert "action_url" in result
            assert "form_data" in result

    def test_create_authorization_invalid_plan(self):
        """Test creating authorization with invalid plan ID."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plan_id"):
            self.use_case.create_authorization(
                user_id=self.user_id,
                plan_id="INVALID_PLAN",
                billing_cycle="monthly",
            )

    def test_create_authorization_invalid_billing_cycle(self):
        """Test creating authorization with invalid billing cycle."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid billing_cycle"):
            self.use_case.create_authorization(
                user_id=self.user_id, plan_id="PRO", billing_cycle="invalid"
            )

    def test_create_subscription_accepts_uppercase_plan_id(self):
        """Test creating subscription when plan ID and billing cycle are uppercase."""
        authorization_id = uuid4()
        mock_auth = ECPayCreditAuthorization(
            id=authorization_id,
            user_id=self.user_id,
            merchant_member_id=f"MEMBER_{self.user_id}",
            auth_amount=100,
            period_type="Month",
            period_amount=0,
            auth_status=ECPayAuthStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            mock_auth
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None

        mock_plan_config = SimpleNamespace(
            plan_type=UserPlan.PRO,
            pricing=SimpleNamespace(
                monthly_price_twd_cents=89900,
                annual_price_twd_cents=0,
                monthly_price_cents=0,
                annual_price_cents=0,
            ),
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = mock_plan_config

        self.mock_subscription_repo.save_subscription.side_effect = (
            lambda subscription: subscription
        )
        self.mock_user_repo.update_plan.return_value = None

        result = self.use_case.create_subscription(
            user_id=self.user_id,
            authorization_id=authorization_id,
            plan_id="PRO",
            billing_cycle="MONTHLY",
        )

        assert result.plan_id == UserPlan.PRO.value
        assert result.billing_cycle == "monthly"
        assert result.amount_twd == mock_plan_config.pricing.monthly_price_twd_cents
        self.mock_plan_config_repo.get_by_plan_type.assert_called_once_with(
            UserPlan.PRO
        )
        self.mock_user_repo.update_plan.assert_called_once_with(
            self.user_id, UserPlan.PRO
        )
