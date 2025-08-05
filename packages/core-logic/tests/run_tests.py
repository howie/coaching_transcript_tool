#!/usr/bin/env python3
"""
Test runner script for the Coaching Assistant authentication system.

This script provides easy commands to run different types of tests:
- Unit tests: Test individual functions in isolation
- Integration tests: Test complete API endpoints and flows
- All tests: Run the complete test suite

Usage:
    python run_tests.py unit          # Run unit tests only
    python run_tests.py integration   # Run integration tests only
    python run_tests.py all           # Run all tests
    python run_tests.py              # Run all tests (default)
"""

import sys
import subprocess
import os
from pathlib import Path

# Add the src directory to Python path so we can import the modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

def run_unit_tests():
    """Run unit tests only"""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/api/test_auth.py",
        "-v",
        "-k", "TestPasswordHashing or TestJWTTokens",
        "--tb=short"
    ]
    
    return run_command(cmd)

def run_integration_tests():
    """Run integration tests only"""
    print("🔗 Running Integration Tests...")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/api/test_auth.py",
        "-v", 
        "-k", "not (TestPasswordHashing or TestJWTTokens)",
        "--tb=short"
    ]
    
    return run_command(cmd)

def run_all_tests():
    """Run all tests"""
    print("🚀 Running All Tests...")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/api/test_auth.py",
        "-v",
        "--tb=short",
        "--cov=coaching_assistant.api.auth",
        "--cov-report=term-missing"
    ]
    
    return run_command(cmd)

def run_tests_with_coverage():
    """Run all tests with detailed coverage report"""
    print("📊 Running Tests with Coverage Analysis...")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/api/test_auth.py",
        "-v",
        "--tb=short",
        "--cov=coaching_assistant.api.auth",
        "--cov=coaching_assistant.models.user",
        "--cov=coaching_assistant.core.config",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    success = run_command(cmd)
    
    if success:
        print("\n📈 Coverage report generated in 'htmlcov/' directory")
        print("Open 'htmlcov/index.html' in your browser to view detailed coverage")
    
    return success

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    
    dependencies = [
        "pytest",
        "pytest-cov", 
        "pytest-asyncio",
        "httpx",
        "fastapi[all]",
        "sqlalchemy",
        "python-jose[cryptography]",
        "passlib",
        "python-multipart"
    ]
    
    for dep in dependencies:
        cmd = ["pip", "install", dep]
        print(f"Installing {dep}...")
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f"❌ Failed to install {dep}")
            return False
    
    print("✅ All test dependencies installed successfully!")
    return True

def check_environment():
    """Check if the test environment is properly set up"""
    print("🔍 Checking test environment...")
    
    # Check if we're in the right directory
    if not os.path.exists("tests/api/test_auth.py"):
        print("❌ test_auth.py not found. Please run this script from packages/core-logic/")
        return False
    
    # Check if source code exists
    if not os.path.exists("src/coaching_assistant"):
        print("❌ Source code not found. Please run this script from packages/core-logic/")
        return False
    
    # Try to import required modules
    try:
        import pytest
        import httpx
        import fastapi
        import sqlalchemy
        import jose
        import passlib
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: python run_tests.py install-deps")
        return False
    
    print("✅ Test environment is ready!")
    return True

def main():
    """Main function to handle command line arguments"""
    
    # Change to the correct directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        command = "all"
    
    if command == "install-deps":
        success = install_test_dependencies()
        sys.exit(0 if success else 1)
    
    if command == "check":
        success = check_environment()
        sys.exit(0 if success else 1)
    
    # Check environment before running tests
    if not check_environment():
        print("\n💡 Try running: python run_tests.py install-deps")
        sys.exit(1)
    
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.executable}")
    print("-" * 50)
    
    if command == "unit":
        success = run_unit_tests()
    elif command == "integration":
        success = run_integration_tests()
    elif command == "coverage":
        success = run_tests_with_coverage()
    elif command in ["all", ""]:
        success = run_all_tests()
    else:
        print(f"❌ Unknown command: {command}")
        print("\nAvailable commands:")
        print("  unit         - Run unit tests only")
        print("  integration  - Run integration tests only") 
        print("  all          - Run all tests (default)")
        print("  coverage     - Run tests with coverage analysis")
        print("  install-deps - Install test dependencies")
        print("  check        - Check test environment")
        sys.exit(1)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
