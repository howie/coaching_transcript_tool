"""
Comprehensive ECPay parameter validation tests to prevent API errors.
These tests validate that all parameters comply with ECPay's strict requirements.
"""

import re
from unittest.mock import Mock, patch

import pytest

from src.coaching_assistant.core.services.ecpay_service import (
    ECPaySubscriptionService,
)


class TestECPayParameterValidation:
    """Test ECPay parameter format compliance to prevent API errors"""

    @pytest.fixture
    def mock_db_session(self):
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def mock_settings(self):
        settings = Mock()
        settings.ECPAY_MERCHANT_ID = "3002607"
        settings.ECPAY_HASH_KEY = "pwFHCqoQZGmho4w6"
        settings.ECPAY_HASH_IV = "EkRm7iFT261dpevs"
        settings.ECPAY_ENVIRONMENT = "sandbox"
        settings.FRONTEND_URL = "http://localhost:3000"
        settings.API_BASE_URL = "http://localhost:8000"
        return settings

    @pytest.fixture
    def ecpay_service(self, mock_db_session, mock_settings):
        return ECPaySubscriptionService(mock_db_session, mock_settings)

    def test_text_fields_english_only(self, ecpay_service):
        """Test that all text fields use English only (no Chinese characters)"""

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"

        with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan",
            }

            result = ecpay_service.create_credit_authorization(
                user_id, plan_id, billing_cycle
            )
            auth_data = result["form_data"]

            # Text fields that must be English only
            text_fields = ["ProductDesc", "TradeDesc", "ItemName", "Remark"]

            for field in text_fields:
                assert field in auth_data, f"Missing text field: {field}"
                value = str(auth_data[field])

                # Check for Chinese characters (Unicode ranges)
                chinese_pattern = re.compile(
                    r"[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]"
                )
                assert not chinese_pattern.search(value), (
                    f"{field} contains Chinese characters: '{value}' - ECPay requires English only"
                )

                # Check for problematic special characters
                forbidden_chars = ["<", ">", "&", '"', "'", "\\n", "\\t"]
                for char in forbidden_chars:
                    assert char not in value, (
                        f"{field} contains forbidden character '{char}': '{value}'"
                    )

    def test_exec_times_business_rules(self, ecpay_service):
        """Test ECPay ExecTimes rules: M=0 (unlimited), Y=2-99 (limited)"""

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"

        test_cases = [
            ("monthly", "M", 0),  # Monthly = unlimited
            ("annual", "Y", 99),  # Yearly = limited to 99
        ]

        for (
            billing_cycle,
            expected_period_type,
            expected_exec_times,
        ) in test_cases:
            with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
                mock_pricing.return_value = {
                    "amount_twd": 89900,
                    "plan_name": "Professional Plan",
                }

                result = ecpay_service.create_credit_authorization(
                    user_id, plan_id, billing_cycle
                )
                auth_data = result["form_data"]

                assert auth_data["PeriodType"] == expected_period_type, (
                    f"PeriodType should be {expected_period_type} for {billing_cycle}"
                )

                assert auth_data["ExecTimes"] == expected_exec_times, (
                    f"ExecTimes should be {expected_exec_times} for {billing_cycle} "
                    f"(PeriodType {expected_period_type}), got {auth_data['ExecTimes']}"
                )

                # Validate ECPay business rules
                if expected_period_type == "M":
                    assert auth_data["ExecTimes"] == 0, (
                        "Monthly plans must have ExecTimes=0"
                    )
                elif expected_period_type == "Y":
                    assert 2 <= auth_data["ExecTimes"] <= 99, (
                        f"Yearly plans must have ExecTimes between 2-99, got {auth_data['ExecTimes']}"
                    )

    def test_missing_action_type_for_aio_checkout(self, ecpay_service):
        """Test that ActionType is NOT present for AioCheckOut endpoint"""

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"

        with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan",
            }

            result = ecpay_service.create_credit_authorization(
                user_id, plan_id, billing_cycle
            )
            auth_data = result["form_data"]

            # ActionType should NOT be present for AioCheckOut
            assert "ActionType" not in auth_data, (
                "ActionType should not be present for AioCheckOut endpoint. "
                "This causes ECPay error 10100050 (Parameter Error. ActionType Not In Spec.)"
            )

    def test_required_aio_checkout_fields(self, ecpay_service):
        """Test all required fields for AioCheckOut recurring payments"""

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"

        with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan",
            }

            result = ecpay_service.create_credit_authorization(
                user_id, plan_id, billing_cycle
            )
            auth_data = result["form_data"]

            # Required fields for AioCheckOut recurring payments
            required_fields = [
                "MerchantID",
                "MerchantMemberID",
                "MerchantTradeNo",
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

            for field in required_fields:
                assert field in auth_data, (
                    f"Missing required AioCheckOut field: {field}"
                )
                assert auth_data[field] is not None, f"Field {field} is None"
                assert str(auth_data[field]).strip() != "", f"Field {field} is empty"

    def test_parameter_length_constraints(self, ecpay_service):
        """Test ECPay parameter length constraints"""

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"

        with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan",
            }

            result = ecpay_service.create_credit_authorization(
                user_id, plan_id, billing_cycle
            )
            auth_data = result["form_data"]

            # Critical length constraints
            assert len(auth_data["MerchantTradeNo"]) <= 20, (
                f"MerchantTradeNo too long: {len(auth_data['MerchantTradeNo'])} chars "
                f"(max 20). Value: '{auth_data['MerchantTradeNo']}'"
            )

            # ProductDesc length (typical ECPay limit ~200 chars)
            assert len(auth_data["ProductDesc"]) <= 200, (
                f"ProductDesc too long: {len(auth_data['ProductDesc'])} chars"
            )

    def test_merchant_trade_no_format_compliance(self, ecpay_service):
        """Test MerchantTradeNo format prevents ECPay errors"""

        # Test with various user IDs that could cause issues
        problematic_user_ids = [
            "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID
            "user@domain.com",  # Email format
            "用戶中文名稱",  # Chinese characters
            "user with spaces",  # Spaces
            "user<script>alert</script>",  # Malicious input
        ]

        plan_id = "PRO"
        billing_cycle = "monthly"

        for user_id in problematic_user_ids:
            with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
                mock_pricing.return_value = {
                    "amount_twd": 89900,
                    "plan_name": "Professional Plan",
                }

                result = ecpay_service.create_credit_authorization(
                    user_id, plan_id, billing_cycle
                )
                auth_data = result["form_data"]

                merchant_trade_no = auth_data["MerchantTradeNo"]

                # Critical: Must not exceed 20 characters
                assert len(merchant_trade_no) <= 20, (
                    f"MerchantTradeNo exceeds 20 chars for user '{user_id[:20]}...': "
                    f"'{merchant_trade_no}' ({len(merchant_trade_no)} chars)"
                )

                # Should be alphanumeric after processing
                assert merchant_trade_no.replace("SUB", "").isalnum(), (
                    f"MerchantTradeNo contains non-alphanumeric chars: '{merchant_trade_no}'"
                )

    def test_api_endpoint_configuration(self, ecpay_service):
        """Test that correct API endpoint is configured"""

        # Should use AioCheckOut for recurring payments, not CreditDetail
        assert "AioCheckOut" in ecpay_service.aio_url, (
            "Should use AioCheckOut endpoint for recurring payments"
        )

        assert "payment-stage.ecpay.com.tw" in ecpay_service.aio_url, (
            "Should use sandbox environment for testing"
        )

        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"

        with patch.object(ecpay_service, "_get_plan_pricing") as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan",
            }

            result = ecpay_service.create_credit_authorization(
                user_id, plan_id, billing_cycle
            )

            # Should return AioCheckOut URL
            assert result["action_url"] == ecpay_service.aio_url, (
                "Authorization should use AioCheckOut endpoint"
            )
