"""Unit tests for subscription management use cases."""

from datetime import date, datetime, UTC
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from src.coaching_assistant.core.models.subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)
from src.coaching_assistant.core.models.user import User, UserPlan
from src.coaching_assistant.core.services.subscription_management_use_case import (
    SubscriptionCreationUseCase,
    SubscriptionModificationUseCase,
    SubscriptionRetrievalUseCase,
)
from src.coaching_assistant.exceptions import DomainException
from src.coaching_assistant.models.plan_configuration import PlanConfiguration


@pytest.fixture
def mock_subscription_repo():
    """Mock subscription repository."""
    return Mock()


@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    return Mock()


@pytest.fixture
def mock_plan_config_repo():
    """Mock plan configuration repository."""
    return Mock()


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        plan=UserPlan.FREE,
    )


@pytest.fixture
def sample_plan_config():
    """Sample plan configuration for testing."""
    return PlanConfiguration(
        id=1,
        plan_type=UserPlan.PRO,
        monthly_price_twd_cents=99900,  # 999 TWD
        annual_price_twd_cents=999900,  # 9999 TWD
    )


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

    def test_create_authorization_success(self, sample_user):
        """Test successful authorization creation."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            None
        )

        mock_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_{sample_user.id}",
            auth_amount=100,
            period_type="Month",
            period_amount=0,
            auth_status=ECPayAuthStatus.PENDING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            frequency=1,
        )
        self.mock_subscription_repo.save_credit_authorization.return_value = mock_auth

        # Act
        result = self.use_case.create_authorization(
            user_id=sample_user.id,
            plan_id="PRO",
            billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert "action_url" in result
        assert "form_data" in result
        self.mock_user_repo.get_by_id.assert_called_once_with(sample_user.id)
        self.mock_subscription_repo.save_credit_authorization.assert_called_once()

    def test_create_authorization_user_not_found(self):
        """Test authorization creation with non-existent user."""
        # Arrange
        user_id = uuid4()
        self.mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(DomainException, match="User not found"):
            self.use_case.create_authorization(
                user_id=user_id,
                plan_id="PRO",
                billing_cycle="monthly",
            )

    def test_create_authorization_invalid_plan_id(self, sample_user):
        """Test authorization creation with invalid plan ID."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plan_id"):
            self.use_case.create_authorization(
                user_id=sample_user.id,
                plan_id="INVALID",
                billing_cycle="monthly",
            )

    def test_create_authorization_invalid_billing_cycle(self, sample_user):
        """Test authorization creation with invalid billing cycle."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid billing_cycle"):
            self.use_case.create_authorization(
                user_id=sample_user.id,
                plan_id="PRO",
                billing_cycle="invalid",
            )

    def test_create_authorization_existing_active_auth(self, sample_user):
        """Test authorization creation when user already has active authorization."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user

        existing_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_{sample_user.id}",
            auth_amount=100,
            period_type="Month",
            period_amount=0,
            auth_status=ECPayAuthStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            frequency=1,
        )
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            existing_auth
        )

        # Act & Assert
        with pytest.raises(
            DomainException,
            match="already has an active credit card authorization",
        ):
            self.use_case.create_authorization(
                user_id=sample_user.id,
                plan_id="PRO",
                billing_cycle="monthly",
            )

    def test_create_subscription_success(self, sample_user, sample_plan_config):
        """Test successful subscription creation."""
        # Arrange
        auth_id = uuid4()

        mock_auth = ECPayCreditAuthorization(
            id=auth_id,
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_{sample_user.id}",
            auth_amount=100,
            period_type="Month",
            period_amount=99900,
            auth_status=ECPayAuthStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            frequency=1,
        )
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            mock_auth
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None
        self.mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.save_subscription.return_value = mock_subscription

        # Act
        result = self.use_case.create_subscription(
            user_id=sample_user.id,
            authorization_id=auth_id,
            plan_id="PRO",
            billing_cycle="monthly",
        )

        # Assert
        assert result.user_id == sample_user.id
        assert result.plan_id == "pro"
        assert result.billing_cycle == "monthly"
        self.mock_user_repo.update_plan.assert_called_once_with(
            sample_user.id, UserPlan.PRO
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

    def test_get_current_subscription_success(self, sample_user):
        """Test successful subscription retrieval."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user

        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            amount_twd=99900,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            currency="TWD",
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )

        mock_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_{sample_user.id}",
            auth_amount=100,
            period_type="Month",
            period_amount=0,
            auth_status=ECPayAuthStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            frequency=1,
        )
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            mock_auth
        )

        # Act
        result = self.use_case.get_current_subscription(sample_user.id)

        # Assert
        assert result["status"] == "active"
        assert result["subscription"]["plan_id"] == "pro"
        assert result["subscription"]["billing_cycle"] == "monthly"
        assert result["payment_method"]["auth_id"] == mock_auth.merchant_member_id

    def test_get_current_subscription_user_not_found(self):
        """Test subscription retrieval with non-existent user."""
        # Arrange
        user_id = uuid4()
        self.mock_user_repo.get_by_id.return_value = None

        # Act
        result = self.use_case.get_current_subscription(user_id)

        # Assert - production code catches exception and returns error status
        assert result["status"] == "error"
        assert result["subscription"] is None

    def test_get_current_subscription_no_subscription(self, sample_user):
        """Test subscription retrieval when user has no subscription."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = (
            None
        )

        # Act
        result = self.use_case.get_current_subscription(sample_user.id)

        # Assert
        assert result["status"] == "no_subscription"
        assert result["subscription"] is None

    def test_get_current_subscription_error_handling(self, sample_user):
        """Test subscription retrieval with database errors."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = sample_user
        self.mock_subscription_repo.get_subscription_by_user_id.side_effect = Exception(
            "Database error"
        )
        # Authorization query should also be set up to avoid side effects
        self.mock_subscription_repo.get_credit_authorization_by_user_id.return_value = None

        # Act
        result = self.use_case.get_current_subscription(sample_user.id)

        # Assert - production code logs the error but treats it as recoverable,
        # returning "no_subscription" status when subscription is None
        assert result["status"] == "no_subscription"
        assert result["subscription"] is None

    def test_get_subscription_payments_success(self, sample_user):
        """Test successful payment history retrieval."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )

        mock_payments = [
            SubscriptionPayment(
                id=uuid4(),
                subscription_id=mock_subscription.id,
                gwsr="TEST123456",
                amount=99900,
                status=PaymentStatus.SUCCESS,
                period_start=date.today(),
                period_end=date.today(),
                created_at=datetime.now(UTC),
                currency="TWD",
            )
        ]
        self.mock_subscription_repo.get_payments_for_subscription.return_value = (
            mock_payments
        )

        # Act
        result = self.use_case.get_subscription_payments(sample_user.id)

        # Assert
        assert result["total"] == 1
        assert len(result["payments"]) == 1
        assert result["payments"][0]["status"] == PaymentStatus.SUCCESS.value

    def test_get_subscription_payments_no_subscription(self, sample_user):
        """Test payment history retrieval when user has no subscription."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None

        # Act
        result = self.use_case.get_subscription_payments(sample_user.id)

        # Assert
        assert result["total"] == 0
        assert result["payments"] == []


class TestSubscriptionModificationUseCase:
    """Test cases for SubscriptionModificationUseCase."""

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

    def test_upgrade_subscription_success(self, sample_user, sample_plan_config):
        """Test successful subscription upgrade."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="student",
            plan_name="STUDENT Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=49900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config
        self.mock_subscription_repo.save_subscription.return_value = mock_subscription

        # Act
        result = self.use_case.upgrade_subscription(
            user_id=sample_user.id,
            new_plan_id="PRO",
            new_billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert result["operation"] == "upgrade"
        assert result["old_plan"] == "student"
        assert result["new_plan"] == "pro"
        self.mock_user_repo.update_plan.assert_called_once_with(
            sample_user.id, UserPlan.PRO
        )

    def test_cancel_subscription_immediate(self, sample_user):
        """Test immediate subscription cancellation."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )
        self.mock_subscription_repo.update_subscription_status.return_value = (
            mock_subscription
        )

        # Act
        result = self.use_case.cancel_subscription(
            user_id=sample_user.id,
            immediate=True,
            reason="User request",
        )

        # Assert
        assert result["success"] is True
        assert "canceled" in result["message"]
        self.mock_user_repo.update_plan.assert_called_once_with(
            sample_user.id, UserPlan.FREE
        )
        self.mock_subscription_repo.update_subscription_status.assert_called_once()

    def test_cancel_subscription_period_end(self, sample_user):
        """Test subscription cancellation at period end."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )
        self.mock_subscription_repo.save_subscription.return_value = mock_subscription

        # Act
        result = self.use_case.cancel_subscription(
            user_id=sample_user.id,
            immediate=False,
            reason="User request",
        )

        # Assert
        assert result["success"] is True
        assert "scheduled for cancellation" in result["message"]
        # User plan should not be updated immediately for period-end
        # cancellation
        self.mock_user_repo.update_plan.assert_not_called()

    def test_cancel_subscription_not_found(self, sample_user):
        """Test cancellation when subscription not found."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="No active subscription found"):
            self.use_case.cancel_subscription(
                user_id=sample_user.id,
                immediate=True,
                reason="User request",
            )

    def test_cancel_subscription_not_active(self, sample_user):
        """Test cancellation when subscription is not active."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            amount_twd=99900,
            status=SubscriptionStatus.CANCELLED,
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            currency="TWD",
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )

        # Act & Assert
        with pytest.raises(DomainException, match="Subscription is not active"):
            self.use_case.cancel_subscription(
                user_id=sample_user.id,
                immediate=True,
                reason="User request",
            )

    def test_calculate_proration_success(self, sample_user, sample_plan_config):
        """Test successful proration calculation."""
        # Arrange
        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="student",
            plan_name="STUDENT Plan",
            billing_cycle="monthly",
            amount_twd=49900,  # 499 TWD
            status=SubscriptionStatus.ACTIVE,
            current_period_start=date(2024, 12, 1),
            current_period_end=date(2024, 12, 31),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            currency="TWD",
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = sample_plan_config

        # Act
        with patch(
            "src.coaching_assistant.core.services.subscription_management_use_case.datetime"
        ) as mock_datetime:
            mock_datetime.utcnow.return_value.date.return_value = date(2024, 12, 1)
            result = self.use_case.calculate_proration(
                user_id=sample_user.id,
                new_plan_id="PRO",
                new_billing_cycle="monthly",
            )

        # Assert
        assert "current_plan_remaining_value" in result
        assert "new_plan_prorated_cost" in result
        assert "net_charge" in result
        assert (
            result["new_plan_prorated_cost"]
            == sample_plan_config.monthly_price_twd_cents
        )

    def test_calculate_proration_no_subscription(self, sample_user):
        """Test proration calculation when user has no subscription."""
        # Arrange
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="No active subscription found"):
            self.use_case.calculate_proration(
                user_id=sample_user.id,
                new_plan_id="PRO",
                new_billing_cycle="monthly",
            )

    def test_downgrade_subscription_success(self, sample_user, sample_plan_config):
        """Test successful subscription downgrade."""
        # Arrange
        student_config = PlanConfiguration(
            id=2,
            plan_type=UserPlan.STUDENT,
            monthly_price_twd_cents=49900,  # 499 TWD
            annual_price_twd_cents=499900,  # 4999 TWD
        )

        mock_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="pro",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date.today(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.mock_subscription_repo.get_subscription_by_user_id.return_value = (
            mock_subscription
        )
        self.mock_plan_config_repo.get_by_plan_type.return_value = student_config
        self.mock_subscription_repo.save_subscription.return_value = mock_subscription

        # Act
        result = self.use_case.downgrade_subscription(
            user_id=sample_user.id,
            new_plan_id="STUDENT",
            new_billing_cycle="monthly",
        )

        # Assert
        assert result["success"] is True
        assert result["operation"] == "downgrade"
        assert result["old_plan"] == "pro"
        assert result["new_plan"] == "student"
        self.mock_user_repo.update_plan.assert_called_once_with(
            sample_user.id, UserPlan.STUDENT
        )
