#!/usr/bin/env python3
"""
ECPay Test Runner - Comprehensive test suite to prevent regression of ECPay integration bugs.

This script runs all ECPay-related tests including:
- Unit tests for MerchantTradeNo generation
- Integration tests for field validation
- API response validation tests
- E2E tests for authorization flow

Usage:
    From project root: python tests/run_ecpay_tests.py [--verbose] [--coverage]
"""

import subprocess
import sys
import argparse
import os
from pathlib import Path

# Ensure we're running from project root
if not Path("src/coaching_assistant").exists():
    print("❌ Please run this script from the project root directory")
    print("   Usage: python tests/run_ecpay_tests.py")
    sys.exit(1)

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🔄 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run ECPay integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    
    args = parser.parse_args()
    
    print("🚀 ECPay Test Suite - Preventing Regression Bugs")
    print("=" * 60)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    if args.verbose:
        pytest_cmd.append("-v")
    if args.coverage:
        pytest_cmd.extend(["--cov=src/coaching_assistant/core/services/ecpay_service", "--cov-report=html"])
    
    test_results = []
    
    # 1. Unit Tests - MerchantTradeNo Generation
    if not args.integration_only:
        print("\n📋 UNIT TESTS")
        print("-" * 30)
        
        unit_tests = [
            ("tests/unit/test_merchant_trade_no_generation.py::TestMerchantTradeNoGeneration::test_merchant_trade_no_length_constraint", 
             "Length Constraint Validation"),
            ("tests/unit/test_merchant_trade_no_generation.py::TestMerchantTradeNoGeneration::test_regression_original_bug_scenario",
             "Original Bug Regression Test"),
            ("tests/unit/test_merchant_trade_no_generation.py::TestMerchantTradeNoGeneration::test_merchant_trade_no_uniqueness_over_time",
             "Uniqueness Over Time"),
            ("tests/unit/test_merchant_trade_no_generation.py::TestMerchantTradeNoGeneration::test_merchant_trade_no_character_safety",
             "Character Safety Validation"),
        ]
        
        for test_path, description in unit_tests:
            result = run_command(pytest_cmd + [test_path], f"Unit Test: {description}")
            test_results.append((f"Unit: {description}", result))
    
    # 2. Integration Tests - Field Validation
    if not args.unit_only:
        print("\n🔗 INTEGRATION TESTS")
        print("-" * 30)
        
        integration_tests = [
            ("tests/integration/test_ecpay_integration.py::TestECPayIntegration::test_merchant_trade_no_length_compliance",
             "MerchantTradeNo Length Compliance"),
            ("tests/integration/test_ecpay_integration.py::TestECPayIntegration::test_required_fields_present",
             "Required Fields Validation"),
            ("tests/integration/test_ecpay_integration.py::TestECPayIntegration::test_check_mac_value_generation",
             "CheckMacValue Generation"),
            ("tests/integration/test_ecpay_integration.py::TestECPayIntegration::test_uniqueness_constraints",
             "Uniqueness Constraints"),
        ]
        
        for test_path, description in integration_tests:
            result = run_command(pytest_cmd + [test_path], f"Integration Test: {description}")
            test_results.append((f"Integration: {description}", result))
    
    # 3. API Response Validation Tests  
    if not args.unit_only:
        print("\n🌐 API VALIDATION TESTS")
        print("-" * 30)
        
        api_tests = [
            ("tests/unit/test_ecpay_api_response_validation.py::TestECPayAPIResponseValidation::test_successful_auth_callback_handling",
             "Successful Auth Callback"),
            ("tests/unit/test_ecpay_api_response_validation.py::TestECPayAPIResponseValidation::test_failed_auth_callback_handling", 
             "Failed Auth Callback"),
            ("tests/unit/test_ecpay_api_response_validation.py::TestECPayAPIResponseValidation::test_check_mac_value_generation_consistency",
             "CheckMacValue Consistency"),
            ("tests/unit/test_ecpay_api_response_validation.py::TestECPayAPIResponseValidation::test_callback_verification_security",
             "Callback Security Verification"),
        ]
        
        for test_path, description in api_tests:
            result = run_command(pytest_cmd + [test_path], f"API Test: {description}")
            test_results.append((f"API: {description}", result))
    
    # 4. Simple Test Scripts
    print("\n🔧 UTILITY TESTS")
    print("-" * 30)
    
    utility_tests = [
        (["python", "tests/unit/test_ecpay_merchant_trade_no.py"], "MerchantTradeNo Generation Utility"),
        (["python", "tests/integration/test_ecpay_flow.py"], "ECPay Integration Flow"),
    ]
    
    for cmd, description in utility_tests:
        if Path(cmd[1]).exists():
            result = run_command(cmd, f"Utility Test: {description}")
            test_results.append((f"Utility: {description}", result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_count = 0
    failed_count = 0
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} {test_name}")
        
        if passed:
            passed_count += 1
        else:
            failed_count += 1
    
    total_count = passed_count + failed_count
    
    print("-" * 60)
    print(f"Total Tests: {total_count}")
    print(f"Passed:     {passed_count}")
    print(f"Failed:     {failed_count}")
    print(f"Success Rate: {(passed_count/total_count*100 if total_count > 0 else 0):.1f}%")
    
    if failed_count == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ ECPay integration is protected against regression bugs.")
        print("✅ MerchantTradeNo length validation is working correctly.")
        print("✅ All required fields are properly validated.")
        return 0
    else:
        print(f"\n⚠️  {failed_count} TEST(S) FAILED!")
        print("❌ ECPay integration may have issues.")
        print("🔧 Please review failed tests and fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())