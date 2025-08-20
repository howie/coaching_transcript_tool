"""Tests for ECPay webhook processing functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models import (
    User, ECPayCreditAuthorization, SaasSubscription, 
    SubscriptionPayment, WebhookLog, ECPayAuthStatus, 
    SubscriptionStatus, PaymentStatus, WebhookStatus
)
from coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService


class TestWebhookProcessing:
    """Test webhook processing functionality."""
    
    def test_authorization_callback_success(self, db_session: Session, test_client: TestClient):
        """Test successful authorization callback processing."""
        
        # Create test user and auth record
        user = User(email="test@example.com", plan="FREE")
        db_session.add(user)
        db_session.flush()
        
        auth_record = ECPayCreditAuthorization(
            user_id=user.id,
            merchant_member_id="USER12345678901234567890",
            auth_amount=89900,
            period_type="M",
            period_amount=89900,
            description="Test authorization",
            auth_status=ECPayAuthStatus.PENDING.value
        )
        db_session.add(auth_record)
        db_session.commit()
        
        # Mock callback data
        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": auth_record.merchant_member_id,
            "RtnCode": "1",
            "RtnMsg": "Success",
            "AuthCode": "123456",
            "card4no": "1234",
            "card6no": "VISA",
            "CheckMacValue": "TEST_MAC_VALUE"
        }
        
        # Mock ECPay service to return True for verification
        with patch.object(ECPaySubscriptionService, '_verify_callback', return_value=True):
            response = test_client.post(
                "/api/webhooks/ecpay-auth",
                data=callback_data
            )
        
        assert response.status_code == 200
        assert response.text == "1|OK"
        
        # Verify webhook log was created
        webhook_log = db_session.query(WebhookLog).filter(
            WebhookLog.webhook_type == "auth_callback",
            WebhookLog.merchant_member_id == auth_record.merchant_member_id
        ).first()
        
        assert webhook_log is not None
        assert webhook_log.status == WebhookStatus.SUCCESS.value
        assert webhook_log.check_mac_value_verified is True
        assert webhook_log.user_id == user.id
        
        # Verify authorization was updated
        db_session.refresh(auth_record)
        assert auth_record.auth_status == ECPayAuthStatus.ACTIVE.value
        assert auth_record.auth_code == "123456"
        assert auth_record.card_last4 == "1234"
        assert auth_record.card_brand == "VISA"
        
        # Verify subscription was created
        subscription = db_session.query(SaasSubscription).filter(
            SaasSubscription.auth_id == auth_record.id
        ).first()
        
        assert subscription is not None
        assert subscription.user_id == user.id
        assert subscription.status == SubscriptionStatus.ACTIVE.value
    
    def test_authorization_callback_verification_failed(self, db_session: Session, test_client: TestClient):
        """Test authorization callback with CheckMacValue verification failure."""
        
        user = User(email="test@example.com", plan="FREE")
        db_session.add(user)
        db_session.flush()
        
        auth_record = ECPayCreditAuthorization(
            user_id=user.id,
            merchant_member_id="USER12345678901234567890",
            auth_amount=89900,
            period_type="M",
            period_amount=89900,
            description="Test authorization",
            auth_status=ECPayAuthStatus.PENDING.value
        )
        db_session.add(auth_record)
        db_session.commit()
        
        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": auth_record.merchant_member_id,
            "RtnCode": "1",
            "RtnMsg": "Success",
            "CheckMacValue": "INVALID_MAC_VALUE"
        }
        
        # Mock ECPay service to return False for verification
        with patch.object(ECPaySubscriptionService, '_verify_callback', return_value=False):
            response = test_client.post(
                "/api/webhooks/ecpay-auth",
                data=callback_data
            )
        
        assert response.status_code == 200
        assert response.text == "0|Security Verification Failed"
        
        # Verify webhook log shows verification failure
        webhook_log = db_session.query(WebhookLog).filter(
            WebhookLog.webhook_type == "auth_callback",
            WebhookLog.merchant_member_id == auth_record.merchant_member_id
        ).first()
        
        assert webhook_log is not None
        assert webhook_log.status == WebhookStatus.FAILED.value
        assert webhook_log.check_mac_value_verified is False
        assert "CheckMacValue verification failed" in webhook_log.error_message
    
    def test_billing_callback_success(self, db_session: Session, test_client: TestClient):
        """Test successful billing callback processing."""
        
        # Create test data
        user = User(email="test@example.com", plan="PRO")
        db_session.add(user)
        db_session.flush()
        
        auth_record = ECPayCreditAuthorization(
            user_id=user.id,
            merchant_member_id="USER12345678901234567890",
            auth_amount=89900,
            period_type="M",
            period_amount=89900,
            auth_status=ECPayAuthStatus.ACTIVE.value
        )
        db_session.add(auth_record)
        db_session.flush()
        
        subscription = SaasSubscription(
            user_id=user.id,
            auth_id=auth_record.id,
            plan_id="PRO",
            plan_name="專業方案",
            billing_cycle="monthly",
            amount_twd=89900,
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=datetime.now().date(),
            current_period_end=(datetime.now() + timedelta(days=30)).date()
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Mock billing webhook data
        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": auth_record.merchant_member_id,
            "gwsr": "TEST_GWSR_123456",
            "amount": "899",
            "process_date": "2025/08/20 19:00:00",
            "auth_code": "123456",
            "RtnCode": "1",
            "RtnMsg": "Success",
            "CheckMacValue": "TEST_MAC_VALUE"
        }
        
        # Mock notification methods
        with patch.object(ECPaySubscriptionService, '_verify_callback', return_value=True), \
             patch.object(ECPaySubscriptionService, '_handle_payment_success_notifications') as mock_success_notif:
            
            response = test_client.post(
                "/api/webhooks/ecpay-billing",
                data=webhook_data
            )
        
        assert response.status_code == 200
        assert response.text == "1|OK"
        
        # Verify webhook log was created
        webhook_log = db_session.query(WebhookLog).filter(
            WebhookLog.webhook_type == "billing_callback",
            WebhookLog.gwsr == "TEST_GWSR_123456"
        ).first()
        
        assert webhook_log is not None
        assert webhook_log.status == WebhookStatus.SUCCESS.value
        assert webhook_log.user_id == user.id
        assert webhook_log.subscription_id == subscription.id
        
        # Verify payment record was created
        payment = db_session.query(SubscriptionPayment).filter(
            SubscriptionPayment.gwsr == "TEST_GWSR_123456"
        ).first()
        
        assert payment is not None
        assert payment.status == PaymentStatus.SUCCESS.value
        assert payment.amount == 89900  # Amount in cents
        
        # Verify notifications were sent
        mock_success_notif.assert_called_once()
    
    def test_webhook_health_check(self, db_session: Session, test_client: TestClient):
        """Test webhook health check endpoint."""
        
        # Create some test webhook logs
        webhook_log1 = WebhookLog(
            webhook_type="auth_callback",
            status=WebhookStatus.SUCCESS.value,
            received_at=datetime.utcnow() - timedelta(minutes=10)
        )
        webhook_log2 = WebhookLog(
            webhook_type="billing_callback",
            status=WebhookStatus.FAILED.value,
            received_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        db_session.add_all([webhook_log1, webhook_log2])
        db_session.commit()
        
        response = test_client.get("/api/webhooks/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "ecpay-webhooks"
        assert "status" in data
        assert "metrics" in data
        assert "recent_webhooks_30min" in data["metrics"]
        assert "success_rate_24h" in data["metrics"]
    
    def test_webhook_statistics(self, db_session: Session, test_client: TestClient):
        """Test webhook statistics endpoint."""
        
        # Create test webhook logs with different types and statuses
        webhook_logs = [
            WebhookLog(
                webhook_type="auth_callback",
                status=WebhookStatus.SUCCESS.value,
                received_at=datetime.utcnow() - timedelta(hours=1)
            ),
            WebhookLog(
                webhook_type="auth_callback",
                status=WebhookStatus.FAILED.value,
                received_at=datetime.utcnow() - timedelta(hours=2)
            ),
            WebhookLog(
                webhook_type="billing_callback",
                status=WebhookStatus.SUCCESS.value,
                received_at=datetime.utcnow() - timedelta(hours=3)
            ),
            WebhookLog(
                webhook_type="billing_callback",
                status=WebhookStatus.SUCCESS.value,
                received_at=datetime.utcnow() - timedelta(hours=4)
            )
        ]
        
        db_session.add_all(webhook_logs)
        db_session.commit()
        
        response = test_client.get("/api/webhooks/webhook-stats?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period_hours"] == 24
        assert "webhook_types" in data
        
        # Verify auth_callback stats
        auth_stats = data["webhook_types"]["auth_callback"]
        assert auth_stats["total"] == 2
        assert auth_stats["success"] == 1
        assert auth_stats["failed"] == 1
        assert auth_stats["success_rate"] == 50.0
        
        # Verify billing_callback stats
        billing_stats = data["webhook_types"]["billing_callback"]
        assert billing_stats["total"] == 2
        assert billing_stats["success"] == 2
        assert billing_stats["failed"] == 0
        assert billing_stats["success_rate"] == 100.0


# Test fixtures would be defined in conftest.py
# These are placeholder implementations

@pytest.fixture
def db_session():
    """Mock database session."""
    return MagicMock()

@pytest.fixture
def test_client():
    """Mock test client."""
    return MagicMock()