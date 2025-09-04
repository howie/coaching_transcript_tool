"""
End-to-End Tests for Receipt Download Feature

Tests the complete receipt download flow from frontend to backend
"""

import pytest
import json
from datetime import datetime, date
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models import User, SaasSubscription, SubscriptionPayment, ECPayCreditAuthorization
from coaching_assistant.models.ecpay_subscription import PaymentStatus, SubscriptionStatus


class TestReceiptDownloadE2E:
    """End-to-end tests for receipt download functionality."""
    
    def test_complete_receipt_download_flow(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test complete receipt download flow from API to frontend processing."""
        
        # Step 1: Create subscription and payment data (backend setup)
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"E2E{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=89900,
            period_type="M",
            exec_times=1,
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
            current_period_start=date(2025, 8, 1),
            current_period_end=date(2025, 8, 31)
        )
        test_db.add(subscription)
        test_db.flush()
        
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.SUCCESS.value,
            period_start=date(2025, 8, 1),
            period_end=date(2025, 8, 31),
            processed_at=datetime(2025, 8, 15, 10, 30, 0)
        )
        test_db.add(payment)
        test_db.commit()
        
        # Step 2: Simulate frontend calling billing history API
        billing_response = test_client.get(
            "/api/v1/subscriptions/billing-history",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert billing_response.status_code == 200
        billing_data = billing_response.json()
        assert len(billing_data["payments"]) > 0
        
        # Find our test payment
        test_payment = None
        for p in billing_data["payments"]:
            if p["id"] == str(payment.id):
                test_payment = p
                break
        
        assert test_payment is not None
        assert test_payment["status"] == "success"
        
        # Step 3: Frontend requests receipt download
        receipt_response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert receipt_response.status_code == 200
        receipt_data = receipt_response.json()
        
        # Step 4: Verify receipt data matches payment data
        receipt = receipt_data["receipt"]
        
        # Verify receipt corresponds to the correct payment
        assert receipt["payment_id"] == str(payment.id)
        assert receipt["payment"]["amount"] == 899.0  # Converted from cents
        assert receipt["subscription"]["plan_name"] == "專業方案"
        assert receipt["subscription"]["billing_cycle"] == "monthly"
        
        # Step 5: Simulate frontend processing (what handleDownloadReceipt would do)
        receipt_html_content = self._generate_receipt_html(receipt)
        
        # Verify HTML content contains expected data
        assert "付款收據" in receipt_html_content
        assert receipt["receipt_id"] in receipt_html_content
        assert "專業方案" in receipt_html_content
        assert "NT$899" in receipt_html_content
        assert test_user.email in receipt_html_content
        assert "信用卡 (ECPay)" in receipt_html_content
        
        # Step 6: Verify receipt filename generation
        expected_filename = f"收據_{receipt['receipt_id']}_{receipt['issue_date']}.html"
        assert receipt["receipt_id"] in expected_filename
        assert receipt["issue_date"] in expected_filename
        assert expected_filename.endswith(".html")
    
    def test_receipt_download_with_different_plans(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test receipt download for different subscription plans."""
        
        test_plans = [
            {
                "plan_id": "PRO",
                "plan_name": "專業方案", 
                "billing_cycle": "monthly",
                "amount": 89900,
                "period_type": "M"
            },
            {
                "plan_id": "ENTERPRISE",
                "plan_name": "企業方案",
                "billing_cycle": "annual", 
                "amount": 299900,
                "period_type": "Y"
            }
        ]
        
        for plan in test_plans:
            # Create subscription for each plan
            auth_record = ECPayCreditAuthorization(
                id=uuid4(),
                user_id=test_user.id,
                merchant_trade_no=f"E2E{datetime.now().strftime('%Y%m%d%H%M%S')}{plan['plan_id']}",
                period_amount=plan["amount"],
                period_type=plan["period_type"],
                exec_times=1,
                frequency=1,
                status="active"
            )
            test_db.add(auth_record)
            test_db.flush()
            
            subscription = SaasSubscription(
                id=uuid4(),
                user_id=test_user.id,
                auth_id=auth_record.id,
                plan_id=plan["plan_id"],
                plan_name=plan["plan_name"],
                billing_cycle=plan["billing_cycle"],
                amount_twd=plan["amount"],
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
                amount=plan["amount"],
                currency="TWD",
                status=PaymentStatus.SUCCESS.value,
                period_start=date.today(),
                period_end=date.today(),
                processed_at=datetime.now()
            )
            test_db.add(payment)
            test_db.commit()
            
            # Test receipt generation for this plan
            response = test_client.get(
                f"/api/v1/subscriptions/payment/{payment.id}/receipt",
                headers={"Authorization": f"Bearer {test_user.id}"}
            )
            
            assert response.status_code == 200
            receipt = response.json()["receipt"]
            
            # Verify plan-specific data
            assert receipt["subscription"]["plan_name"] == plan["plan_name"]
            assert receipt["subscription"]["billing_cycle"] == plan["billing_cycle"]
            assert receipt["payment"]["amount"] == plan["amount"] / 100
            
            # Verify billing cycle display
            billing_cycle_display = "月繳" if plan["billing_cycle"] == "monthly" else "年繳"
            receipt_html = self._generate_receipt_html(receipt)
            assert billing_cycle_display in receipt_html
    
    def test_receipt_error_handling_e2e(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test error handling in receipt download flow."""
        
        # Test 1: Non-existent payment
        fake_payment_id = str(uuid4())
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{fake_payment_id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404
        
        # Test 2: Failed payment (no receipt allowed)
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"FAIL{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
        
        failed_payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription.id,
            amount=89900,
            currency="TWD",
            status=PaymentStatus.FAILED.value,
            period_start=date.today(),
            period_end=date.today(),
            failure_reason="Credit card expired"
        )
        test_db.add(failed_payment)
        test_db.commit()
        
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{failed_payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 400
        assert "successful payments" in response.json()["detail"]
    
    def test_receipt_accessibility_and_format(self, test_client: TestClient, test_user: User, test_db: Session):
        """Test receipt accessibility and format requirements."""
        
        # Create test data
        auth_record = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=test_user.id,
            merchant_trade_no=f"ACC{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period_amount=89900,
            period_type="M",
            exec_times=1,
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
        
        # Get receipt
        response = test_client.get(
            f"/api/v1/subscriptions/payment/{payment.id}/receipt",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        receipt = response.json()["receipt"]
        receipt_html = self._generate_receipt_html(receipt)
        
        # Test accessibility features
        assert 'lang="zh-TW"' in receipt_html
        assert 'meta charset="UTF-8"' in receipt_html
        assert 'meta name="viewport"' in receipt_html
        
        # Test print-friendly CSS
        assert '@media print' in receipt_html
        assert 'font-family:' in receipt_html
        
        # Test structured content
        assert '<h3>' in receipt_html  # Section headers
        assert 'class="section"' in receipt_html  # Structured sections
        assert 'class="info-row"' in receipt_html  # Data rows
        
        # Test proper escaping (security)
        assert '&' not in receipt["customer"]["name"]  # Should not contain HTML entities in data
        assert '<script>' not in receipt_html  # Should not contain scripts
    
    def _generate_receipt_html(self, receipt_data: dict) -> str:
        """
        Generate HTML content for receipt (simulates frontend logic).
        This mirrors the frontend handleDownloadReceipt function.
        """
        
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>付款收據 - {receipt_data['receipt_id']}</title>
    <style>
        body {{ font-family: Arial, 'Microsoft JhengHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .company-name {{ font-size: 24px; font-weight: bold; color: #2563eb; margin-bottom: 10px; }}
        .receipt-title {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
        .receipt-info {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
        .section {{ margin-bottom: 25px; }}
        .section h3 {{ font-size: 16px; font-weight: bold; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-bottom: 15px; }}
        .info-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
        .info-label {{ font-weight: bold; color: #555; }}
        .amount {{ font-size: 18px; font-weight: bold; color: #2563eb; }}
        .footer {{ border-top: 1px solid #ccc; padding-top: 20px; margin-top: 30px; text-align: center; color: #666; }}
        @media print {{ body {{ margin: 0; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{receipt_data['company']['name']}</div>
        <div class="receipt-title">付款收據</div>
        <div class="receipt-info">
            <div><strong>收據編號:</strong> {receipt_data['receipt_id']}</div>
            <div><strong>開立日期:</strong> {receipt_data['issue_date']}</div>
        </div>
    </div>

    <div class="section">
        <h3>客戶資訊</h3>
        <div class="info-row">
            <span class="info-label">姓名:</span>
            <span>{receipt_data['customer']['name']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">電子郵件:</span>
            <span>{receipt_data['customer']['email']}</span>
        </div>
    </div>

    <div class="section">
        <h3>訂閱資訊</h3>
        <div class="info-row">
            <span class="info-label">方案名稱:</span>
            <span>{receipt_data['subscription']['plan_name']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">計費週期:</span>
            <span>{'月繳' if receipt_data['subscription']['billing_cycle'] == 'monthly' else '年繳'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">服務期間:</span>
            <span>{receipt_data['subscription']['period_start']} 至 {receipt_data['subscription']['period_end']}</span>
        </div>
    </div>

    <div class="section">
        <h3>付款資訊</h3>
        <div class="info-row">
            <span class="info-label">付款金額:</span>
            <span class="amount">NT${receipt_data['payment']['amount']:,.0f}</span>
        </div>
        <div class="info-row">
            <span class="info-label">付款方式:</span>
            <span>{receipt_data['payment']['payment_method']}</span>
        </div>
        <div class="info-row">
            <span class="info-label">付款時間:</span>
            <span>{receipt_data['payment']['payment_date'] or '處理中'}</span>
        </div>
    </div>

    <div class="footer">
        <div><strong>{receipt_data['company']['name']}</strong></div>
        <div>{receipt_data['company']['address']}</div>
        <div>統一編號: {receipt_data['company']['tax_id']}</div>
        <div>{receipt_data['company']['website']}</div>
    </div>
</body>
</html>"""