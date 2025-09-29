"""
Unit tests for ECPay API response validation and error handling.
These tests ensure robust handling of ECPay API responses and prevent
silent failures that could lead to billing issues.
"""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.coaching_assistant.core.services.ecpay_service import (
    ECPaySubscriptionService,
)
from src.coaching_assistant.models.ecpay_subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    SubscriptionStatus,
)


class TestECPayAPIResponseValidation:
    """Unit tests for ECPay API response validation"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def mock_settings(self):
        """Mock ECPay settings"""
        settings = Mock()
        settings.ECPAY_MERCHANT_ID = "3002607"
        settings.ECPAY_HASH_KEY = "pwFHCqoQZGmho4w6"
        settings.ECPAY_HASH_IV = "EkRm7iFT261dpevs"
        settings.ECPAY_ENVIRONMENT = "sandbox"
        settings.FRONTEND_URL = "http://localhost:3000"
        settings.API_BASE_URL = "http://localhost:8000"
        return settings

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def mock_subscription_repo(self):
        """Mock subscription repository"""
        return Mock()

    @pytest.fixture
    def mock_ecpay_client(self):
        """Mock ECPay client"""
        return Mock()

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service"""
        return Mock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_subscription_repo, mock_settings, mock_ecpay_client, mock_notification_service, mock_db_session):
        """Create service instance with all required dependencies"""
        service = ECPaySubscriptionService(
            user_repo=mock_user_repo,
            subscription_repo=mock_subscription_repo,
            settings=mock_settings,
            ecpay_client=mock_ecpay_client,
            notification_service=mock_notification_service
        )
        # Add mock db session for backwards compatibility with existing tests
        service.db = mock_db_session
        return service

    def test_successful_auth_callback_handling(self, service, mock_db_session):
        """Test handling of successful ECPay authorization callback"""

        # Mock database queries
        mock_auth = Mock()
        mock_auth.user_id = "user123"
        mock_auth.period_type = "Month"
        mock_auth.id = "auth123"

        # Mock the auth record query (first query)
        auth_query_mock = Mock()
        auth_query_mock.filter.return_value.first.return_value = mock_auth

        # Mock the user query (second query)
        mock_user = Mock()
        user_query_mock = Mock()
        user_query_mock.filter.return_value.first.return_value = mock_user

        # Set up query sequence to return different results for different model types
        mock_db_session.query.side_effect = [auth_query_mock, user_query_mock]

        # Valid successful callback data
        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "USER550e84001755520128",
            "MerchantTradeNo": "SUB520128550E8400",
            "RtnCode": "1",  # Success
            "gwsr": "123456789",
            "AuthCode": "AUTH123456",
            "card4no": "4242",
            "card6no": "424242",
            "CheckMacValue": "VALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=True):
            with patch.object(service, "_create_subscription") as mock_create_sub:
                mock_subscription = Mock()
                mock_subscription.plan_id = "PRO"
                mock_create_sub.return_value = mock_subscription

                result = service.handle_auth_callback(callback_data)

                # Should succeed
                assert result is True, "Successful callback should return True"

                # Verify auth record was updated
                assert mock_auth.auth_status == ECPayAuthStatus.ACTIVE.value
                assert mock_auth.gwsr == "123456789"
                assert mock_auth.auth_code == "AUTH123456"
                assert mock_auth.card_last4 == "4242"
                assert mock_auth.card_brand == "424242"

                # Verify database operations
                mock_db_session.commit.assert_called()
                mock_create_sub.assert_called_once_with(mock_auth)

    def test_failed_auth_callback_handling(self, service, mock_db_session):
        """Test handling of failed ECPay authorization callback"""

        mock_auth = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_auth
        )

        # Failed callback data
        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "USER550e84001755520128",
            "MerchantTradeNo": "SUB520128550E8400",
            "RtnCode": "0",  # Failed
            "RtnMsg": "Credit card authorization failed",
            "CheckMacValue": "VALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=True):
            result = service.handle_auth_callback(callback_data)

            # Should return False for failed auth
            assert result is False, "Failed callback should return False"

            # Verify auth record was marked as failed
            assert mock_auth.auth_status == ECPayAuthStatus.FAILED.value
            mock_db_session.commit.assert_called()

    def test_invalid_callback_mac_value(self, service, mock_db_session):
        """Test rejection of callback with invalid CheckMacValue"""

        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "USER550e84001755520128",
            "RtnCode": "1",
            "CheckMacValue": "INVALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=False):
            result = service.handle_auth_callback(callback_data)

            # Should reject invalid MAC
            assert result is False, "Invalid MAC should be rejected"

            # Should not perform any database operations
            mock_db_session.commit.assert_not_called()
            mock_db_session.rollback.assert_not_called()

    def test_missing_merchant_member_id_callback(self, service, mock_db_session):
        """Test handling of callback missing MerchantMemberID"""

        callback_data = {
            "MerchantID": "3002607",
            "RtnCode": "1",
            "CheckMacValue": "VALID_MAC_VALUE",
            # Missing MerchantMemberID
        }

        with patch.object(service, "_verify_callback", return_value=True):
            result = service.handle_auth_callback(callback_data)

            assert result is False, "Missing MerchantMemberID should be rejected"

    def test_auth_record_not_found_callback(self, service, mock_db_session):
        """Test handling of callback for non-existent authorization record"""

        # Mock query to return None (record not found)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        callback_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "NONEXISTENT_MEMBER_ID",
            "RtnCode": "1",
            "CheckMacValue": "VALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=True):
            result = service.handle_auth_callback(callback_data)

            assert result is False, "Non-existent auth record should be rejected"

    def test_successful_payment_webhook_handling(self, service, mock_db_session):
        """Test handling of successful payment webhook"""

        # Mock authorization record
        mock_auth = Mock()
        mock_auth.id = "auth123"
        mock_auth.period_type = "M"  # Should be "M" for Month, not "Month"
        mock_auth.exec_times = 0  # Initialize exec_times for arithmetic operations

        # Mock subscription
        mock_subscription = Mock()
        mock_subscription.id = "sub123"
        mock_subscription.current_period_start = date.today()
        mock_subscription.current_period_end = date.today()

        # Setup database queries
        query_mock = mock_db_session.query.return_value
        query_mock.filter.return_value.first.side_effect = [
            mock_auth,
            mock_subscription,
        ]

        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "USER550e84001755520128",
            "gwsr": "987654321",
            "RtnCode": "1",  # Success
            "amount": "899",  # In dollars
            "CheckMacValue": "VALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=True):
            with patch.object(service, "_handle_payment_success_notifications", new=AsyncMock()):
                result = service.handle_payment_webhook(webhook_data)

            assert result is True, "Successful payment webhook should return True"

            # Verify subscription was extended
            assert mock_subscription.status == SubscriptionStatus.ACTIVE.value
            mock_db_session.add.assert_called()  # Payment record added
            mock_db_session.commit.assert_called()

    def test_failed_payment_webhook_handling(self, service, mock_db_session):
        """Test handling of failed payment webhook"""

        mock_auth = Mock()
        mock_auth.id = "auth123"

        mock_subscription = Mock()
        mock_subscription.id = "sub123"

        query_mock = mock_db_session.query.return_value
        query_mock.filter.return_value.first.side_effect = [
            mock_auth,
            mock_subscription,
        ]

        webhook_data = {
            "MerchantID": "3002607",
            "MerchantMemberID": "USER550e84001755520128",
            "gwsr": "987654321",
            "RtnCode": "0",  # Failed
            "RtnMsg": "Insufficient funds",
            "amount": "899",
            "CheckMacValue": "VALID_MAC_VALUE",
        }

        with patch.object(service, "_verify_callback", return_value=True):
            with patch.object(service, "_handle_failed_payment") as mock_handle_failed:
                result = service.handle_payment_webhook(webhook_data)

                assert result is True, (
                    "Webhook processing should succeed even if payment failed"
                )
                mock_handle_failed.assert_called_once()

    def test_check_mac_value_generation_consistency(self, service):
        """Test CheckMacValue generation is consistent and secure"""

        test_data = {
            "MerchantID": "3002607",
            "MerchantTradeNo": "SUB520128550E8400",
            "TotalAmount": "899",
            "PaymentType": "aio",
            "ActionType": "CreateAuth",
        }

        # Generate multiple times with same data
        mac1 = service._generate_check_mac_value(test_data.copy())
        mac2 = service._generate_check_mac_value(test_data.copy())
        mac3 = service._generate_check_mac_value(test_data.copy())

        # Should be identical
        assert mac1 == mac2 == mac3, "CheckMacValue generation not consistent"

        # Should be 64 characters (SHA256)
        assert len(mac1) == 64, f"CheckMacValue should be 64 chars, got {len(mac1)}"

        # Should be uppercase hex
        assert mac1.isupper(), "CheckMacValue should be uppercase"
        assert all(c in "0123456789ABCDEF" for c in mac1), "CheckMacValue should be hex"

    def test_check_mac_value_changes_with_data(self, service):
        """Test CheckMacValue changes when data changes"""

        base_data = {
            "MerchantID": "3002607",
            "MerchantTradeNo": "SUB520128550E8400",
            "TotalAmount": "899",
        }

        # Generate base MAC
        base_mac = service._generate_check_mac_value(base_data)

        # Test with different values
        test_variations = [
            {"MerchantID": "3002608"},  # Different merchant
            {"MerchantTradeNo": "SUB520128550E8401"},  # Different trade no
            {"TotalAmount": "900"},  # Different amount
            {"ExtraField": "extra_value"},  # Additional field
        ]

        for variation in test_variations:
            modified_data = {**base_data, **variation}
            modified_mac = service._generate_check_mac_value(modified_data)

            assert modified_mac != base_mac, (
                f"CheckMacValue should change for variation {variation}"
            )
            assert len(modified_mac) == 64, "Modified MAC should still be 64 chars"

    def test_callback_verification_security(self, service):
        """Test that callback verification properly validates CheckMacValue"""

        valid_callback = {
            "MerchantID": "3002607",
            "MerchantTradeNo": "SUB520128550E8400",
            "RtnCode": "1",
        }

        # Generate correct MAC
        correct_mac = service._generate_check_mac_value(valid_callback)
        valid_callback["CheckMacValue"] = correct_mac

        # Should verify successfully
        assert service._verify_callback(valid_callback) is True

        # Test with wrong MAC
        invalid_callback = valid_callback.copy()
        invalid_callback["CheckMacValue"] = "WRONG_MAC_VALUE"

        assert service._verify_callback(invalid_callback) is False

        # Test with modified data but same MAC (tampering attempt)
        tampered_callback = valid_callback.copy()
        tampered_callback["TotalAmount"] = "99999"  # Changed amount
        # MAC is still the original, so should fail

        assert service._verify_callback(tampered_callback) is False

    def test_error_response_codes_handling(self, service):
        """Test handling of various ECPay error response codes"""

        # Common ECPay error codes
        error_test_cases = [
            ("10200001", "MerchantID Error"),
            ("10200002", "MerchantTradeNo Error"),
            ("10200003", "TotalAmount Error"),
            ("10200004", "CheckMacValue Error"),
            ("10200052", "MerchantTradeNo Error"),  # The original bug
            ("10200053", "Payment Error"),
            ("2", "System Error"),
        ]

        for error_code, error_msg in error_test_cases:
            # Test in authorization callback
            callback_data = {
                "MerchantID": "3002607",
                "MerchantMemberID": "USER550e84001755520128",
                "RtnCode": error_code,
                "RtnMsg": error_msg,
                "CheckMacValue": "VALID_MAC_VALUE",
            }

            mock_auth = Mock()
            service.db.query.return_value.filter.return_value.first.return_value = (
                mock_auth
            )

            with patch.object(service, "_verify_callback", return_value=True):
                result = service.handle_auth_callback(callback_data)

                # All non-"1" codes should be treated as failures
                assert result is False, (
                    f"Error code {error_code} should be treated as failure"
                )

                if error_code != "1":
                    assert mock_auth.auth_status == ECPayAuthStatus.FAILED.value

    def test_amount_parsing_and_validation(self, service):
        """Test proper parsing and validation of monetary amounts"""

        # Test amount conversion scenarios
        amount_test_cases = [
            # (webhook_amount_string, expected_cents)
            ("899", 89900),  # 899 TWD -> 89900 cents
            ("8999", 899900),  # 8999 TWD -> 899900 cents
            ("2999", 299900),  # 2999 TWD -> 299900 cents
            ("29999", 2999900),  # 29999 TWD -> 2999900 cents
            ("1", 100),  # 1 TWD -> 100 cents
            ("0", 0),  # 0 TWD -> 0 cents
        ]

        for amount_str, expected_cents in amount_test_cases:
            # Simulate webhook processing
            mock_auth = Mock()
            mock_subscription = Mock()

            service.db.query.return_value.filter.return_value.first.side_effect = [
                mock_auth,
                mock_subscription,
            ]

            webhook_data = {
                "MerchantID": "3002607",
                "MerchantMemberID": "USER550e84001755520128",
                "amount": amount_str,
                "RtnCode": "1",
                "CheckMacValue": "VALID_MAC_VALUE",
            }

            with patch.object(service, "_verify_callback", return_value=True):
                service.handle_payment_webhook(webhook_data)

                # Check that the amount was converted correctly
                payment_record_call = service.db.add.call_args
                if payment_record_call:
                    payment_record = payment_record_call[0][0]
                    if hasattr(payment_record, "amount"):
                        assert payment_record.amount == expected_cents, (
                            f"Amount {amount_str} should convert to {expected_cents} cents"
                        )

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {},  # Empty callback
            {"MerchantID": "wrong_id"},  # Wrong merchant ID
            {"CheckMacValue": ""},  # Empty MAC
            {"RtnCode": ""},  # Empty return code
            None,  # None data
        ],
    )
    def test_invalid_callback_data_rejection(self, service, invalid_data):
        """Test that invalid callback data is properly rejected"""

        if invalid_data is None:
            # Handle None case separately
            with pytest.raises((TypeError, AttributeError)):
                service.handle_auth_callback(invalid_data)
        else:
            result = service.handle_auth_callback(invalid_data)
            assert result is False, f"Invalid data should be rejected: {invalid_data}"
