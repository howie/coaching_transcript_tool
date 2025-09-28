"""Integration tests for subscription repository."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from src.coaching_assistant.infrastructure.db.repositories.subscription_repository import (
    SubscriptionRepository,
)
from src.coaching_assistant.models.ecpay_subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)


@pytest.mark.integration
class TestSubscriptionRepositoryIntegration:
    """Integration tests for SubscriptionRepository with real database."""

    def test_save_and_get_subscription(self, db_session, sample_user):
        """Test saving and retrieving a subscription."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE.value,
            amount_twd=99900,
            currency="TWD",
            current_period_start=date.today(),
            current_period_end=date(2024, 12, 31),
            created_at=datetime.utcnow(),
        )

        # Act
        saved_subscription = repo.save_subscription(subscription)
        db_session.commit()

        # Assert
        assert saved_subscription.id is not None

        # Retrieve and verify
        retrieved_subscription = repo.get_subscription_by_user_id(sample_user.id)
        assert retrieved_subscription is not None
        assert retrieved_subscription.user_id == sample_user.id
        assert retrieved_subscription.plan_id == "PRO"
        assert retrieved_subscription.billing_cycle == "monthly"

    def test_save_and_get_credit_authorization(self, db_session, sample_user):
        """Test saving and retrieving credit authorization."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_{sample_user.id}",
            auth_amount=100,
            period_type="Month",
            frequency=1,
            period_amount=99900,
            auth_status=ECPayAuthStatus.ACTIVE.value,
            created_at=datetime.utcnow(),
        )

        # Act
        saved_auth = repo.save_credit_authorization(auth)
        db_session.commit()

        # Assert
        assert saved_auth.id is not None

        # Retrieve and verify
        retrieved_auth = repo.get_credit_authorization_by_user_id(sample_user.id)
        assert retrieved_auth is not None
        assert retrieved_auth.user_id == sample_user.id
        assert retrieved_auth.merchant_member_id == f"MEMBER_{sample_user.id}"
        assert retrieved_auth.auth_status == ECPayAuthStatus.ACTIVE.value

    def test_save_and_get_subscription_payments(self, db_session, sample_user):
        """Test saving and retrieving subscription payments."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # First create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            plan_name="PRO Plan",
            billing_cycle="monthly",
            status=SubscriptionStatus.ACTIVE.value,
            amount_twd=99900,
            currency="TWD",
            created_at=datetime.utcnow(),
        )
        saved_subscription = repo.save_subscription(subscription)
        db_session.commit()

        # Create payment
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=saved_subscription.id,
            amount_twd=99900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            payment_date=datetime.utcnow(),
            ecpay_trade_no="TEST_TRADE_123",
            created_at=datetime.utcnow(),
        )

        # Act
        saved_payment = repo.save_payment(payment)
        db_session.commit()

        # Assert
        assert saved_payment.id is not None

        # Retrieve and verify
        payments = repo.get_payments_for_subscription(saved_subscription.id)
        assert len(payments) == 1
        assert payments[0].subscription_id == saved_subscription.id
        assert payments[0].amount_twd == 99900
        assert payments[0].status == PaymentStatus.SUCCESS.value

    def test_update_subscription_status(self, db_session, sample_user):
        """Test updating subscription status."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            status=SubscriptionStatus.ACTIVE.value,
            created_at=datetime.utcnow(),
        )
        saved_subscription = repo.save_subscription(subscription)
        db_session.commit()

        # Act
        updated_subscription = repo.update_subscription_status(
            saved_subscription.id, SubscriptionStatus.CANCELLED
        )
        db_session.commit()

        # Assert
        assert updated_subscription.status == SubscriptionStatus.CANCELLED.value

        # Verify in database
        retrieved_subscription = repo.get_subscription_by_user_id(sample_user.id)
        # Should not return cancelled subscription in normal query
        assert (
            retrieved_subscription is None
            or retrieved_subscription.status != SubscriptionStatus.ACTIVE.value
        )

    def test_get_subscription_by_user_id_filters_status(self, db_session, sample_user):
        """Test that get_subscription_by_user_id only returns active-like subscriptions."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # Create cancelled subscription
        cancelled_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            status=SubscriptionStatus.CANCELLED.value,
            created_at=datetime.utcnow(),
        )
        repo.save_subscription(cancelled_subscription)

        # Create active subscription
        active_subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            status=SubscriptionStatus.ACTIVE.value,
            created_at=datetime.utcnow(),
        )
        repo.save_subscription(active_subscription)
        db_session.commit()

        # Act
        retrieved_subscription = repo.get_subscription_by_user_id(sample_user.id)

        # Assert - should get active subscription, not cancelled one
        assert retrieved_subscription is not None
        assert retrieved_subscription.status == SubscriptionStatus.ACTIVE.value
        assert retrieved_subscription.id == active_subscription.id

    def test_database_error_handling(self, db_session):
        """Test database error handling."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # Act & Assert - should handle non-existent user gracefully
        result = repo.get_subscription_by_user_id(uuid4())
        assert result is None

        # Test with non-existent subscription ID
        with pytest.raises(ValueError, match="Subscription not found"):
            repo.update_subscription_status(uuid4(), SubscriptionStatus.CANCELLED)

    def test_session_state_validation(self, db_session, sample_user):
        """Test session state validation."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # Close session to simulate inactive state
        db_session.close()

        # Act - should handle inactive session gracefully
        result = repo.get_subscription_by_user_id(sample_user.id)

        # Assert - should return None instead of raising error
        assert result is None

    def test_multiple_authorizations_returns_latest(self, db_session, sample_user):
        """Test that get_credit_authorization_by_user_id returns latest authorization."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # Create older authorization
        older_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_OLD_{sample_user.id}",
            auth_status=ECPayAuthStatus.EXPIRED.value,
            created_at=datetime(2023, 1, 1),
        )
        repo.save_credit_authorization(older_auth)

        # Create newer authorization
        newer_auth = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=sample_user.id,
            merchant_member_id=f"MEMBER_NEW_{sample_user.id}",
            auth_status=ECPayAuthStatus.ACTIVE.value,
            created_at=datetime.utcnow(),
        )
        repo.save_credit_authorization(newer_auth)
        db_session.commit()

        # Act
        retrieved_auth = repo.get_credit_authorization_by_user_id(sample_user.id)

        # Assert - should get the newer authorization
        assert retrieved_auth is not None
        assert retrieved_auth.id == newer_auth.id
        assert "NEW" in retrieved_auth.merchant_member_id

    def test_payments_ordered_by_created_at_desc(self, db_session, sample_user):
        """Test that payments are returned in descending order by created_at."""
        # Arrange
        repo = SubscriptionRepository(db_session)

        # Create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=sample_user.id,
            plan_id="PRO",
            status=SubscriptionStatus.ACTIVE.value,
            created_at=datetime.utcnow(),
        )
        saved_subscription = repo.save_subscription(subscription)

        # Create payments with different timestamps
        payment1 = SubscriptionPayment(
            id=uuid4(),
            subscription_id=saved_subscription.id,
            amount_twd=99900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            ecpay_trade_no="TRADE_001",
            created_at=datetime(2023, 1, 1),
        )

        payment2 = SubscriptionPayment(
            id=uuid4(),
            subscription_id=saved_subscription.id,
            amount_twd=99900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            ecpay_trade_no="TRADE_002",
            created_at=datetime.utcnow(),
        )

        repo.save_payment(payment1)
        repo.save_payment(payment2)
        db_session.commit()

        # Act
        payments = repo.get_payments_for_subscription(saved_subscription.id)

        # Assert - newer payment should be first
        assert len(payments) == 2
        assert payments[0].ecpay_trade_no == "TRADE_002"  # Newer payment first
        assert payments[1].ecpay_trade_no == "TRADE_001"  # Older payment second
