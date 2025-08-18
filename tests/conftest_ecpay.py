"""
Pytest configuration specifically for ECPay tests.
This file provides fixtures and utilities for ECPay testing.
"""

import pytest
import os
from unittest.mock import Mock, patch

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"
os.environ["ECPAY_MERCHANT_ID"] = "3002607"
os.environ["ECPAY_HASH_KEY"] = "pwFHCqoQZGmho4w6" 
os.environ["ECPAY_HASH_IV"] = "EkRm7iFT261dpevs"
os.environ["ECPAY_ENVIRONMENT"] = "sandbox"


@pytest.fixture
def ecpay_test_settings():
    """ECPay test configuration settings"""
    settings = Mock()
    settings.ECPAY_MERCHANT_ID = "3002607"
    settings.ECPAY_HASH_KEY = "pwFHCqoQZGmho4w6"
    settings.ECPAY_HASH_IV = "EkRm7iFT261dpevs"
    settings.ECPAY_ENVIRONMENT = "sandbox"
    settings.FRONTEND_URL = "http://localhost:3000"
    settings.API_BASE_URL = "http://localhost:8000"
    return settings


@pytest.fixture
def mock_db():
    """Mock database session for testing"""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_auth_callback_data():
    """Sample ECPay authorization callback data"""
    return {
        "MerchantID": "3002607",
        "MerchantMemberID": "USER550e84001755520128",
        "MerchantTradeNo": "SUB520128550E8400",
        "RtnCode": "1",
        "gwsr": "123456789",
        "AuthCode": "AUTH123456",
        "card4no": "4242",
        "card6no": "424242",
        "CheckMacValue": "VALID_TEST_MAC_VALUE"
    }


@pytest.fixture
def sample_payment_webhook_data():
    """Sample ECPay payment webhook data"""
    return {
        "MerchantID": "3002607",
        "MerchantMemberID": "USER550e84001755520128",
        "gwsr": "987654321",
        "RtnCode": "1",
        "amount": "899",
        "CheckMacValue": "VALID_TEST_MAC_VALUE"
    }


class ECPayTestHelper:
    """Helper class for ECPay testing utilities"""
    
    @staticmethod
    def generate_test_merchant_trade_no(timestamp=1755520128, user_id="550e8400"):
        """Generate test MerchantTradeNo using the fixed logic"""
        return f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
    
    @staticmethod
    def validate_merchant_trade_no_length(trade_no):
        """Validate MerchantTradeNo length constraint"""
        return len(trade_no) <= 20
    
    @staticmethod
    def validate_required_fields(form_data):
        """Validate all required ECPay fields are present"""
        required_fields = [
            "MerchantID", "MerchantMemberID", "MerchantTradeNo", "ActionType",
            "TotalAmount", "ProductDesc", "OrderResultURL", "ReturnURL",
            "ClientBackURL", "PeriodType", "Frequency", "PeriodAmount",
            "ExecTimes", "PaymentType", "ChoosePayment", "TradeDesc",
            "ItemName", "MerchantTradeDate", "ExpireDate", "CheckMacValue"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in form_data or form_data[field] is None or str(form_data[field]).strip() == "":
                missing_fields.append(field)
        
        return missing_fields


@pytest.fixture
def ecpay_helper():
    """ECPay test helper fixture"""
    return ECPayTestHelper()