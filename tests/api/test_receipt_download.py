"""
API Integration Tests for Receipt Download Functionality

Tests the /api/v1/subscriptions/payment/{payment_id}/receipt endpoint
"""

import pytest
from datetime import datetime, date
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models import User, SaasSubscription, SubscriptionPayment, ECPayCreditAuthorization
from coaching_assistant.models.ecpay_subscription import PaymentStatus, SubscriptionStatus


class TestReceiptDownloadAPI:
    """Test receipt download API endpoint."""
    
    def test_generate_receipt_success(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test successful receipt generation for valid payment."""
        
        # Create authorization record
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=299900,  # $2999.00 in cents
            period_type="Y",
            exec_times=0,
            frequency=1,
            status="active"
        )
        test_db.add(auth_record)
        test_db.flush()
        
        # Create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=test_user.id,
            auth_id=auth_record.id,
            plan_id="ENTERPRISE",
            plan_name="企業方案",
            billing_cycle="annual",
            amount_twd=299900,
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=date.today(),
            current_period_end=date.today()
        )
        test_db.add(subscription)
        test_db.flush()
        
        # Create successful payment
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=299900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            period_start=date.today(),
            period_end=date.today(),
            processed_at=datetime.now()
        )
        test_db.add(payment)
        test_db.commit()
        
        # Test receipt generation
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}  # Mock auth
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["status"] == "success"
        assert "receipt" in data
        
        receipt = data["receipt"]
        
        # Verify receipt data
        assert receipt["receipt_id"].startswith("RCP-")
        assert receipt["payment_id"] == str(payment.id)
        assert receipt["issue_date"] == date.today().strftime("%Y-%m-%d")
        
        # Verify customer data
        assert receipt["customer"]["name"] == test_user.name
        assert receipt["customer"]["email"] == test_user.email
        assert receipt["customer"]["user_id"] == str(test_user.id)
        
        # Verify subscription data
        assert receipt["subscription"]["plan_name"] == "企業方案"
        assert receipt["subscription"]["billing_cycle"] == "annual"
        assert receipt["subscription"]["period_start"] == date.today().strftime("%Y-%m-%d")
        assert receipt["subscription"]["period_end"] == date.today().strftime("%Y-%m-%d")
        
        # Verify payment data
        assert receipt["payment"]["amount"] == 2999.00  # Converted from cents
        assert receipt["payment"]["currency"] == "TWD"
        assert receipt["payment"]["payment_method"] == "信用卡 (ECPay)"
        assert receipt["payment"]["payment_date"] is not None
        
        # Verify company data
        assert receipt["company"]["name"] == "Coaching Transcript Tool"
        assert receipt["company"]["address"] == "台灣"
        assert receipt["company"]["tax_id"] == "統一編號待補"
        assert receipt["company"]["website"] == "https://coaching-transcript-tool.com"
    
    def test_payment_not_found(self, test_client: TestClient, test_user: User):
        """Test receipt generation for non-existent payment."""
        
        fake_payment_id = str(uuid4())
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{fake_payment_id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found."
    
    def test_unauthorized_access(self, test_client: TestClient, test_db: Session):
        """Test receipt generation without proper authorization."""
        
        # Create user and payment for different user
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            name="Other User"
        )
        test_db.add(other_user)
        test_db.flush()
        
        # Create auth record for other user
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=other_user.id,
            merchant_trade_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=89900,
            period_type="M",
            exec_times=0,
            frequency=1,
            status="active"
        )
        test_db.add(auth_record)
        test_db.flush()
        
        # Create subscription for other user
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=other_user.id,
            auth_id=auth_record.id,
            plan_id="PRO",
            plan_name="專業方案",
            billing_cycle="monthly",
            amount_twd=89900,
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=date.today(),
            current_period_end=date.today()
        )
        test_db.add(subscription)
        test_db.flush()
        
        # Create payment for other user
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            period_start=date.today(),
            period_end=date.today(),
            processed_at=datetime.now()
        )
        test_db.add(payment)
        test_db.commit()
        
        # Create test user (different from payment owner)
        test_user = User(
            id=uuid4(),
            email="test@example.com", 
            name="Test User"
        )
        test_db.add(test_user)
        test_db.commit()
        
        # Try to access other user's receipt
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied. Payment does not belong to current user."
    
    def test_failed_payment_receipt(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test receipt generation for failed payment (should be rejected)."""
        
        # Create authorization record
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=89900,
            period_type="M",
            exec_times=0,
            frequency=1,
            status="active"
        )
        test_db.add(auth_record)
        test_db.flush()
        
        # Create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=test_user.id,
            auth_id=auth_record.id,
            plan_id="PRO",
            plan_name="專業方案",
            billing_cycle="monthly",
            amount_twd=89900,
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=date.today(),
            current_period_end=date.today()
        )
        test_db.add(subscription)
        test_db.flush()
        
        # Create failed payment
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.FAILED.value,
            period_start=date.today(),
            period_end=date.today(),
            failure_reason="Credit card declined"
        )
        test_db.add(payment)
        test_db.commit()
        
        # Test receipt generation for failed payment
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Receipt can only be generated for successful payments."
    
    def test_receipt_id_format(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test receipt ID format consistency."""
        
        # Create test data
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=89900,
            period_type="M",
            exec_times=0,
            frequency=1,
            status="active"
        )
        test_db.add(auth_record)
        test_db.flush()
        
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=test_user.id,
            auth_id=auth_record.id,
            plan_id="PRO",
            plan_name="專業方案",
            billing_cycle="monthly",
            amount_twd=89900,
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=date.today(),
            current_period_end=date.today()
        )
        test_db.add(subscription)
        test_db.flush()
        
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            period_start=date.today(),
            period_end=date.today(),
            processed_at=datetime.now()
        )
        test_db.add(payment)
        test_db.commit()
        
        # Test receipt generation
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        receipt = response.json()["receipt"]
        
        # Verify receipt ID format: RCP-XXXXXXXX (RCP- + first 8 chars of payment ID)
        expected_prefix = f"RCP-{str(payment.id)[:8].upper()}"
        assert receipt["receipt_id"] == expected_prefix
        
        # Verify receipt ID is uppercase
        assert receipt["receipt_id"][4:].isupper()
    
    def test_receipt_amount_conversion(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test proper amount conversion from cents to TWD."""
        
        test_cases = [
            (89900, 899.00),    # PRO monthly
            (899, 8.99),        # Small amount
            (299900, 2999.00),  # ENTERPRISE annual
            (100, 1.00),        # Minimum amount
        ]
        
        for amount_cents, expected_twd in test_cases:
            with test_db.begin():
                # Create fresh test data for each case
                auth_record = ECPayCreditAuthorization(
                    id=uuid4(),
                    user_id=test_user.id,
                    merchant_trade_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}{amount_cents}",
                    period_amount=amount_cents,
                    period_type="M",
                    exec_times=0,
                    frequency=1,
                    status="active"
                )
                test_db.add(auth_record)
                test_db.flush()
                
                subscription = SaasSubscription(
                    id=uuid4(),
                    user_id=test_user.id,
                    auth_id=auth_record.id,
                    plan_id="TEST",
                    plan_name="測試方案",
                    billing_cycle="monthly",
                    amount_twd=amount_cents,
                    currency="TWD",
                    status=SubscriptionStatus.ACTIVE.value,
                    current_period_start=date.today(),
                    current_period_end=date.today()
                )
                test_db.add(subscription)
                test_db.flush()
                
                payment = SubscriptionPayment(
                    id=uuid4(),
                    subscription_id=subscription.id,
                    amount=amount_cents,
                    currency="TWD",
                    status=PaymentStatus.SUCCESS.value,
                    period_start=date.today(),
                    period_end=date.today(),
                    processed_at=datetime.now()
                )
                test_db.add(payment)
                test_db.flush()
                
                # Test receipt generation
                response = test_client.get(
                    f"/api/v1/subscriptions/payment/{payment.id}/receipt",
                    headers={"Authorization": f"Bearer {test_user.id}"}
                )
                
                assert response.status_code == 200
                receipt = response.json()["receipt"]
                
                # Verify amount conversion
                assert receipt["payment"]["amount"] == expected_twd
                
                # Clean up for next iteration
                test_db.delete(payment)
                test_db.delete(subscription)
                test_db.delete(auth_record)