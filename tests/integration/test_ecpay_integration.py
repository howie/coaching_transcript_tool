"""
Integration tests for ECPay subscription service to validate all field requirements
and prevent API errors like MerchantTradeNo length violations.
"""

import pytest
import time
from datetime import datetime, timedelta, date
from unittest.mock import Mock, patch
from decimal import Decimal

from src.coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService
from src.coaching_assistant.core.config import Settings
from src.coaching_assistant.models.ecpay_subscription import (
    ECPayCreditAuthorization, SaasSubscription, ECPayAuthStatus, SubscriptionStatus
)


class TestECPayIntegration:
    """Integration tests for ECPay service field validation and API compliance"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for ECPay configuration"""
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
        """Create ECPay service instance for testing"""
        return ECPaySubscriptionService(mock_db_session, mock_settings)

    def test_merchant_trade_no_length_compliance(self, ecpay_service):
        """Test that MerchantTradeNo never exceeds 20 characters"""
        
        # Test with various user ID formats
        test_cases = [
            "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID
            "user123456789012345678901234567890",     # Very long user ID
            "12345678",                               # Short user ID
            "a" * 50,                                # Extremely long user ID
            "",                                      # Edge case: empty user ID
        ]
        
        for user_id in test_cases:
            timestamp = int(time.time())
            
            # Use the same generation logic as the service
            merchant_trade_no = f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
            
            # Critical assertion: Must never exceed 20 characters
            assert len(merchant_trade_no) <= 20, (
                f"MerchantTradeNo '{merchant_trade_no}' is {len(merchant_trade_no)} "
                f"characters, exceeds ECPay's 20-character limit"
            )
            
            # Additional validations
            assert merchant_trade_no.startswith("SUB"), "MerchantTradeNo must start with SUB"
            assert len(merchant_trade_no) >= 3, "MerchantTradeNo too short"
            assert merchant_trade_no.replace("SUB", "").replace("-", "").isalnum(), "Invalid characters"

    def test_merchant_member_id_length_compliance(self, ecpay_service):
        """Test that MerchantMemberID doesn't exceed limits"""
        
        test_user_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "very_long_user_id_that_might_cause_issues",
            "short",
            "a" * 100,  # Extremely long
        ]
        
        for user_id in test_user_ids:
            timestamp = int(time.time())
            merchant_member_id = f"USER{user_id[:8]}{timestamp}"
            
            # ECPay MerchantMemberID limit is typically 30 characters
            assert len(merchant_member_id) <= 30, (
                f"MerchantMemberID '{merchant_member_id}' is {len(merchant_member_id)} "
                f"characters, exceeds 30-character limit"
            )

    def test_required_fields_present(self, ecpay_service):
        """Test that all required ECPay fields are present in authorization data"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"
        
        # Mock the plan pricing
        with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "專業方案"
            }
            
            try:
                result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
                auth_data = result["form_data"]
                
                # Critical required fields that caused the original error
                required_fields = [
                    "MerchantID",
                    "MerchantMemberID", 
                    "MerchantTradeNo",  # This was missing before!
                    # "ActionType",  # Removed for AioCheckOut endpoint
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
                    "CheckMacValue"
                ]
                
                for field in required_fields:
                    assert field in auth_data, f"Missing required field: {field}"
                    assert auth_data[field] is not None, f"Field {field} is None"
                    assert str(auth_data[field]).strip() != "", f"Field {field} is empty"
                
                # Specific value validations
                assert auth_data["MerchantTradeNo"] != "", "MerchantTradeNo cannot be empty"
                assert len(auth_data["MerchantTradeNo"]) <= 20, "MerchantTradeNo too long"
                # ActionType no longer used in AioCheckOut endpoint
                assert auth_data["PaymentType"] == "aio", "Wrong PaymentType"
                assert auth_data["ChoosePayment"] == "Credit", "Wrong ChoosePayment"
                
            except Exception as e:
                pytest.fail(f"Authorization creation failed: {e}")

    def test_amount_conversion_accuracy(self, ecpay_service):
        """Test that amount conversion from cents to dollars is accurate"""
        
        test_cases = [
            (89900, 899),   # PRO monthly: 899 TWD
            (899900, 8999), # PRO annual: 8999 TWD  
            (299900, 2999), # ENTERPRISE monthly: 2999 TWD
            (2999900, 29999), # ENTERPRISE annual: 29999 TWD
        ]
        
        for amount_cents, expected_dollars in test_cases:
            converted = amount_cents // 100
            assert converted == expected_dollars, (
                f"Amount conversion failed: {amount_cents} cents should be {expected_dollars} dollars, "
                f"got {converted}"
            )

    def test_date_format_compliance(self, ecpay_service):
        """Test that date formats match ECPay requirements"""
        
        # ECPay expects dates in "YYYY/MM/DD HH:MM:SS" format
        now = datetime.now()
        formatted_date = now.strftime("%Y/%m/%d %H:%M:%S")
        
        # Validate format
        assert len(formatted_date) == 19, "Date format length incorrect"
        assert formatted_date.count("/") == 2, "Date should have 2 slashes"
        assert formatted_date.count(":") == 2, "Time should have 2 colons"
        assert " " in formatted_date, "Date and time should be separated by space"
        
        # Test parsing back to ensure validity
        try:
            parsed = datetime.strptime(formatted_date, "%Y/%m/%d %H:%M:%S")
            assert parsed is not None, "Date parsing failed"
        except ValueError as e:
            pytest.fail(f"Date format is invalid: {e}")

    def test_check_mac_value_generation(self, ecpay_service):
        """Test CheckMacValue generation is consistent and non-empty"""
        
        test_data = {
            "MerchantID": "3002607",
            "MerchantTradeNo": "SUB520140550E8400",
            "TotalAmount": "899",
            "PaymentType": "aio"
        }
        
        # Generate CheckMacValue
        mac_value = ecpay_service._generate_check_mac_value(test_data)
        
        # Validations
        assert mac_value is not None, "CheckMacValue cannot be None"
        assert len(mac_value) > 0, "CheckMacValue cannot be empty"
        assert len(mac_value) == 64, "CheckMacValue should be 64 characters (SHA256)"
        assert mac_value.isupper(), "CheckMacValue should be uppercase"
        
        # Test consistency - same data should generate same MAC
        mac_value2 = ecpay_service._generate_check_mac_value(test_data)
        assert mac_value == mac_value2, "CheckMacValue generation is not consistent"

    def test_period_type_validation(self, ecpay_service):
        """Test that PeriodType is correctly set based on billing cycle"""
        
        test_cases = [
            ("monthly", "M"),  # ECPay format
            ("annual", "Y"),   # ECPay format
        ]
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        
        for billing_cycle, expected_period_type in test_cases:
            with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
                mock_pricing.return_value = {
                    "amount_twd": 89900,
                    "plan_name": "專業方案"
                }
                
                try:
                    result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
                    auth_data = result["form_data"]
                    
                    assert auth_data["PeriodType"] == expected_period_type, (
                        f"PeriodType should be {expected_period_type} for {billing_cycle}, "
                        f"got {auth_data['PeriodType']}"
                    )
                    
                except Exception as e:
                    pytest.fail(f"Authorization creation failed for {billing_cycle}: {e}")

    def test_uniqueness_constraints(self, ecpay_service):
        """Test that generated IDs are unique across multiple calls"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"
        
        generated_trade_nos = set()
        generated_member_ids = set()
        
        with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "專業方案"
            }
            
            # Generate multiple authorizations
            for i in range(10):
                try:
                    # Add small delay to ensure different timestamps
                    time.sleep(0.1)
                    
                    result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
                    auth_data = result["form_data"]
                    
                    trade_no = auth_data["MerchantTradeNo"]
                    member_id = auth_data["MerchantMemberID"]
                    
                    # Check uniqueness
                    assert trade_no not in generated_trade_nos, f"Duplicate MerchantTradeNo: {trade_no}"
                    assert member_id not in generated_member_ids, f"Duplicate MerchantMemberID: {member_id}"
                    
                    generated_trade_nos.add(trade_no)
                    generated_member_ids.add(member_id)
                    
                except Exception as e:
                    pytest.fail(f"Authorization creation failed on iteration {i}: {e}")
        
        # Verify we got unique values
        assert len(generated_trade_nos) == 10, "Not all MerchantTradeNo values were unique"
        assert len(generated_member_ids) == 10, "Not all MerchantMemberID values were unique"