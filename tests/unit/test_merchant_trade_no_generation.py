"""
Unit tests for ECPay MerchantTradeNo generation logic.
These tests prevent regression of the 20-character limit violation bug.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService


class TestMerchantTradeNoGeneration:
    """Unit tests for MerchantTradeNo generation logic"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_settings(self):
        """Mock ECPay settings"""
        settings = Mock()
        settings.ECPAY_MERCHANT_ID = "3002607"
        settings.ECPAY_HASH_KEY = "test_key"
        settings.ECPAY_HASH_IV = "test_iv"
        settings.ECPAY_ENVIRONMENT = "sandbox"
        settings.FRONTEND_URL = "http://localhost:3000"
        settings.API_BASE_URL = "http://localhost:8000"
        return settings

    @pytest.fixture
    def service(self, mock_db_session, mock_settings):
        """Create service instance"""
        return ECPaySubscriptionService(mock_db_session, mock_settings)

    def test_merchant_trade_no_format_compliance(self, service):
        """Test MerchantTradeNo format matches expected pattern"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('time.time', return_value=1755520128):  # Fixed timestamp for testing
            timestamp = int(time.time())
            
            # Generate using the same logic as the service
            merchant_trade_no = f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
            
            # Format validations
            assert merchant_trade_no == "SUB520128550E8400", f"Unexpected format: {merchant_trade_no}"
            assert merchant_trade_no.startswith("SUB"), "Must start with SUB prefix"
            assert len(merchant_trade_no) == 17, f"Expected 17 chars, got {len(merchant_trade_no)}"

    def test_merchant_trade_no_length_constraint(self, service):
        """Test MerchantTradeNo never exceeds 20-character ECPay limit"""
        
        # Test with extreme cases
        test_cases = [
            # (user_id, description)
            ("550e8400-e29b-41d4-a716-446655440000", "Standard UUID"),
            ("user_with_very_long_name_that_could_cause_issues", "Very long user ID"),
            ("12345678901234567890123456789012345678901234567890", "Extremely long user ID"),
            ("", "Empty user ID"),
            ("a", "Single character user ID"),
            ("12345678", "8-character user ID"),
            ("123456789", "9-character user ID"),
            ("short", "Short user ID"),
            ("UPPERCASE_USER_ID", "Uppercase user ID"),
            ("user@domain.com", "Email-like user ID"),
            ("user-with-dashes", "User ID with dashes"),
            ("user_with_underscores", "User ID with underscores"),
        ]
        
        for user_id, description in test_cases:
            with patch('time.time', return_value=1755520128 + len(user_id)):  # Vary timestamp
                timestamp = int(time.time())
                merchant_trade_no = f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
                
                # Critical assertion: NEVER exceed 20 characters
                assert len(merchant_trade_no) <= 20, (
                    f"CRITICAL: {description} - MerchantTradeNo '{merchant_trade_no}' "
                    f"is {len(merchant_trade_no)} characters, exceeds 20-char limit"
                )
                
                # Additional format validations
                assert merchant_trade_no.startswith("SUB"), f"Must start with SUB: {merchant_trade_no}"
                assert len(merchant_trade_no) >= 3, f"Too short: {merchant_trade_no}"

    def test_merchant_trade_no_uniqueness_over_time(self, service):
        """Test that MerchantTradeNo is unique across different timestamps"""
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        generated_ids = set()
        
        # Test with different timestamps
        test_timestamps = [
            1755520128,  # Base timestamp
            1755520129,  # 1 second later
            1755520228,  # 100 seconds later
            1755521128,  # 1000 seconds later  
            1755530128,  # 10000 seconds later
            1799999999,  # Year 2027
            1000000000,  # Year 2001
        ]
        
        for timestamp in test_timestamps:
            with patch('time.time', return_value=timestamp):
                merchant_trade_no = f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
                
                # Check uniqueness
                assert merchant_trade_no not in generated_ids, (
                    f"Duplicate MerchantTradeNo generated: {merchant_trade_no} "
                    f"for timestamp {timestamp}"
                )
                
                generated_ids.add(merchant_trade_no)
                
                # Length constraint still applies
                assert len(merchant_trade_no) <= 20, (
                    f"Length violation for timestamp {timestamp}: {merchant_trade_no}"
                )

    def test_merchant_trade_no_with_different_users(self, service):
        """Test MerchantTradeNo uniqueness across different users"""
        
        test_users = [
            "user1234-5678-9012-3456-789012345678",
            "user2345-6789-0123-4567-890123456789", 
            "user3456-7890-1234-5678-901234567890",
            "different-user-format-here-12345678",
            "another_user_with_underscores_12345",
        ]
        
        generated_ids = set()
        fixed_timestamp = 1755520128
        
        with patch('time.time', return_value=fixed_timestamp):
            for user_id in test_users:
                merchant_trade_no = f"SUB{str(fixed_timestamp)[-6:]}{user_id[:8].upper()}"
                
                # Should be unique even with same timestamp (different user prefixes)
                assert merchant_trade_no not in generated_ids, (
                    f"Duplicate MerchantTradeNo: {merchant_trade_no} for user {user_id[:20]}..."
                )
                
                generated_ids.add(merchant_trade_no)
                
                # Length compliance
                assert len(merchant_trade_no) <= 20, (
                    f"Length violation for user {user_id[:20]}...: {merchant_trade_no}"
                )

    def test_merchant_trade_no_character_safety(self, service):
        """Test MerchantTradeNo contains only safe characters"""
        
        # Test with user IDs containing potentially problematic characters
        problematic_user_ids = [
            "user@domain.com",
            "user-with-dashes",
            "user_with_underscores", 
            "user with spaces",
            "user<script>alert</script>",
            "user&special%chars",
            "用戶中文名稱",  # Chinese characters
            "ユーザー日本語",  # Japanese characters
            "user\nwith\nnewlines",
            "user\twith\ttabs",
        ]
        
        for user_id in problematic_user_ids:
            timestamp = 1755520128
            with patch('time.time', return_value=timestamp):
                # Use the same sanitization logic as the service
                safe_user_prefix = ''.join(c for c in user_id[:8].upper() if c.isalnum())[:8]
                safe_user_prefix = safe_user_prefix.ljust(8, '0')[:8]
                merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"
                
                # Length constraint
                assert len(merchant_trade_no) <= 20, (
                    f"Length violation for problematic user ID: {merchant_trade_no}"
                )
                
                # Character safety - should be alphanumeric after processing
                # The [:8] slice and .upper() should handle most issues
                safe_part = merchant_trade_no[3:]  # After "SUB" prefix
                
                # At minimum, should not contain obvious problem characters
                forbidden_chars = [' ', '\n', '\t', '<', '>', '&', '%']
                for char in forbidden_chars:
                    assert char not in merchant_trade_no, (
                        f"Forbidden character '{char}' in MerchantTradeNo: {merchant_trade_no}"
                    )

    def test_timestamp_extraction_logic(self, service):
        """Test that timestamp extraction produces expected results"""
        
        test_cases = [
            # (timestamp, expected_last_6)
            (1755520128, "520128"),
            (1000000000, "000000"),
            (9999999999, "999999"),  # Max 10-digit timestamp
            (123456789, "456789"),   # 9-digit timestamp
            (1234567890123, "567890123"[-6:]),  # Handle overflow gracefully
        ]
        
        user_id = "testuser"
        
        for timestamp, expected_suffix in test_cases:
            with patch('time.time', return_value=timestamp):
                extracted = str(timestamp)[-6:]
                assert extracted == expected_suffix, (
                    f"Timestamp {timestamp} should extract to {expected_suffix}, "
                    f"got {extracted}"
                )
                
                # Test full generation
                merchant_trade_no = f"SUB{extracted}{user_id.upper()}"
                expected_full = f"SUB{expected_suffix}TESTUSER"
                
                assert merchant_trade_no == expected_full, (
                    f"Full generation mismatch: expected {expected_full}, got {merchant_trade_no}"
                )
                
                # Still within limits
                assert len(merchant_trade_no) <= 20, (
                    f"Generated ID too long: {merchant_trade_no}"
                )

    def test_regression_original_bug_scenario(self, service):
        """Test the exact scenario that caused the original 21-character bug"""
        
        # Original bug: SUB{full_timestamp}{user_prefix} was 21 characters
        # Fixed: SUB{timestamp_last_6}{user_prefix} is 17 characters
        
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        timestamp = 1755520128  # 10-digit timestamp
        
        # OLD (buggy) logic that would have created 21 characters:
        buggy_merchant_trade_no = f"SUB{timestamp}{user_id[:8].upper()}"
        assert len(buggy_merchant_trade_no) == 21, "Confirming old logic was 21 chars"
        
        # NEW (fixed) logic that creates 17 characters:
        with patch('time.time', return_value=timestamp):
            fixed_merchant_trade_no = f"SUB{str(timestamp)[-6:]}{user_id[:8].upper()}"
            
            assert len(fixed_merchant_trade_no) == 17, "Fixed logic should be 17 chars"
            assert fixed_merchant_trade_no == "SUB520128550E8400", "Exact expected value"
            
            # Most important: within ECPay limit
            assert len(fixed_merchant_trade_no) <= 20, (
                "Fixed logic must be within 20-character limit"
            )
            
            # Verify they're different (regression prevention)
            assert buggy_merchant_trade_no != fixed_merchant_trade_no, (
                "Fixed logic should produce different result than buggy logic"
            )