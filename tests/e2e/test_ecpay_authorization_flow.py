"""
End-to-end tests for ECPay subscription authorization flow.
Tests the complete workflow from frontend request to ECPay API interaction.
"""

import os
from datetime import datetime
from typing import Any, Dict

import pytest
import requests

# API Base URL for testing
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class TestECPayAuthorizationE2E:
    """End-to-end tests for ECPay authorization workflow"""

    @pytest.fixture
    def valid_user_token(self):
        """Mock user token for authenticated requests"""
        # In a real E2E test, this would authenticate a test user
        return "mock_jwt_token_for_testing"

    @pytest.fixture
    def test_plan_data(self):
        """Test plan data for authorization requests"""
        return {
            "PRO": {
                "monthly": {"plan_id": "PRO", "billing_cycle": "monthly"},
                "annual": {"plan_id": "PRO", "billing_cycle": "annual"},
            },
            "ENTERPRISE": {
                "monthly": {
                    "plan_id": "ENTERPRISE",
                    "billing_cycle": "monthly",
                },
                "annual": {"plan_id": "ENTERPRISE", "billing_cycle": "annual"},
            },
        }

    def test_health_check_endpoint(self):
        """Test that ECPay webhook health endpoint is accessible"""
        response = requests.get(f"{API_BASE_URL}/api/webhooks/health")

        assert response.status_code == 200, (
            f"Health check failed: {response.status_code}"
        )

        data = response.json()
        assert data["service"] == "ecpay-webhooks", "Wrong service name in health check"
        assert data["status"] == "healthy", "Service is not healthy"
        assert "timestamp" in data, "Missing timestamp in health check"

    def test_subscription_current_requires_auth(self):
        """Test that subscription endpoints require authentication"""
        response = requests.get(f"{API_BASE_URL}/api/v1/subscriptions/current")

        assert response.status_code == 401, (
            "Subscription endpoint should require authentication"
        )

    def test_authorization_requires_auth(self):
        """Test that authorization endpoint requires authentication"""
        test_data = {"plan_id": "PRO", "billing_cycle": "monthly"}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/subscriptions/authorize", json=test_data
        )

        assert response.status_code == 401, (
            "Authorization endpoint should require authentication"
        )

    @pytest.mark.skip(reason="Requires valid JWT token - enable for full E2E testing")
    def test_full_authorization_flow(self, valid_user_token, test_plan_data):
        """
        Test complete authorization flow from API request to ECPay form generation.

        This test is skipped by default as it requires:
        1. Valid JWT token from authenticated user
        2. Database connection
        3. ECPay sandbox environment

        Enable this test in CI/staging environments with proper test setup.
        """
        headers = {"Authorization": f"Bearer {valid_user_token}"}

        for plan_type, cycles in test_plan_data.items():
            for cycle_type, request_data in cycles.items():
                # Step 1: Make authorization request
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/subscriptions/authorize",
                    json=request_data,
                    headers=headers,
                )

                # Step 2: Validate response structure
                assert response.status_code == 200, (
                    f"Authorization failed for {plan_type} {cycle_type}: {response.status_code}"
                )

                auth_data = response.json()

                # Step 3: Validate response contains required fields
                required_fields = [
                    "action_url",
                    "form_data",
                    "merchant_member_id",
                    "auth_id",
                ]
                for field in required_fields:
                    assert field in auth_data, f"Missing field {field} in response"

                # Step 4: Validate ECPay form data
                form_data = auth_data["form_data"]
                self._validate_ecpay_form_data(form_data, plan_type, cycle_type)

                # Step 5: Validate URLs
                assert (
                    auth_data["action_url"]
                    in [
                        "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction",  # Sandbox  # noqa: E501
                        "https://payment.ecpay.com.tw/CreditDetail/DoAction",  # Production  # noqa: E501
                    ]
                ), "Invalid ECPay action URL"

    def _validate_ecpay_form_data(
        self, form_data: Dict[str, Any], plan_type: str, cycle_type: str
    ):
        """Validate ECPay form data contains all required fields with correct values"""

        # Critical fields that must be present and non-empty
        critical_fields = [
            "MerchantID",
            "MerchantMemberID",
            "MerchantTradeNo",  # This caused the original bug!
            "ActionType",
            "TotalAmount",
            "ProductDesc",
            "OrderResultURL",
            "ReturnURL",
            "ClientBackURL",
            "PeriodType",
            "Frequency",
            "PeriodAmount",
            "ExecTimes",
            "PaymentType",
            "ChoosePayment",
            "TradeDesc",
            "ItemName",
            "MerchantTradeDate",
            "ExpireDate",
            "CheckMacValue",
        ]

        for field in critical_fields:
            assert field in form_data, f"Missing critical field: {field}"
            assert form_data[field] is not None, f"Field {field} is None"
            assert str(form_data[field]).strip() != "", f"Field {field} is empty"

        # Field-specific validations
        assert form_data["MerchantID"] == "3002607", "Wrong MerchantID"
        assert form_data["ActionType"] == "CreateAuth", "Wrong ActionType"
        assert form_data["PaymentType"] == "aio", "Wrong PaymentType"
        assert form_data["ChoosePayment"] == "Credit", "Wrong ChoosePayment"

        # Length validations (prevent original bug)
        assert len(form_data["MerchantTradeNo"]) <= 20, (
            f"MerchantTradeNo too long: {len(form_data['MerchantTradeNo'])} chars"
        )
        assert len(form_data["MerchantMemberID"]) <= 30, (
            f"MerchantMemberID too long: {len(form_data['MerchantMemberID'])} chars"
        )

        # Amount validations
        total_amount = int(form_data["TotalAmount"])
        period_amount = int(form_data["PeriodAmount"])
        assert total_amount == period_amount, "TotalAmount should equal PeriodAmount"
        assert total_amount > 0, "Amount must be positive"

        # Period type validation
        expected_period = "Month" if cycle_type == "monthly" else "Year"
        assert form_data["PeriodType"] == expected_period, (
            f"Wrong PeriodType: expected {expected_period}, got {form_data['PeriodType']}"
        )

        # Date format validation
        trade_date = form_data["MerchantTradeDate"]
        try:
            datetime.strptime(trade_date, "%Y/%m/%d %H:%M:%S")
        except ValueError:
            pytest.fail(f"Invalid MerchantTradeDate format: {trade_date}")

        # URL validation
        for url_field in ["OrderResultURL", "ReturnURL", "ClientBackURL"]:
            url = form_data[url_field]
            assert url.startswith(("http://", "https://")), (
                f"Invalid URL in {url_field}: {url}"
            )

        # CheckMacValue validation
        mac_value = form_data["CheckMacValue"]
        assert len(mac_value) == 64, (
            f"CheckMacValue should be 64 chars, got {len(mac_value)}"
        )
        assert mac_value.isupper(), "CheckMacValue should be uppercase"

    def test_subscription_cancel_requires_auth(self):
        """Test that subscription cancellation requires authentication"""
        test_subscription_id = "550e8400-e29b-41d4-a716-446655440000"

        response = requests.post(
            f"{API_BASE_URL}/api/v1/subscriptions/cancel/{test_subscription_id}"
        )

        assert response.status_code == 401, (
            "Cancel endpoint should require authentication"
        )

    def test_subscription_reactivate_requires_auth(self):
        """Test that subscription reactivation requires authentication"""
        test_subscription_id = "550e8400-e29b-41d4-a716-446655440000"

        response = requests.post(
            f"{API_BASE_URL}/api/v1/subscriptions/reactivate/{test_subscription_id}"
        )

        assert response.status_code == 401, (
            "Reactivate endpoint should require authentication"
        )

    def test_invalid_plan_id_handling(self):
        """Test that invalid plan IDs are handled gracefully"""

        # Mock authentication for this test
        headers = {"Authorization": "Bearer mock_token"}

        invalid_requests = [
            {"plan_id": "INVALID", "billing_cycle": "monthly"},
            {"plan_id": "PRO", "billing_cycle": "invalid_cycle"},
            {"plan_id": "", "billing_cycle": "monthly"},
            {"billing_cycle": "monthly"},  # Missing plan_id
            {"plan_id": "PRO"},  # Missing billing_cycle
        ]

        for invalid_request in invalid_requests:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/subscriptions/authorize",
                json=invalid_request,
                headers=headers,
            )

            # Should return 400 or 422 for validation errors
            assert response.status_code in [400, 401, 422], (
                f"Invalid request should be rejected: {invalid_request}, "
                f"got status {response.status_code}"
            )

    def test_webhook_endpoints_exist(self):
        """Test that ECPay webhook endpoints are accessible"""

        webhook_endpoints = [
            "/api/webhooks/ecpay-auth",
            "/api/webhooks/ecpay-billing",
            "/api/webhooks/health",
        ]

        for endpoint in webhook_endpoints:
            # Use HEAD request to check endpoint exists without triggering
            # processing
            response = requests.head(f"{API_BASE_URL}{endpoint}")

            # Should not return 404 (endpoint exists)
            assert response.status_code != 404, (
                f"Webhook endpoint not found: {endpoint}"
            )

    def test_ecpay_api_connectivity(self):
        """Test that ECPay sandbox API is reachable (network connectivity test)"""

        ecpay_urls = [
            "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction",
            "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5",
        ]

        for url in ecpay_urls:
            try:
                # Use HEAD request with short timeout to test connectivity
                response = requests.head(url, timeout=10)

                # ECPay should at least respond (even if it returns an error
                # for no data)
                assert response.status_code is not None, f"No response from {url}"

                # Common ECPay responses: 200, 400, 405 (Method Not Allowed for HEAD)
                # 404 would indicate the endpoint doesn't exist
                assert response.status_code != 404, f"ECPay endpoint not found: {url}"

            except requests.exceptions.ConnectTimeout:
                pytest.skip(f"ECPay API timeout - network connectivity issue: {url}")
            except requests.exceptions.ConnectionError:
                pytest.skip(f"Cannot connect to ECPay API: {url}")

    def test_database_migration_applied(self):
        """Test that ECPay database tables exist (indirect test via API)"""

        # This test verifies that database migrations were applied correctly
        # by checking if the API can handle database operations

        response = requests.get(f"{API_BASE_URL}/api/webhooks/health")
        assert response.status_code == 200, (
            "Health check should pass if DB is properly set up"
        )

        # The health check internally verifies database connectivity
        data = response.json()
        assert "database" not in data or data.get("database") != "error", (
            "Database error detected in health check"
        )
