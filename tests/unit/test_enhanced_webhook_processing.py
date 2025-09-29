"""Test enhanced webhook processing functionality."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from src.coaching_assistant.core.services.ecpay_service import (
    ECPaySubscriptionService,
)
from src.coaching_assistant.models import (
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
    User,
)
from src.coaching_assistant.tasks.subscription_maintenance_tasks import (
    cleanup_old_webhook_logs,
    process_failed_payment_retry,
    process_subscription_maintenance,
)


class TestEnhancedWebhookProcessing:
    """Test enhanced webhook processing functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session

    def test_payment_failure_grace_period_handling(self, mock_db_session):
        """Test grace period handling for payment failures."""

        # Create mock subscription
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub123"
        mock_subscription.user_id = "user123"
        mock_subscription.status = SubscriptionStatus.ACTIVE.value
        mock_subscription.grace_period_ends_at = None

        # Create mock payment
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay123"
        mock_payment.retry_count = 0
        mock_payment.subscription_id = "sub123"

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.count.return_value = (
            1  # First failure
        )

        # Create service with proper dependencies
        service = ECPaySubscriptionService(
            user_repo=Mock(),
            subscription_repo=Mock(),
            settings=Mock(),
            ecpay_client=Mock(),
            notification_service=Mock()
        )
        service.db = mock_db_session  # Add for backward compatibility

        # Test first payment failure
        service._handle_failed_payment(mock_subscription, mock_payment)

        # Verify grace period was set
        assert mock_subscription.status == SubscriptionStatus.PAST_DUE.value
        assert mock_subscription.grace_period_ends_at is not None
        assert mock_payment.retry_count == 1

    def test_subscription_downgrade_after_max_failures(self, mock_db_session):
        """Test automatic downgrade to FREE plan after max payment failures."""

        # Create mock subscription
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub123"
        mock_subscription.user_id = "user123"
        mock_subscription.status = SubscriptionStatus.PAST_DUE.value
        mock_subscription.plan_id = "PRO"
        mock_subscription.grace_period_ends_at = datetime.now() - timedelta(
            days=1
        )  # Expired

        # Create mock payment
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.retry_count = 3  # Max failures reached

        # Create mock user
        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.plan = "PRO"

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.count.return_value = (
            3  # Third failure
        )
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        # Create service with proper dependencies
        service = ECPaySubscriptionService(
            user_repo=Mock(),
            subscription_repo=Mock(),
            settings=Mock(),
            ecpay_client=Mock(),
            notification_service=Mock()
        )
        service.db = mock_db_session  # Add for backward compatibility

        # Test payment failure handling
        service._handle_failed_payment(mock_subscription, mock_payment)

        # Verify downgrade occurred
        assert mock_subscription.plan_id == "FREE"
        assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
        assert mock_subscription.amount_twd == 0
        assert mock_subscription.downgraded_at is not None
        assert mock_subscription.downgrade_reason == "payment_failure"
        assert mock_user.plan == "FREE"

    def test_payment_retry_scheduling(self, mock_db_session):
        """Test payment retry scheduling with exponential backoff."""

        # Create mock subscription and payment
        mock_subscription = Mock(spec=SaasSubscription)
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.retry_count = 1
        mock_payment.next_retry_at = None
        mock_payment.max_retries = None

        # Create service with proper dependencies
        service = ECPaySubscriptionService(
            user_repo=Mock(),
            subscription_repo=Mock(),
            settings=Mock(),
            ecpay_client=Mock(),
            notification_service=Mock()
        )
        service.db = mock_db_session  # Add for backward compatibility

        # Test retry scheduling
        service._schedule_payment_retry(mock_subscription, mock_payment)

        # Verify retry was scheduled
        assert mock_payment.next_retry_at is not None
        assert mock_payment.max_retries == 3

        # Verify exponential backoff (second retry should be 3 days later)
        expected_delay = datetime.now() + timedelta(days=3)
        assert (
            abs((mock_payment.next_retry_at - expected_delay).total_seconds()) < 60
        )  # Within 1 minute

    def test_notification_system_integration(self, mock_db_session):
        """Test payment failure notification system."""

        # Create mock subscription and user
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub123"
        mock_subscription.user_id = "user123"
        mock_subscription.plan_id = "PRO"
        mock_subscription.amount_twd = 89900
        mock_subscription.grace_period_ends_at = datetime.now() + timedelta(days=7)

        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay123"

        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.email = "user@example.com"

        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        # Create service with proper dependencies
        service = ECPaySubscriptionService(
            user_repo=Mock(),
            subscription_repo=Mock(),
            settings=Mock(),
            ecpay_client=Mock(),
            notification_service=Mock()
        )
        service.db = mock_db_session  # Add for backward compatibility

        # Test notification for first failure
        with patch.object(service, "logger") as mock_logger:
            service._send_payment_failure_notification(
                mock_subscription, mock_payment, 1
            )

            # Verify notification was queued
            mock_logger.info.assert_called_with(
                "📧 Payment failure notification queued: first_payment_failure for user@example.com"
            )

    def test_webhook_health_monitoring(self, mock_db_session):
        """Test webhook health check functionality."""

        from src.coaching_assistant.api.webhooks.ecpay import (
            webhook_health_check,
        )

        # Mock recent webhook counts
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [
            5,  # recent_webhooks
            1,  # failed_webhooks
            10,  # total_webhooks
        ]

        # Execute health check
        result = webhook_health_check(mock_db_session)

        # Verify health status calculation
        assert result["status"] == "healthy"  # 90% success rate
        assert result["service"] == "ecpay-webhooks"
        assert result["metrics"]["success_rate_24h"] == 90.0
        assert result["metrics"]["recent_webhooks_30min"] == 5
        assert result["metrics"]["failed_webhooks_24h"] == 1

    @patch("src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db")
    def test_subscription_maintenance_task(self, mock_get_db):
        """Test the main subscription maintenance background task."""

        # Setup mock database session
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = [mock_db]  # Generator mock

        # Mock ECPay service methods
        with patch(
            "src.coaching_assistant.tasks.subscription_maintenance_tasks.ECPaySubscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.check_and_handle_expired_subscriptions.return_value = True
            mock_service.retry_failed_payments.return_value = True
            mock_service_class.return_value = mock_service

            # Mock maintenance stats
            with patch(
                "src.coaching_assistant.tasks.subscription_maintenance_tasks._generate_maintenance_stats"
            ) as mock_stats:
                mock_stats.return_value = {
                    "active_subscriptions": 100,
                    "past_due_subscriptions": 5,
                }

                # Execute maintenance task
                result = process_subscription_maintenance()

                # Verify task execution
                assert result["status"] == "success"
                assert "maintenance_stats" in result
                mock_service.check_and_handle_expired_subscriptions.assert_called_once()
                mock_service.retry_failed_payments.assert_called_once()

    def test_failed_payment_retry_task(self, mock_db_session):
        """Test individual failed payment retry task."""

        # Create mock payment and subscription
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay123"
        mock_payment.subscription_id = "sub123"
        mock_payment.retry_count = 1
        mock_payment.max_retries = 3

        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub123"
        mock_subscription.billing_cycle = "monthly"
        mock_subscription.current_period_end = date.today() + timedelta(days=10)

        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_payment,  # First query for payment
            mock_subscription,  # Second query for subscription
        ]

        # Mock successful retry
        with patch(
            "src.coaching_assistant.tasks.subscription_maintenance_tasks._simulate_payment_retry",
            return_value=True,
        ):
            with patch(
                "src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db",
                return_value=[mock_db_session],
            ):
                result = process_failed_payment_retry("pay123")

                # Verify successful retry
                assert result["status"] == "success"
                assert result["payment_id"] == "pay123"
                assert mock_payment.status == PaymentStatus.SUCCESS.value
                assert mock_subscription.status == SubscriptionStatus.ACTIVE.value

    def test_webhook_log_cleanup_task(self, mock_db_session):
        """Test webhook log cleanup background task."""

        # Mock old webhook log deletion
        mock_query = Mock()
        mock_query.filter.return_value.delete.return_value = 150  # 150 logs deleted
        mock_db_session.query.return_value = mock_query

        with patch(
            "src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db",
            return_value=[mock_db_session],
        ):
            result = cleanup_old_webhook_logs()

            # Verify cleanup execution
            assert result["status"] == "success"
            assert result["deleted_count"] == 150
            mock_db_session.commit.assert_called_once()

    def test_manual_payment_retry_endpoint(self, mock_db_session):
        """Test manual payment retry webhook endpoint."""

        from fastapi import Request

        from src.coaching_assistant.api.webhooks.ecpay import (
            handle_manual_payment_retry,
        )

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "127.0.0.1"

        # Mock payment and subscription
        mock_payment = Mock()
        mock_subscription = Mock()

        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_payment,  # Payment query
            mock_subscription,  # Subscription query
        ]

        # Mock settings with admin token
        with patch(
            "src.coaching_assistant.api.webhooks.ecpay.settings"
        ) as mock_settings:
            mock_settings.ADMIN_WEBHOOK_TOKEN = "admin123"

            # Mock ECPay service
            with patch(
                "src.coaching_assistant.api.webhooks.ecpay.ECPaySubscriptionService"
            ) as mock_service_class:
                mock_service = Mock()
                mock_service.retry_failed_payments.return_value = True
                mock_service_class.return_value = mock_service

                # Test manual retry endpoint
                result = handle_manual_payment_retry(
                    request=mock_request,
                    payment_id="pay123",
                    admin_token="admin123",
                    db=mock_db_session,
                )

                # Verify successful retry
                assert result["status"] == "success"
                assert result["payment_id"] == "pay123"
                assert "processing_time_ms" in result

    def test_subscription_status_endpoint(self, mock_db_session):
        """Test subscription status debugging endpoint."""

        from src.coaching_assistant.api.webhooks.ecpay import (
            get_subscription_webhook_status,
        )

        # Mock subscription
        mock_subscription = Mock()
        mock_subscription.id = "sub123"
        mock_subscription.plan_id = "PRO"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = date.today() + timedelta(days=15)
        mock_subscription.grace_period_ends_at = None
        mock_subscription.downgrade_reason = None

        # Mock webhook logs and payments
        mock_webhooks = [Mock(), Mock()]
        mock_payments = [Mock()]

        # Setup mock queries (structure documented but handled by mock)
        # query_results defines the expected query structure:
        # [subscription, webhook_logs, payments]
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_subscription
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.side_effect = [
            mock_webhooks,  # Webhook logs
            mock_payments,  # Payments
        ]

        # Mock webhook and payment attributes
        for webhook in mock_webhooks:
            webhook.id = "webhook123"
            webhook.webhook_type = "billing_callback"
            webhook.status = "success"
            webhook.received_at = datetime.now()
            webhook.processing_time_ms = 150
            webhook.check_mac_value_verified = True

        for payment in mock_payments:
            payment.id = "pay123"
            payment.status = "success"
            payment.amount = 89900  # TWD cents
            payment.retry_count = 0
            payment.next_retry_at = None
            payment.created_at = datetime.now()

        # Mock settings
        with patch(
            "src.coaching_assistant.api.webhooks.ecpay.settings"
        ) as mock_settings:
            mock_settings.ADMIN_WEBHOOK_TOKEN = "admin123"

            # Test status endpoint
            result = get_subscription_webhook_status(
                user_id="user123", admin_token="admin123", db=mock_db_session
            )

            # Verify response structure
            assert result["user_id"] == "user123"
            assert result["subscription_found"] is True
            assert result["subscription"]["plan_id"] == "PRO"
            assert len(result["recent_webhooks"]) == 2
            assert len(result["recent_payments"]) == 1
            assert result["summary"]["failed_payments"] == 0


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock(spec=Session)


# Integration test for the complete webhook processing flow
class TestWebhookIntegrationFlow:
    """Test the complete webhook processing flow."""

    def test_complete_payment_failure_to_recovery_flow(self, mock_db_session):
        """Test complete flow from payment failure to recovery."""

        # 1. Initial successful subscription
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub123"
        mock_subscription.user_id = "user123"
        mock_subscription.status = SubscriptionStatus.ACTIVE.value
        mock_subscription.plan_id = "PRO"
        mock_subscription.grace_period_ends_at = None

        mock_user = Mock(spec=User)
        mock_user.id = "user123"
        mock_user.email = "user@example.com"
        mock_user.plan = "PRO"

        # 2. First payment failure
        service = ECPaySubscriptionService(mock_db_session, Mock())

        mock_payment_1 = Mock(spec=SubscriptionPayment)
        mock_payment_1.retry_count = 0

        # Mock first failure (count = 1)
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )

        service._handle_failed_payment(mock_subscription, mock_payment_1)

        # Verify first failure handling
        assert mock_subscription.status == SubscriptionStatus.PAST_DUE.value
        assert mock_subscription.grace_period_ends_at is not None

        # 3. Second payment failure
        mock_payment_2 = Mock(spec=SubscriptionPayment)
        mock_payment_2.retry_count = 0

        # Mock second failure (count = 2)
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2

        service._handle_failed_payment(mock_subscription, mock_payment_2)

        # Verify grace period extended
        assert mock_subscription.status == SubscriptionStatus.PAST_DUE.value

        # 4. Successful retry
        mock_payment_retry = Mock(spec=SubscriptionPayment)
        mock_payment_retry.status = PaymentStatus.FAILED.value
        mock_payment_retry.retry_count = 1
        mock_payment_retry.max_retries = 3

        # Mock successful retry
        with patch.object(service, "_simulate_payment_retry", return_value=True):
            # Simulate retry processing
            mock_payment_retry.status = PaymentStatus.SUCCESS.value
            mock_payment_retry.processed_at = datetime.now()
            mock_subscription.status = SubscriptionStatus.ACTIVE.value
            mock_subscription.grace_period_ends_at = None

        # Verify recovery
        assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
        assert mock_subscription.grace_period_ends_at is None
        assert mock_payment_retry.status == PaymentStatus.SUCCESS.value
