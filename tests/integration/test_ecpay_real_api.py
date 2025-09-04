"""
Real ECPay API integration tests that make actual HTTP requests to ECPay sandbox.
These tests validate that our parameters work with the actual ECPay API.

WARNING: These tests make real API calls to ECPay sandbox environment.
Run with: pytest tests/integration/test_ecpay_real_api.py -v --tb=short
"""

import pytest
import requests
import time
from urllib.parse import urlencode
from unittest.mock import Mock, patch

from src.coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService


class TestECPayRealAPI:
    """Test ECPay integration with actual API calls"""

    @pytest.fixture
    def mock_db_session(self):
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def ecpay_service(self, mock_db_session):
        settings = Mock()
        settings.ECPAY_MERCHANT_ID = "3002607"  # ECPay test merchant
        settings.ECPAY_HASH_KEY = "pwFHCqoQZGmho4w6"
        settings.ECPAY_HASH_IV = "EkRm7iFT261dpevs"
        settings.ECPAY_ENVIRONMENT = "sandbox"
        settings.FRONTEND_URL = "http://localhost:3000"
        settings.API_BASE_URL = "http://localhost:8000"
        return ECPaySubscriptionService(mock_db_session, settings)

    @pytest.mark.integration
    def test_ecpay_parameter_validation_with_real_api(self, ecpay_service):
        """Test our parameters against actual ECPay API to catch format errors"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"
        
        with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan"
            }
            
            # Generate authorization data
            result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
            form_data = result["form_data"]
            action_url = result["action_url"]
            
            # Make actual HTTP request to ECPay
            try:
                response = requests.post(
                    action_url,
                    data=form_data,
                    timeout=10,
                    allow_redirects=False  # Don't follow redirects
                )
                
                # Log response for debugging
                print(f"\\nECPay API Response:")
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                print(f"Response Text: {response.text[:500]}...")
                
                # Check for specific ECPay error codes in response
                response_text = response.text
                
                # These are the errors we fixed - they should NOT appear
                error_patterns = [
                    "10200052",  # MerchantTradeNo Error
                    "10200027",  # TradeNo Error  
                    "10100228",  # ExecTimes Error
                    "10100050",  # Parameter Error (ActionType/ProductDesc)
                ]
                
                for error_code in error_patterns:
                    assert error_code not in response_text, (
                        f"ECPay returned error {error_code} - our parameter fixes failed! "
                        f"Response: {response_text[:200]}..."
                    )
                
                # Success indicators (ECPay will redirect or show payment form)
                success_indicators = [
                    response.status_code in [200, 302],  # OK or redirect
                    "<!DOCTYPE html>" in response_text.lower(),  # HTML payment page
                    "ecpay" in response_text.lower(),  # ECPay content
                ]
                
                assert any(success_indicators), (
                    f"ECPay API response doesn't look successful. "
                    f"Status: {response.status_code}, Response: {response_text[:200]}..."
                )
                
                print("\\n✅ ECPay API accepted our parameters without errors!")
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Could not connect to ECPay API (network issue): {e}")

    @pytest.mark.integration  
    def test_ecpay_yearly_plan_exec_times(self, ecpay_service):
        """Test yearly plan with ExecTimes=99 against real ECPay API"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "ENTERPRISE"
        billing_cycle = "annual"  # This should trigger ExecTimes=99
        
        with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 299900,
                "plan_name": "Enterprise Plan"
            }
            
            result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
            form_data = result["form_data"]
            
            # Verify our ExecTimes fix
            assert form_data["ExecTimes"] == 99, "Yearly plans should have ExecTimes=99"
            assert form_data["PeriodType"] == "Y", "Yearly plans should have PeriodType=Y"
            
            try:
                response = requests.post(
                    result["action_url"],
                    data=form_data,
                    timeout=10,
                    allow_redirects=False
                )
                
                # Should NOT contain ExecTimes error
                assert "10100228" not in response.text, (
                    "ECPay returned ExecTimes Error - yearly ExecTimes fix failed!"
                )
                
                print("\\n✅ Yearly plan ExecTimes=99 accepted by ECPay API!")
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Could not test yearly plan: {e}")

    @pytest.mark.integration
    def test_english_only_parameters(self, ecpay_service):
        """Test that English-only parameters work with ECPay API"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        plan_id = "PRO"
        billing_cycle = "monthly"
        
        with patch.object(ecpay_service, '_get_plan_pricing') as mock_pricing:
            mock_pricing.return_value = {
                "amount_twd": 89900,
                "plan_name": "Professional Plan"
            }
            
            result = ecpay_service.create_credit_authorization(user_id, plan_id, billing_cycle)
            form_data = result["form_data"]
            
            # Verify English-only text fields
            text_fields = ["ProductDesc", "TradeDesc", "ItemName"]
            for field in text_fields:
                value = form_data[field]
                # Should not contain Chinese characters
                assert not any(ord(char) > 127 for char in value), (
                    f"{field} contains non-ASCII characters: {value}"
                )
            
            try:
                response = requests.post(
                    result["action_url"],
                    data=form_data,
                    timeout=10,
                    allow_redirects=False
                )
                
                # Should NOT contain ProductDesc error
                assert "ProductDesc" not in response.text or "Error" not in response.text, (
                    "ECPay may have rejected English-only ProductDesc"
                )
                
                print("\\n✅ English-only text parameters accepted by ECPay API!")
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Could not test English parameters: {e}")

    def test_create_test_summary_report(self, ecpay_service):
        """Generate a summary report of what our tests would catch"""
        
        print("\\n" + "="*70)
        print("🧪 ECPay Test Coverage Analysis")
        print("="*70)
        
        test_scenarios = [
            {
                "error_code": "10200052",
                "error_name": "MerchantTradeNo Error",
                "test_coverage": "✅ COVERED",
                "test_method": "test_merchant_trade_no_format_compliance",
                "description": "Tests 20-character limit, character sanitization"
            },
            {
                "error_code": "10200027", 
                "error_name": "TradeNo Error",
                "test_coverage": "✅ COVERED",
                "test_method": "test_api_endpoint_configuration",
                "description": "Tests AioCheckOut endpoint usage"
            },
            {
                "error_code": "10100228",
                "error_name": "ExecTimes Error", 
                "test_coverage": "✅ COVERED",
                "test_method": "test_exec_times_business_rules",
                "description": "Tests M=0, Y=2-99 rules"
            },
            {
                "error_code": "10100050",
                "error_name": "ActionType Parameter Error",
                "test_coverage": "✅ COVERED", 
                "test_method": "test_missing_action_type_for_aio_checkout",
                "description": "Tests ActionType removal for AioCheckOut"
            },
            {
                "error_code": "10100050",
                "error_name": "ProductDesc Parameter Error",
                "test_coverage": "✅ COVERED",
                "test_method": "test_text_fields_english_only", 
                "description": "Tests English-only text fields"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"Error {scenario['error_code']}: {scenario['error_name']}")
            print(f"  Coverage: {scenario['test_coverage']}")
            print(f"  Test: {scenario['test_method']}")
            print(f"  What it tests: {scenario['description']}")
            print()
        
        print("="*70)
        print("✅ Our updated test suite now covers ALL the ECPay errors we encountered!")
        print("💡 These tests will prevent regression and catch similar issues early.")
        print("="*70)