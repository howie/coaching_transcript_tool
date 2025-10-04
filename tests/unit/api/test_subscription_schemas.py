"""Unit tests for subscription API Pydantic schemas.

This test suite validates Pydantic schema definitions in isolation,
ensuring they handle edge cases like None values correctly.

These tests complement integration tests by validating schema behavior
without requiring database setup or service layer dependencies.
"""

import pytest
from pydantic import ValidationError

from coaching_assistant.api.v1.subscriptions import (
    AuthorizationResponse,
    CancelRequest,
    CreateAuthorizationRequest,
    CurrentSubscriptionResponse,
    DowngradeRequest,
    ProrationPreviewResponse,
    UpgradeRequest,
)


class TestCurrentSubscriptionResponse:
    """Test CurrentSubscriptionResponse Pydantic schema.

    Critical: These tests validate that the schema properly handles None values,
    which is essential for users without subscriptions.

    Bug History:
    - Original schema used `Dict[str, Any] = None` which Pydantic v2 rejects
    - Fixed to use `Optional[Dict[str, Any]] = None`
    - These tests ensure the fix works correctly
    """

    def test_accepts_none_for_subscription(self):
        """Verify schema accepts None for subscription field."""
        response = CurrentSubscriptionResponse(
            subscription=None, payment_method={"auth_id": "123"}, status="active"
        )

        assert response.subscription is None
        assert response.payment_method == {"auth_id": "123"}
        assert response.status == "active"

    def test_accepts_none_for_payment_method(self):
        """Verify schema accepts None for payment_method field."""
        response = CurrentSubscriptionResponse(
            subscription={"id": "sub_123"}, payment_method=None, status="active"
        )

        assert response.subscription == {"id": "sub_123"}
        assert response.payment_method is None
        assert response.status == "active"

    def test_accepts_none_for_both_optional_fields(self):
        """Verify schema accepts None for both subscription and payment_method.

        This is the production bug scenario: user has no subscription.
        The API should return all None values without Pydantic validation errors.
        """
        response = CurrentSubscriptionResponse(
            subscription=None, payment_method=None, status="no_subscription"
        )

        assert response.subscription is None
        assert response.payment_method is None
        assert response.status == "no_subscription"

    def test_accepts_valid_subscription_data(self):
        """Verify schema accepts valid complete subscription data."""
        response = CurrentSubscriptionResponse(
            subscription={
                "id": "sub_123",
                "plan_id": "pro",
                "billing_cycle": "monthly",
                "status": "active",
                "amount_cents": 29900,
                "currency": "TWD",
            },
            payment_method={"auth_id": "AUTH_123", "auth_status": "active"},
            status="active",
        )

        assert response.subscription["id"] == "sub_123"
        assert response.subscription["plan_id"] == "pro"
        assert response.payment_method["auth_id"] == "AUTH_123"
        assert response.status == "active"

    def test_default_status_value(self):
        """Verify default status is 'no_subscription'."""
        response = CurrentSubscriptionResponse()

        assert response.subscription is None
        assert response.payment_method is None
        assert response.status == "no_subscription"

    def test_json_serialization_with_none_values(self):
        """Verify schema serializes to JSON correctly with None values."""
        response = CurrentSubscriptionResponse(
            subscription=None, payment_method=None, status="no_subscription"
        )

        json_data = response.model_dump()

        assert json_data == {
            "subscription": None,
            "payment_method": None,
            "status": "no_subscription",
        }


class TestCreateAuthorizationRequest:
    """Test CreateAuthorizationRequest schema validation."""

    def test_valid_request_monthly(self):
        """Verify valid monthly authorization request."""
        request = CreateAuthorizationRequest(plan_id="PRO", billing_cycle="monthly")

        assert request.plan_id == "PRO"
        assert request.billing_cycle == "monthly"

    def test_valid_request_annual(self):
        """Verify valid annual authorization request."""
        request = CreateAuthorizationRequest(
            plan_id="COACHING_SCHOOL", billing_cycle="annual"
        )

        assert request.plan_id == "COACHING_SCHOOL"
        assert request.billing_cycle == "annual"

    def test_missing_plan_id_raises_error(self):
        """Verify missing plan_id raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAuthorizationRequest(billing_cycle="monthly")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("plan_id",) for e in errors)

    def test_missing_billing_cycle_raises_error(self):
        """Verify missing billing_cycle raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            CreateAuthorizationRequest(plan_id="PRO")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("billing_cycle",) for e in errors)


class TestCancelRequest:
    """Test CancelRequest schema validation."""

    def test_default_values(self):
        """Verify default values for optional fields."""
        request = CancelRequest()

        assert request.immediate is False
        assert request.reason is None

    def test_immediate_cancellation(self):
        """Verify immediate cancellation request."""
        request = CancelRequest(immediate=True, reason="Not satisfied with service")

        assert request.immediate is True
        assert request.reason == "Not satisfied with service"

    def test_period_end_cancellation(self):
        """Verify period-end cancellation request."""
        request = CancelRequest(immediate=False, reason="Switching to competitor")

        assert request.immediate is False
        assert request.reason == "Switching to competitor"


class TestUpgradeDowngradeRequests:
    """Test UpgradeRequest and DowngradeRequest schemas."""

    def test_upgrade_request_valid(self):
        """Verify valid upgrade request."""
        request = UpgradeRequest(plan_id="COACHING_SCHOOL", billing_cycle="annual")

        assert request.plan_id == "COACHING_SCHOOL"
        assert request.billing_cycle == "annual"

    def test_downgrade_request_valid(self):
        """Verify valid downgrade request."""
        request = DowngradeRequest(plan_id="FREE", billing_cycle="monthly")

        assert request.plan_id == "FREE"
        assert request.billing_cycle == "monthly"

    def test_upgrade_missing_fields_raises_error(self):
        """Verify missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UpgradeRequest(plan_id="PRO")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("billing_cycle",) for e in errors)


class TestProrationPreviewResponse:
    """Test ProrationPreviewResponse schema."""

    def test_valid_proration_data(self):
        """Verify valid proration preview response."""
        response = ProrationPreviewResponse(
            current_plan_remaining_value=5000,
            new_plan_prorated_cost=15000,
            net_charge=10000,
            effective_date="2025-11-04",
        )

        assert response.current_plan_remaining_value == 5000
        assert response.new_plan_prorated_cost == 15000
        assert response.net_charge == 10000
        assert response.effective_date == "2025-11-04"

    def test_negative_net_charge(self):
        """Verify proration with credit (negative net charge)."""
        response = ProrationPreviewResponse(
            current_plan_remaining_value=20000,
            new_plan_prorated_cost=15000,
            net_charge=-5000,
            effective_date="2025-11-04",
        )

        assert response.net_charge == -5000


class TestAuthorizationResponse:
    """Test AuthorizationResponse schema."""

    def test_valid_authorization_response(self):
        """Verify valid authorization response."""
        response = AuthorizationResponse(
            success=True,
            action_url="https://payment.ecpay.com.tw/...",
            form_data={"MerchantID": "123", "TradeNo": "456"},
            merchant_member_id="MEMBER_123",
            auth_id="AUTH_456",
        )

        assert response.success is True
        assert response.action_url.startswith("https://")
        assert response.form_data["MerchantID"] == "123"
        assert response.merchant_member_id == "MEMBER_123"
        assert response.auth_id == "AUTH_456"

    def test_failed_authorization_response(self):
        """Verify failed authorization response."""
        response = AuthorizationResponse(
            success=False,
            action_url="",
            form_data={},
            merchant_member_id="",
            auth_id="",
        )

        assert response.success is False
        assert response.action_url == ""
        assert response.form_data == {}
