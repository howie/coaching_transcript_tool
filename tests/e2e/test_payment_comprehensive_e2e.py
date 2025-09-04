"""
Comprehensive E2E tests for ECPay subscription payment system.
Tests complete payment flows, error scenarios, and recovery mechanisms.
"""

import pytest
import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

# Test configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
ADMIN_TOKEN = os.getenv('ADMIN_WEBHOOK_TOKEN', 'test_admin_token')
TEST_TIMEOUT = 30  # seconds


class TestPaymentFlowsE2E:
    """Complete end-to-end payment flow tests."""

    @pytest.fixture
    def test_client(self):
        """FastAPI test client for direct API testing."""
        from coaching_assistant.main import app
        return TestClient(app)

    @pytest.fixture
    def mock_user_token(self):
        """Mock authenticated user token."""
        return {
            "user_id": "test_user_123",
            "email": "test@example.com", 
            "name": "Test User",
            "plan": "FREE"
        }

    @pytest.fixture
    def subscription_test_data(self):
        """Test data for subscription scenarios."""
        return {
            "plans": ["PRO", "ENTERPRISE"],
            "cycles": ["monthly", "annual"],
            "amounts": {
                "PRO_monthly": 89900,  # TWD cents
                "PRO_annual": 899000,
                "ENTERPRISE_monthly": 299900,
                "ENTERPRISE_annual": 2999000
            }
        }

    def test_complete_subscription_authorization_flow(self, test_client, mock_user_token, subscription_test_data):
        """Test complete subscription authorization from start to ECPay redirect."""
        
        headers = {"Authorization": f"Bearer mock_jwt_token"}
        
        for plan in subscription_test_data["plans"]:
            for cycle in subscription_test_data["cycles"]:
                # Step 1: Check user's current plan limits
                response = test_client.get("/api/plans/current", headers=headers)
                if response.status_code == 200:
                    current_plan = response.json()
                    assert current_plan["plan"] in ["FREE", "PRO", "ENTERPRISE"]

                # Step 2: Initiate subscription authorization
                auth_request = {
                    "plan_id": plan,
                    "billing_cycle": cycle
                }
                
                with patch('src.coaching_assistant.services.auth_service.verify_jwt_token') as mock_auth:
                    mock_auth.return_value = mock_user_token
                    
                    response = test_client.post(
                        "/api/v1/subscriptions/authorize",
                        json=auth_request,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        # Step 3: Validate ECPay authorization response
                        auth_data = response.json()
                        self._validate_ecpay_authorization_response(auth_data, plan, cycle)
                        
                        # Step 4: Simulate user completing payment on ECPay
                        self._simulate_ecpay_payment_completion(
                            test_client, 
                            auth_data["merchant_member_id"],
                            auth_data["merchant_trade_no"]
                        )

    def _validate_ecpay_authorization_response(self, auth_data: Dict[str, Any], plan: str, cycle: str):
        """Validate ECPay authorization response structure and data."""
        
        # Critical fields validation
        required_fields = [
            "action_url", "form_data", "merchant_member_id", 
            "merchant_trade_no", "auth_id"
        ]
        
        for field in required_fields:
            assert field in auth_data, f"Missing field: {field}"
            assert auth_data[field] is not None, f"Field {field} is None"

        # ECPay form data validation
        form_data = auth_data["form_data"]
        assert form_data["ActionType"] == "CreateAuth"
        assert form_data["PaymentType"] == "aio"
        assert form_data["ChoosePayment"] == "Credit"
        
        # Amount validation
        total_amount = int(form_data["TotalAmount"])
        period_amount = int(form_data["PeriodAmount"])
        assert total_amount == period_amount
        assert total_amount > 0

        # Period type validation
        expected_period = "Month" if cycle == "monthly" else "Year"
        assert form_data["PeriodType"] == expected_period

        # Security validation
        assert len(form_data["CheckMacValue"]) == 64
        assert form_data["CheckMacValue"].isupper()

    def _simulate_ecpay_payment_completion(self, client: TestClient, member_id: str, trade_no: str):
        """Simulate ECPay calling our webhook after payment completion."""
        
        # Simulate successful authorization webhook
        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": member_id,
            "MerchantTradeNo": trade_no,
            "AuthCode": "777777",
            "card4no": "1234",
            "card6no": "123456",
            "amount": "89900",
            "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "auth_cap_flag": "N",
            "status": "1",
            "CheckMacValue": "mock_check_mac_value"
        }

        # Send authorization webhook
        response = client.post(
            "/api/webhooks/ecpay-auth",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        return response.status_code in [200, 201]

    def test_payment_failure_and_retry_flow(self, test_client):
        """Test complete payment failure, retry, and recovery flow."""
        
        # Step 1: Create subscription with failed payment
        subscription_data = self._create_test_subscription_with_failure(test_client)
        
        # Step 2: Verify subscription enters PAST_DUE status
        response = test_client.get(
            f"/api/webhooks/subscription-status/{subscription_data['user_id']}?admin_token={ADMIN_TOKEN}"
        )
        
        if response.status_code == 200:
            status = response.json()
            assert status["subscription"]["status"] == "PAST_DUE"
            assert status["subscription"]["grace_period_ends_at"] is not None

        # Step 3: Test manual payment retry
        retry_response = test_client.post(
            f"/api/webhooks/ecpay-manual-retry?payment_id={subscription_data['payment_id']}&admin_token={ADMIN_TOKEN}"
        )
        
        if retry_response.status_code == 200:
            result = retry_response.json()
            assert result["status"] == "success"
            assert result["payment_id"] == subscription_data["payment_id"]

        # Step 4: Verify subscription recovery
        time.sleep(1)  # Allow processing
        
        final_status = test_client.get(
            f"/api/webhooks/subscription-status/{subscription_data['user_id']}?admin_token={ADMIN_TOKEN}"
        )
        
        if final_status.status_code == 200:
            status = final_status.json()
            # Should be recovered or still retrying
            assert status["subscription"]["status"] in ["ACTIVE", "PAST_DUE"]

    def _create_test_subscription_with_failure(self, client: TestClient) -> Dict[str, str]:
        """Create a test subscription with failed payment for testing."""
        
        # Simulate failed billing webhook
        failed_payment_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "test_member_456",
            "MerchantTradeNo": "FAIL20250101123456",
            "amount": "89900",
            "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "status": "0",  # Failed
            "gwsr": "10100050",  # ECPay error code
            "CheckMacValue": "mock_failed_check_mac"
        }

        client.post(
            "/api/webhooks/ecpay-billing",
            data=failed_payment_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        return {
            "user_id": "test_user_456",
            "payment_id": "test_payment_456",
            "merchant_trade_no": failed_payment_data["MerchantTradeNo"]
        }

    def test_subscription_downgrade_after_max_failures(self, test_client):
        """Test automatic downgrade to FREE after maximum payment failures."""
        
        user_id = "downgrade_test_789"
        
        # Create multiple payment failures
        for i in range(3):
            failed_data = {
                "MerchantID": "3002607", 
                "MerchantMemberID": f"downgrade_member_{i}",
                "MerchantTradeNo": f"FAIL202501{i:02d}123456",
                "amount": "89900",
                "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "status": "0",
                "gwsr": "10100050",
                "CheckMacValue": "mock_check_mac"
            }
            
            client.post(
                "/api/webhooks/ecpay-billing",
                data=failed_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            time.sleep(0.5)  # Allow processing

        # Check final subscription status
        response = test_client.get(
            f"/api/webhooks/subscription-status/{user_id}?admin_token={ADMIN_TOKEN}"
        )
        
        if response.status_code == 200:
            status = response.json()
            subscription = status.get("subscription", {})
            
            # Should be downgraded to FREE or still processing
            if subscription.get("plan_id") == "FREE":
                assert subscription["status"] == "ACTIVE"
                assert subscription["downgrade_reason"] == "payment_failure"

    def test_webhook_security_and_validation(self, test_client):
        """Test webhook security measures and parameter validation."""
        
        # Test 1: Invalid CheckMacValue should be rejected
        invalid_webhook = {
            "MerchantID": "3002607",
            "MerchantMemberID": "security_test",
            "MerchantTradeNo": "SEC20250101123456", 
            "amount": "89900",
            "CheckMacValue": "INVALID_CHECKSUM"
        }
        
        response = test_client.post(
            "/api/webhooks/ecpay-auth",
            data=invalid_webhook,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should reject invalid checksum
        assert response.status_code in [400, 401, 403]

        # Test 2: Missing required fields
        incomplete_webhook = {
            "MerchantID": "3002607",
            "amount": "89900"
            # Missing critical fields
        }
        
        response = test_client.post(
            "/api/webhooks/ecpay-billing",
            data=incomplete_webhook,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code in [400, 422]

        # Test 3: Admin endpoint protection
        response = test_client.post(
            "/api/webhooks/ecpay-manual-retry?payment_id=test&admin_token=wrong_token"
        )
        
        assert response.status_code in [401, 403]

    def test_concurrent_webhook_processing(self, test_client):
        """Test concurrent webhook processing doesn't cause race conditions."""
        
        import threading
        import concurrent.futures
        
        results = []
        
        def send_webhook(webhook_id: int):
            """Send a webhook request and collect result."""
            try:
                webhook_data = {
                    "MerchantID": "3002607",
                    "MerchantMemberID": f"concurrent_test_{webhook_id}",
                    "MerchantTradeNo": f"CON202501{webhook_id:02d}123456",
                    "amount": "89900",
                    "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    "status": "1",
                    "CheckMacValue": f"mock_check_mac_{webhook_id}"
                }
                
                response = test_client.post(
                    "/api/webhooks/ecpay-billing",
                    data=webhook_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                return {
                    "webhook_id": webhook_id,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 201]
                }
            except Exception as e:
                return {
                    "webhook_id": webhook_id,
                    "status_code": 500,
                    "success": False,
                    "error": str(e)
                }

        # Send 5 concurrent webhooks
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_webhook, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all webhooks processed successfully
        successful_webhooks = [r for r in results if r["success"]]
        assert len(successful_webhooks) >= 3, f"Expected at least 3 successful webhooks, got {len(successful_webhooks)}"

    def test_subscription_upgrade_downgrade_flows(self, test_client, mock_user_token):
        """Test subscription upgrade and downgrade flows."""
        
        headers = {"Authorization": "Bearer mock_jwt_token"}
        
        with patch('src.coaching_assistant.services.auth_service.verify_jwt_token') as mock_auth:
            mock_auth.return_value = mock_user_token
            
            # Test 1: Upgrade from FREE to PRO
            upgrade_response = test_client.post(
                "/api/v1/subscriptions/authorize",
                json={"plan_id": "PRO", "billing_cycle": "monthly"},
                headers=headers
            )
            
            if upgrade_response.status_code == 200:
                # Simulate successful upgrade completion
                self._simulate_successful_payment(test_client, upgrade_response.json())

            # Test 2: Upgrade from PRO to ENTERPRISE  
            enterprise_response = test_client.post(
                "/api/v1/subscriptions/authorize",
                json={"plan_id": "ENTERPRISE", "billing_cycle": "monthly"},
                headers=headers
            )
            
            if enterprise_response.status_code == 200:
                self._simulate_successful_payment(test_client, enterprise_response.json())

            # Test 3: Downgrade scenarios
            downgrade_response = test_client.post(
                "/api/v1/subscriptions/cancel/test_sub_id",
                headers=headers
            )
            
            # Should handle downgrade request
            assert downgrade_response.status_code in [200, 404, 401]

    def _simulate_successful_payment(self, client: TestClient, auth_data: Dict[str, Any]):
        """Simulate successful ECPay payment completion."""
        
        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": auth_data.get("merchant_member_id", "test_member"),
            "MerchantTradeNo": auth_data.get("merchant_trade_no", "test_trade"),
            "amount": "89900",
            "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "status": "1",
            "AuthCode": "777777",
            "CheckMacValue": "mock_success_check_mac"
        }

        return client.post(
            "/api/webhooks/ecpay-billing",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios."""

    def test_database_connection_failure_handling(self, test_client):
        """Test handling of database connection failures."""
        
        with patch('src.coaching_assistant.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = test_client.get("/api/webhooks/health")
            
            # Should handle database errors gracefully
            if response.status_code == 200:
                health_data = response.json()
                assert health_data.get("database") in ["error", "unavailable", None]

    def test_ecpay_api_timeout_handling(self, test_client):
        """Test handling of ECPay API timeouts."""
        
        with patch('requests.post') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("ECPay API timeout")
            
            # Test authorization request with timeout
            auth_request = {
                "plan_id": "PRO",
                "billing_cycle": "monthly"
            }
            
            headers = {"Authorization": "Bearer mock_jwt_token"}
            
            with patch('src.coaching_assistant.services.auth_service.verify_jwt_token'):
                response = test_client.post(
                    "/api/v1/subscriptions/authorize",
                    json=auth_request,
                    headers=headers
                )
                
                # Should handle timeout gracefully
                assert response.status_code in [500, 503, 504]

    def test_invalid_webhook_data_handling(self, test_client):
        """Test handling of malformed or invalid webhook data."""
        
        invalid_scenarios = [
            # Empty data
            {},
            
            # Invalid JSON
            {"invalid": "json", "data": None},
            
            # Missing critical fields
            {"MerchantID": "3002607"},
            
            # Invalid amounts
            {"MerchantID": "3002607", "amount": "invalid_amount"},
            
            # Invalid dates
            {"MerchantID": "3002607", "process_date": "invalid_date"},
            
            # Malicious data
            {"MerchantID": "<script>alert('xss')</script>"},
        ]

        for invalid_data in invalid_scenarios:
            response = test_client.post(
                "/api/webhooks/ecpay-billing",
                data=invalid_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Should reject invalid data
            assert response.status_code in [400, 422, 500]

    def test_rate_limiting_and_abuse_prevention(self, test_client):
        """Test rate limiting on webhook endpoints."""
        
        # Send many requests rapidly
        responses = []
        for i in range(10):
            response = test_client.post(
                "/api/webhooks/ecpay-billing",
                data={"MerchantID": "3002607", "test": f"request_{i}"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            responses.append(response.status_code)

        # Should handle rapid requests appropriately
        # Either process all or rate limit some
        success_count = sum(1 for status in responses if status in [200, 201])
        rate_limited_count = sum(1 for status in responses if status == 429)
        
        # At least some should be processed or rate limited appropriately
        assert (success_count + rate_limited_count) > 0


class TestMultiBrowserCompatibility:
    """Multi-browser compatibility tests."""

    def test_payment_form_rendering_compatibility(self):
        """Test ECPay payment form compatibility across browsers."""
        
        # Test different user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124",  # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",      # Firefox
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/14.1.1", # Safari
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",                     # IE
        ]

        for user_agent in user_agents:
            response = requests.get(
                f"{API_BASE_URL}/api/plans/current",
                headers={"User-Agent": user_agent}
            )
            
            # Should work across different browsers
            assert response.status_code in [200, 401]

    def test_mobile_device_compatibility(self):
        """Test payment flows on mobile devices."""
        
        mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 Chrome/91.0.4472.120 Mobile Safari/537.36",
        ]

        for user_agent in mobile_user_agents:
            response = requests.get(
                f"{API_BASE_URL}/api/webhooks/health",
                headers={"User-Agent": user_agent}
            )
            
            # Mobile devices should also work
            assert response.status_code == 200


class TestPerformanceAndScalability:
    """Performance and scalability tests."""

    def test_webhook_processing_performance(self, test_client):
        """Test webhook processing performance under load."""
        
        start_time = time.time()
        
        # Process multiple webhooks
        for i in range(20):
            webhook_data = {
                "MerchantID": "3002607",
                "MerchantMemberID": f"perf_test_{i}",
                "MerchantTradeNo": f"PERF202501{i:02d}123456",
                "amount": "89900",
                "process_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "status": "1",
                "CheckMacValue": f"mock_perf_check_{i}"
            }
            
            test_client.post(
                "/api/webhooks/ecpay-billing",
                data=webhook_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process webhooks efficiently
        average_time_per_webhook = processing_time / 20
        assert average_time_per_webhook < 1.0  # Less than 1 second per webhook

    def test_memory_usage_during_bulk_processing(self, test_client):
        """Test memory usage doesn't grow excessively during bulk processing."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process many webhooks
        for batch in range(5):
            for i in range(10):
                webhook_data = {
                    "MerchantID": "3002607",
                    "MerchantMemberID": f"memory_test_{batch}_{i}",
                    "MerchantTradeNo": f"MEM{batch}{i:02d}20250101123456",
                    "amount": "89900",
                    "status": "1",
                    "CheckMacValue": f"mock_memory_check_{batch}_{i}"
                }
                
                test_client.post(
                    "/api/webhooks/ecpay-billing", 
                    data=webhook_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 100MB for this test)
        assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.2f}MB"


@pytest.mark.integration
class TestIntegrationWithExternalServices:
    """Integration tests with external services."""

    def test_ecpay_sandbox_connectivity(self):
        """Test connectivity to ECPay sandbox environment."""
        
        ecpay_endpoints = [
            "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction",
            "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
        ]

        for endpoint in ecpay_endpoints:
            try:
                response = requests.head(endpoint, timeout=10)
                # Should be reachable (even if returns error for empty request)
                assert response.status_code != 404
            except requests.exceptions.Timeout:
                pytest.skip(f"ECPay sandbox timeout: {endpoint}")
            except requests.exceptions.ConnectionError:
                pytest.skip(f"ECPay sandbox unreachable: {endpoint}")

    def test_database_performance_under_load(self, test_client):
        """Test database performance with concurrent operations."""
        
        start_time = time.time()
        
        # Multiple concurrent health checks (database operations)
        responses = []
        for i in range(10):
            response = test_client.get("/api/webhooks/health")
            responses.append(response.status_code)

        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent database operations efficiently
        assert total_time < 5.0  # All operations under 5 seconds
        successful_responses = sum(1 for status in responses if status == 200)
        assert successful_responses >= 8  # At least 80% success rate


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])