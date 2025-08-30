#!/usr/bin/env python3
"""
Receipt Download Test Runner

Comprehensive test suite for the receipt download functionality
"""

import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_receipt_tests(test_type="all", verbose=False):
    """
    Run receipt download tests.
    
    Args:
        test_type: Type of tests to run ("unit", "api", "e2e", or "all")
        verbose: Enable verbose output
    """
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if verbose:
        pytest_cmd.extend(["-v", "-s"])
    
    # Add coverage reporting
    pytest_cmd.extend([
        "--cov=coaching_assistant.api.v1.subscriptions",
        "--cov-report=html:htmlcov/receipt_tests",
        "--cov-report=term-missing"
    ])
    
    # Determine which tests to run
    test_files = []
    
    if test_type in ["unit", "all"]:
        test_files.append("tests/unit/api/test_receipt_generation.py")
        logger.info("🔧 Including unit tests for receipt generation logic")
    
    if test_type in ["api", "all"]:
        test_files.append("tests/api/test_receipt_download.py")
        logger.info("🌐 Including API integration tests for receipt endpoints")
    
    if test_type in ["e2e", "all"]:
        test_files.append("tests/e2e/test_receipt_download_e2e.py")
        logger.info("🎯 Including end-to-end tests for complete receipt flow")
    
    if not test_files:
        logger.error(f"❌ Unknown test type: {test_type}")
        return False
    
    # Add test files to command
    pytest_cmd.extend(test_files)
    
    # Add test markers and configuration
    pytest_cmd.extend([
        "--tb=short",
        "--color=yes",
        "-x"  # Stop on first failure for faster feedback
    ])
    
    logger.info("🚀 Starting receipt download tests...")
    logger.info(f"📋 Command: {' '.join(pytest_cmd)}")
    
    try:
        # Run the tests
        result = subprocess.run(pytest_cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            logger.info("✅ All receipt tests passed!")
            logger.info("📊 Coverage report generated in htmlcov/receipt_tests/")
            return True
        else:
            logger.error(f"❌ Tests failed with return code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        logger.error("❌ pytest not found. Install with: pip install pytest pytest-cov")
        return False
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return False

def check_test_dependencies():
    """Check if required test dependencies are installed."""
    
    required_packages = [
        "pytest",
        "pytest-cov", 
        "fastapi",
        "sqlalchemy",
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"❌ Missing required packages: {', '.join(missing)}")
        logger.info(f"💡 Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def display_test_summary():
    """Display information about the receipt tests."""
    
    print("\n📋 Receipt Download Test Suite")
    print("=" * 50)
    print()
    print("🔧 Unit Tests (test_receipt_generation.py):")
    print("   - Receipt data structure validation")
    print("   - Receipt ID generation logic") 
    print("   - Amount conversion (cents to TWD)")
    print("   - Date formatting")
    print("   - User name fallback logic")
    print("   - Business rule validation")
    print("   - Localization and security")
    print()
    print("🌐 API Tests (test_receipt_download.py):")
    print("   - Successful receipt generation")
    print("   - Payment not found handling")
    print("   - Unauthorized access prevention")
    print("   - Failed payment rejection")
    print("   - Receipt ID format consistency")
    print("   - Amount conversion accuracy")
    print()
    print("🎯 E2E Tests (test_receipt_download_e2e.py):")
    print("   - Complete receipt download flow")
    print("   - Multiple subscription plans")
    print("   - Error handling scenarios")
    print("   - Receipt accessibility & format")
    print("   - HTML generation simulation")
    print()
    print("Usage Examples:")
    print("  python tests/run_receipt_tests.py --type unit")
    print("  python tests/run_receipt_tests.py --type api --verbose")
    print("  python tests/run_receipt_tests.py --type e2e")
    print("  python tests/run_receipt_tests.py --type all")
    print()

def main():
    """Main test runner function."""
    
    parser = argparse.ArgumentParser(
        description="Run receipt download functionality tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "api", "e2e", "all"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display test information and exit"
    )
    
    args = parser.parse_args()
    
    if args.info:
        display_test_summary()
        return 0
    
    # Check dependencies
    if not check_test_dependencies():
        return 1
    
    # Run tests
    success = run_receipt_tests(args.type, args.verbose)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())