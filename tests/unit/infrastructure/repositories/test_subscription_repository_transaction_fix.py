"""Unit tests for subscription repository transaction management fix."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.coaching_assistant.infrastructure.db.repositories.subscription_repository import (
    SubscriptionRepository,
)
from src.coaching_assistant.models.ecpay_subscription import (
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)


class TestSubscriptionRepositoryTransactionFix:
    """Test that subscription repository properly manages transactions."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        session.get.return_value = None  # Ensure save_subscription takes the add path
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create subscription repository with mock session."""
        return SubscriptionRepository(mock_session)

    @pytest.fixture
    def sample_subscription(self):
        """Create a sample subscription."""
        return SaasSubscription(
            id=uuid4(),
            user_id=uuid4(),
            plan_id="PRO",
            plan_name="Pro Plan",
            billing_cycle="monthly",
            amount_twd=500,
            status=SubscriptionStatus.ACTIVE.value,
        )

    @pytest.fixture
    def sample_authorization(self):
        """Create a sample credit authorization."""
        return ECPayCreditAuthorization(
            id=uuid4(),
            user_id=uuid4(),
            merchant_member_id="MEMBER_123",
            auth_amount=100,
            period_type="Month",
            frequency=1,
        )

    @pytest.fixture
    def sample_payment(self):
        """Create a sample payment."""
        return SubscriptionPayment(
            id=uuid4(),
            subscription_id=uuid4(),
            gwsr="TEST123",
            amount=500,
            status="completed",
        )

    def test_save_subscription_no_commit(
        self, repository, mock_session, sample_subscription
    ):
        """Test that save_subscription uses flush instead of commit."""
        # Act
        result = repository.save_subscription(sample_subscription)

        # Assert - check that add was called with an ORM model (not the domain model)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
        # Result should be the domain model converted back from ORM
        assert result.user_id == sample_subscription.user_id
        assert result.plan_id == sample_subscription.plan_id

    def test_save_credit_authorization_no_commit(
        self, repository, mock_session, sample_authorization
    ):
        """Test that save_credit_authorization uses flush instead of commit."""
        # Act
        result = repository.save_credit_authorization(sample_authorization)

        # Assert - check that add was called with an ORM model (not the domain model)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
        # Result should be the domain model converted back from ORM
        assert result.user_id == sample_authorization.user_id
        assert result.merchant_member_id == sample_authorization.merchant_member_id

    def test_save_payment_no_commit(self, repository, mock_session, sample_payment):
        """Test that save_payment uses flush instead of commit."""
        # Act
        result = repository.save_payment(sample_payment)

        # Assert - check that add was called with an ORM model (not the domain model)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
        # Result should be the domain model converted back from ORM
        assert result.gwsr == sample_payment.gwsr
        assert result.amount == sample_payment.amount

    def test_update_subscription_status_no_commit(
        self, repository, mock_session, sample_subscription
    ):
        """Test that update_subscription_status uses flush instead of commit."""
        # Arrange
        mock_orm_subscription = Mock()
        # Create updated subscription with cancelled status
        updated_subscription = SaasSubscription(
            id=sample_subscription.id,
            user_id=sample_subscription.user_id,
            plan_id=sample_subscription.plan_id,
            plan_name=sample_subscription.plan_name,
            billing_cycle=sample_subscription.billing_cycle,
            amount_twd=sample_subscription.amount_twd,
            status=SubscriptionStatus.CANCELLED.value,
        )
        mock_orm_subscription.to_domain.return_value = updated_subscription
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = mock_orm_subscription

        # Act
        result = repository.update_subscription_status(
            sample_subscription.id, SubscriptionStatus.CANCELLED
        )

        # Assert
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()
        assert result.status == SubscriptionStatus.CANCELLED.value
        assert result.id == sample_subscription.id

    def test_update_subscription_status_not_found(self, repository, mock_session):
        """Test that update_subscription_status raises error when subscription not found."""
        # Arrange
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.first.return_value = None
        subscription_id = uuid4()

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Subscription not found: {subscription_id}"
        ):
            repository.update_subscription_status(
                subscription_id, SubscriptionStatus.CANCELLED
            )

        # Verify no transaction operations were called
        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_get_subscription_by_user_id_no_transaction_operations(
        self, repository, mock_session
    ):
        """Test that read operations don't call any transaction methods."""
        # Act
        repository.get_subscription_by_user_id(uuid4())

        # Assert
        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    def test_get_credit_authorization_by_user_id_no_transaction_operations(
        self, repository, mock_session
    ):
        """Test that read operations don't call any transaction methods."""
        # Act
        repository.get_credit_authorization_by_user_id(uuid4())

        # Assert
        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    def test_get_payments_for_subscription_no_transaction_operations(
        self, repository, mock_session
    ):
        """Test that read operations don't call any transaction methods."""
        # Act
        repository.get_payments_for_subscription(uuid4())

        # Assert
        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.refresh.assert_not_called()

    def test_repository_session_exception_handling(self, mock_session):
        """Test that repository handles session exceptions without committing."""
        # Arrange
        mock_session.flush.side_effect = Exception("Database error")
        repository = SubscriptionRepository(mock_session)
        sample_subscription = SaasSubscription(
            id=uuid4(),
            user_id=uuid4(),
            plan_id="PRO",
            plan_name="Pro Plan",
            billing_cycle="monthly",
            amount_twd=500,
            status=SubscriptionStatus.ACTIVE.value,
        )

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            repository.save_subscription(sample_subscription)

        # Verify commit was never called even when flush fails
        mock_session.commit.assert_not_called()
