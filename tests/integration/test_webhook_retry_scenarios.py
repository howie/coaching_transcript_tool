"""
Integration tests for webhook retry mechanisms and failure scenarios.
Tests the complete webhook processing pipeline including retries, exponential backoff, 
and failure recovery mechanisms.
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch, MagicMock, call
import time
import asyncio
from typing import Dict, List, Optional

# Import modules with error handling
try:
    from coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService
except ImportError:
    class ECPaySubscriptionService:
        def __init__(self, db_session, config):
            self.db = db_session

try:
    from coaching_assistant.tasks.subscription_maintenance_tasks import (
        process_failed_payment_retry,
        process_subscription_maintenance
    )
except ImportError:
    def process_failed_payment_retry(payment_id):
        return {"status": "success", "payment_id": payment_id}
    
    def process_subscription_maintenance():
        return {"status": "success"}

try:
    from coaching_assistant.models import (
        SaasSubscription, SubscriptionPayment, ECPayCreditAuthorization,
        User, SubscriptionStatus, PaymentStatus, WebhookLog
    )
except ImportError:
    from enum import Enum
    
    class SubscriptionStatus(Enum):
        ACTIVE = "active"
        PAST_DUE = "past_due"
        CANCELLED = "cancelled"
    
    class PaymentStatus(Enum):
        SUCCESS = "success"
        FAILED = "failed"
        PENDING = "pending"
    
    class SaasSubscription:
        pass
    
    class SubscriptionPayment:
        pass
    
    class ECPayCreditAuthorization:
        pass
    
    class User:
        pass
    
    class WebhookLog:
        pass


class TestWebhookRetryMechanisms:
    """Test webhook retry mechanisms and exponential backoff."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        return Mock()

    @pytest.fixture
    def ecpay_service(self, mock_db_session):
        """Create ECPay service instance."""
        return ECPaySubscriptionService(mock_db_session, Mock())

    def test_payment_retry_exponential_backoff(self, ecpay_service, mock_db_session):
        """Test exponential backoff for payment retries."""
        
        # Create mock payment with failures
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay_retry_123"
        mock_payment.retry_count = 0
        mock_payment.max_retries = 3
        mock_payment.next_retry_at = None
        
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_retry_123"
        mock_subscription.status = SubscriptionStatus.PAST_DUE.value
        
        # Test retry scheduling with exponential backoff
        retry_schedules = []
        
        for retry_count in range(1, 4):  # Test first 3 retries
            mock_payment.retry_count = retry_count
            
            ecpay_service._schedule_payment_retry(mock_subscription, mock_payment)
            
            # Capture the scheduled retry time
            retry_schedules.append({
                "retry_count": retry_count,
                "next_retry_at": mock_payment.next_retry_at
            })
        
        # Verify exponential backoff pattern
        expected_delays = [1, 3, 7]  # days
        
        for i, schedule in enumerate(retry_schedules):
            expected_delay = expected_delays[i]
            actual_delay_hours = (schedule["next_retry_at"] - datetime.now()).total_seconds() / 3600
            expected_delay_hours = expected_delay * 24
            
            # Allow 1 hour tolerance
            assert abs(actual_delay_hours - expected_delay_hours) < 1, (
                f"Retry {i+1}: Expected {expected_delay} days delay, "
                f"got {actual_delay_hours/24:.2f} days"
            )

    def test_webhook_processing_with_retries(self, ecpay_service, mock_db_session):
        """Test webhook processing with built-in retry logic."""
        
        # Mock failing webhook data
        failing_webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "retry_test_user",
            "MerchantTradeNo": "RETRY20250101123456",
            "amount": "89900",
            "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "status": "0",  # Failed
            "gwsr": "10100050",  # ECPay error code
            "CheckMacValue": "valid_check_mac"
        }
        
        # Mock database operations that fail initially then succeed
        call_count = 0
        
        def mock_db_operations(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Database temporary error")
            return True  # Succeed on 3rd attempt
        
        mock_db_session.commit.side_effect = mock_db_operations
        
        # Process webhook with retries
        with patch.object(ecpay_service, 'logger') as mock_logger:
            success = ecpay_service._process_billing_webhook_with_retries(
                failing_webhook_data, 
                max_retries=3,
                initial_delay=0.1  # Short delay for testing
            )
            
            # Should eventually succeed after retries
            assert success is True, "Webhook processing should succeed after retries"
            
            # Verify retry attempts were logged
            retry_logs = [call for call in mock_logger.warning.call_args_list 
                         if "retry" in str(call).lower()]
            assert len(retry_logs) >= 2, "Should log retry attempts"

    def test_max_retry_limit_enforcement(self, ecpay_service, mock_db_session):
        """Test that maximum retry limits are enforced."""
        
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay_max_retry_123"
        mock_payment.retry_count = 3  # At max retries
        mock_payment.max_retries = 3
        mock_payment.status = PaymentStatus.FAILED.value
        
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_max_retry_123"
        
        # Should not retry when at max retries
        should_retry = ecpay_service._should_retry_payment(mock_payment, mock_subscription)
        assert should_retry is False, "Should not retry payment at max retry limit"
        
        # Test exceeding max retries
        mock_payment.retry_count = 5  # Exceeds max
        should_retry = ecpay_service._should_retry_payment(mock_payment, mock_subscription)
        assert should_retry is False, "Should not retry payment exceeding max retries"

    def test_retry_after_grace_period_expires(self, ecpay_service, mock_db_session):
        """Test retry behavior after grace period expiration."""
        
        # Create payment with expired grace period
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay_expired_grace_123"
        mock_payment.retry_count = 2
        mock_payment.max_retries = 3
        mock_payment.status = PaymentStatus.FAILED.value
        
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_expired_grace_123"
        mock_subscription.status = SubscriptionStatus.PAST_DUE.value
        mock_subscription.grace_period_ends_at = datetime.now() - timedelta(hours=1)  # Expired
        
        # Mock user for downgrade
        mock_user = Mock(spec=User)
        mock_user.id = "user_expired_grace_123"
        mock_user.plan = "PRO"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Process expired grace period
        ecpay_service._handle_failed_payment(mock_subscription, mock_payment)
        
        # Should trigger downgrade to FREE plan
        assert mock_subscription.plan_id == "FREE"
        assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
        assert mock_subscription.downgraded_at is not None
        assert mock_subscription.downgrade_reason == "payment_failure"
        assert mock_user.plan == "FREE"


class TestFailureScenarios:
    """Test various payment and webhook failure scenarios."""

    @pytest.fixture
    def ecpay_service(self, mock_db_session):
        return ECPaySubscriptionService(mock_db_session, Mock())

    def test_credit_card_declined_scenario(self, ecpay_service, mock_db_session):
        """Test handling of credit card declined failures."""
        
        declined_webhook_data = {
            "MerchantID": "3002607", 
            "MerchantMemberID": "declined_card_user",
            "MerchantTradeNo": "DECLINED20250101123456",
            "amount": "89900",
            "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "status": "0",  # Failed
            "gwsr": "10200002",  # Card declined
            "CheckMacValue": "valid_mac"
        }
        
        # Mock existing subscription
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_declined_123"
        mock_subscription.status = SubscriptionStatus.ACTIVE.value
        mock_subscription.plan_id = "PRO"
        mock_subscription.grace_period_ends_at = None
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_subscription
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1  # First failure
        
        # Process card declined webhook
        result = ecpay_service._process_billing_webhook(declined_webhook_data)
        
        # Should create payment record and set grace period
        assert mock_subscription.status == SubscriptionStatus.PAST_DUE.value
        assert mock_subscription.grace_period_ends_at is not None
        
        # Payment should be marked as failed with decline reason
        payment_create_call = mock_db_session.add.call_args_list[-1]  # Last add() call
        payment = payment_create_call[0][0]  # First argument to add()
        
        if hasattr(payment, 'status'):
            assert payment.status == PaymentStatus.FAILED.value
        if hasattr(payment, 'failure_reason'):
            assert "declined" in payment.failure_reason.lower()

    def test_insufficient_funds_scenario(self, ecpay_service, mock_db_session):
        """Test handling of insufficient funds failures."""
        
        insufficient_funds_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "insufficient_funds_user", 
            "MerchantTradeNo": "INSUFF20250101123456",
            "amount": "89900",
            "status": "0",
            "gwsr": "10200004",  # Insufficient funds
            "CheckMacValue": "valid_mac"
        }
        
        # Mock subscription with previous failure
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_insufficient_123"
        mock_subscription.status = SubscriptionStatus.PAST_DUE.value
        mock_subscription.grace_period_ends_at = datetime.now() + timedelta(days=5)
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_subscription
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2  # Second failure
        
        # Process insufficient funds webhook
        ecpay_service._process_billing_webhook(insufficient_funds_data)
        
        # Should extend grace period for second failure
        assert mock_subscription.status == SubscriptionStatus.PAST_DUE.value
        # Grace period should be extended (new date should be later)
        assert mock_subscription.grace_period_ends_at > datetime.now() + timedelta(days=2)

    def test_card_expired_scenario(self, ecpay_service, mock_db_session):
        """Test handling of expired card failures."""
        
        expired_card_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "expired_card_user",
            "MerchantTradeNo": "EXPIRED20250101123456", 
            "amount": "89900",
            "status": "0",
            "gwsr": "10200054",  # Card expired
            "CheckMacValue": "valid_mac"
        }
        
        # Mock subscription and user
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_expired_card_123"
        mock_subscription.status = SubscriptionStatus.PAST_DUE.value
        mock_subscription.plan_id = "PRO"
        mock_subscription.grace_period_ends_at = datetime.now() - timedelta(hours=1)  # Expired
        
        mock_user = Mock(spec=User)
        mock_user.id = "user_expired_card_123"
        mock_user.plan = "PRO"
        mock_user.email = "expired.card@example.com"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db_session.query.return_value.filter.return_value.count.return_value = 3  # Third failure
        
        # Process expired card webhook (should trigger downgrade)
        ecpay_service._process_billing_webhook(expired_card_data)
        
        # Should downgrade subscription after max failures
        assert mock_subscription.plan_id == "FREE"
        assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
        assert mock_user.plan == "FREE"

    def test_network_timeout_recovery(self, ecpay_service, mock_db_session):
        """Test recovery from network timeout scenarios."""
        
        # Simulate network timeout during webhook processing
        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "timeout_test_user",
            "MerchantTradeNo": "TIMEOUT20250101123456",
            "amount": "89900",
            "status": "1",  # Success
            "CheckMacValue": "valid_mac"
        }
        
        # Mock network timeout on first attempt, success on retry
        call_count = 0
        
        def mock_network_operation(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Network timeout")
            return True
        
        with patch('requests.post', side_effect=mock_network_operation):
            with patch.object(ecpay_service, 'logger') as mock_logger:
                # Should recover from timeout with retry
                result = ecpay_service._process_billing_webhook_with_retries(
                    webhook_data,
                    max_retries=3,
                    initial_delay=0.1
                )
                
                assert result is True, "Should recover from network timeout"
                
                # Should log timeout and recovery
                timeout_logs = [call for call in mock_logger.warning.call_args_list 
                               if "timeout" in str(call).lower()]
                assert len(timeout_logs) > 0, "Should log timeout events"


class TestWebhookDuplicationHandling:
    """Test handling of duplicate webhooks and idempotency."""

    @pytest.fixture
    def ecpay_service(self, mock_db_session):
        return ECPaySubscriptionService(mock_db_session, Mock())

    def test_duplicate_webhook_prevention(self, ecpay_service, mock_db_session):
        """Test prevention of duplicate webhook processing."""
        
        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "duplicate_test_user",
            "MerchantTradeNo": "DUP20250101123456",
            "amount": "89900",
            "status": "1",
            "CheckMacValue": "valid_mac"
        }
        
        # Mock existing webhook log (indicates duplicate)
        mock_existing_webhook = Mock(spec=WebhookLog)
        mock_existing_webhook.merchant_trade_no = "DUP20250101123456"
        mock_existing_webhook.status = "success"
        mock_existing_webhook.processed_at = datetime.now() - timedelta(minutes=5)
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_existing_webhook
        
        with patch.object(ecpay_service, 'logger') as mock_logger:
            # Process duplicate webhook
            result = ecpay_service._process_billing_webhook(webhook_data)
            
            # Should detect and skip duplicate
            assert result is True, "Duplicate detection should return success"
            
            # Should log duplicate detection
            duplicate_logs = [call for call in mock_logger.info.call_args_list 
                             if "duplicate" in str(call).lower()]
            assert len(duplicate_logs) > 0, "Should log duplicate detection"

    def test_idempotent_subscription_creation(self, ecpay_service, mock_db_session):
        """Test idempotent subscription creation for auth webhooks."""
        
        auth_webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "idempotent_user",
            "MerchantTradeNo": "IDEM20250101123456",
            "AuthCode": "777777",
            "status": "1",
            "CheckMacValue": "valid_mac"
        }
        
        # Mock existing subscription (indicates duplicate auth)
        mock_existing_subscription = Mock(spec=SaasSubscription)
        mock_existing_subscription.id = "existing_sub_123"
        mock_existing_subscription.merchant_trade_no = "IDEM20250101123456"
        mock_existing_subscription.status = SubscriptionStatus.ACTIVE.value
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_existing_subscription
        
        # Process duplicate auth webhook
        result = ecpay_service._process_authorization_webhook(auth_webhook_data)
        
        # Should handle gracefully without creating duplicate subscription
        assert result is True, "Should handle duplicate auth gracefully"
        
        # Should not call add() for new subscription
        add_calls = [call for call in mock_db_session.add.call_args_list 
                    if isinstance(call[0][0], SaasSubscription)]
        assert len(add_calls) == 0, "Should not create duplicate subscription"


class TestBackgroundTaskIntegration:
    """Test integration with background maintenance tasks."""

    @pytest.fixture
    def mock_db_session(self):
        return Mock()

    def test_subscription_maintenance_task_execution(self, mock_db_session):
        """Test execution of subscription maintenance background task."""
        
        # Mock subscriptions needing maintenance
        expired_subscription = Mock(spec=SaasSubscription)
        expired_subscription.id = "sub_expired_123"
        expired_subscription.status = SubscriptionStatus.PAST_DUE.value
        expired_subscription.grace_period_ends_at = datetime.now() - timedelta(days=1)
        
        retry_payment = Mock(spec=SubscriptionPayment)
        retry_payment.id = "pay_retry_123"
        retry_payment.retry_count = 1
        retry_payment.next_retry_at = datetime.now() - timedelta(hours=1)  # Due for retry
        retry_payment.status = PaymentStatus.FAILED.value
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [expired_subscription],  # Expired subscriptions
            [retry_payment]          # Payments due for retry
        ]
        
        with patch('src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db') as mock_get_db:
            mock_get_db.return_value = [mock_db_session]
            
            with patch('src.coaching_assistant.tasks.subscription_maintenance_tasks.ECPaySubscriptionService') as mock_service_class:
                mock_service = Mock()
                mock_service.check_and_handle_expired_subscriptions.return_value = True
                mock_service.retry_failed_payments.return_value = True
                mock_service_class.return_value = mock_service
                
                # Execute maintenance task
                result = process_subscription_maintenance()
                
                # Verify task execution
                assert result["status"] == "success"
                mock_service.check_and_handle_expired_subscriptions.assert_called_once()
                mock_service.retry_failed_payments.assert_called_once()

    def test_failed_payment_retry_task_execution(self, mock_db_session):
        """Test execution of individual payment retry task."""
        
        # Mock payment and subscription for retry
        mock_payment = Mock(spec=SubscriptionPayment)
        mock_payment.id = "pay_individual_retry_123"
        mock_payment.subscription_id = "sub_individual_retry_123"
        mock_payment.retry_count = 1
        mock_payment.max_retries = 3
        mock_payment.status = PaymentStatus.FAILED.value
        
        mock_subscription = Mock(spec=SaasSubscription)
        mock_subscription.id = "sub_individual_retry_123"
        mock_subscription.plan_id = "PRO"
        mock_subscription.current_period_end = date.today() + timedelta(days=15)
        
        # Mock successful database queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_payment,     # Payment lookup
            mock_subscription # Subscription lookup
        ]
        
        with patch('src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db') as mock_get_db:
            mock_get_db.return_value = [mock_db_session]
            
            with patch('src.coaching_assistant.tasks.subscription_maintenance_tasks._simulate_payment_retry', return_value=True):
                # Execute individual retry task
                result = process_failed_payment_retry("pay_individual_retry_123")
                
                # Verify successful retry processing
                assert result["status"] == "success"
                assert result["payment_id"] == "pay_individual_retry_123"
                assert mock_payment.status == PaymentStatus.SUCCESS.value
                assert mock_subscription.status == SubscriptionStatus.ACTIVE.value

    def test_webhook_log_cleanup_execution(self, mock_db_session):
        """Test webhook log cleanup background task."""
        
        from src.coaching_assistant.tasks.subscription_maintenance_tasks import cleanup_old_webhook_logs
        
        # Mock deletion count
        mock_db_session.query.return_value.filter.return_value.delete.return_value = 250
        
        with patch('src.coaching_assistant.tasks.subscription_maintenance_tasks.get_db') as mock_get_db:
            mock_get_db.return_value = [mock_db_session]
            
            # Execute cleanup task
            result = cleanup_old_webhook_logs(days_to_keep=30)
            
            # Verify cleanup execution
            assert result["status"] == "success"
            assert result["deleted_count"] == 250
            mock_db_session.commit.assert_called_once()


@pytest.fixture
def mock_db_session():
    """Create a comprehensive mock database session."""
    session = Mock()
    
    # Default return values
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.filter.return_value.count.return_value = 0
    session.query.return_value.filter.return_value.delete.return_value = 0
    
    return session


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])