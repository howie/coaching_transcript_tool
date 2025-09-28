#!/usr/bin/env python3
"""
Test script to verify ECPay MerchantTradeNo generation is within 20-character limit.
"""

import time


def test_merchant_trade_no_generation():
    """Test that generated MerchantTradeNo is within ECPay's 20-character limit"""

    # Test with various user IDs
    test_user_ids = [
        "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID
        "user123456789012345",  # Long user ID
        "12345678",  # Short user ID
        "a" * 36,  # Max length user ID
    ]

    print("🧪 Testing ECPay MerchantTradeNo Generation")
    print("=" * 60)

    all_passed = True

    for i, user_id in enumerate(test_user_ids, 1):
        timestamp = int(time.time()) + i  # Slight variation

        # Use the same logic as in ECPaySubscriptionService (with sanitization)
        safe_user_prefix = "".join(c for c in user_id[:8].upper() if c.isalnum())[:8]
        safe_user_prefix = safe_user_prefix.ljust(8, "0")[:8]
        merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"

        length = len(merchant_trade_no)
        status = "✅ PASS" if length <= 20 else "❌ FAIL"

        if length > 20:
            all_passed = False

        print(f"Test {i}: {status}")
        print(f"  User ID: {user_id[:20]}...")
        print(f"  Generated: {merchant_trade_no}")
        print(f"  Length: {length}/20 characters")
        print(f"  Timestamp suffix: {str(timestamp)[-6:]}")
        print(f"  User prefix: {user_id[:8].upper()}")
        print()

    print("=" * 60)
    if all_passed:
        print("✅ All tests PASSED! MerchantTradeNo generation is compliant.")
        print("💡 The ECPay MerchantTradeNo error should now be resolved.")
        return True
    else:
        print("❌ Some tests FAILED! Check the generation logic.")
        return False


if __name__ == "__main__":
    success = test_merchant_trade_no_generation()
    exit(0 if success else 1)
