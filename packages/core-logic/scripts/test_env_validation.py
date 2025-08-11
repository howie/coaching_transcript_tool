#!/usr/bin/env python
"""Test script to demonstrate environment variable validation."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coaching_assistant.core.env_validator import EnvironmentValidator


def test_with_missing_vars():
    """Test validation with missing environment variables."""
    print("🧪 Testing validation with missing environment variables...")
    print("=" * 70)
    
    # Clear some environment variables temporarily
    original_values = {}
    test_vars = ["DATABASE_URL", "GOOGLE_PROJECT_ID", "SECRET_KEY"]
    
    for var in test_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        validator = EnvironmentValidator("development")
        is_valid, report = validator.validate_all()
        validator.print_report(is_valid, report)
        
        if not is_valid:
            print("\n✅ Test passed: Validation correctly detected missing variables")
        else:
            print("\n❌ Test failed: Should have detected missing variables")
            
    finally:
        # Restore original values
        for var, value in original_values.items():
            if value is not None:
                os.environ[var] = value


def test_with_invalid_credentials():
    """Test validation with invalid Google credentials."""
    print("\n🧪 Testing validation with invalid Google credentials...")
    print("=" * 70)
    
    # Set invalid credentials temporarily
    original_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    # Test with invalid JSON
    os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = "invalid-json"
    
    try:
        validator = EnvironmentValidator("development")
        is_valid, report = validator.validate_all()
        validator.print_report(is_valid, report)
        
        if not is_valid:
            print("\n✅ Test passed: Validation correctly detected invalid credentials")
        else:
            print("\n❌ Test failed: Should have detected invalid credentials")
            
    finally:
        # Restore original value
        if original_creds:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = original_creds
        elif "GOOGLE_APPLICATION_CREDENTIALS_JSON" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]


def test_production_mode():
    """Test validation in production mode."""
    print("\n🧪 Testing validation in production mode...")
    print("=" * 70)
    
    # Set production environment
    original_env = os.environ.get("ENVIRONMENT")
    original_secret = os.environ.get("SECRET_KEY")
    
    os.environ["ENVIRONMENT"] = "production"
    os.environ["SECRET_KEY"] = "dev-secret-key"  # Default value (not allowed in production)
    
    try:
        validator = EnvironmentValidator("production")
        is_valid, report = validator.validate_all()
        validator.print_report(is_valid, report)
        
        if not is_valid:
            print("\n✅ Test passed: Production validation correctly detected default secret key")
        else:
            print("\n❌ Test failed: Should have detected default secret key in production")
            
    finally:
        # Restore original values
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
            
        if original_secret:
            os.environ["SECRET_KEY"] = original_secret
        elif "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]


def test_with_all_valid():
    """Test validation with all variables properly set."""
    print("\n🧪 Testing validation with all required variables...")
    print("=" * 70)
    
    # Set minimal required environment variables
    test_env = {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/test",
        "SECRET_KEY": "a-very-secure-secret-key-that-is-long-enough-for-production-use",
        "GOOGLE_PROJECT_ID": "test-project-id",
        "AUDIO_STORAGE_BUCKET": "test-bucket-name",
        "TRANSCRIPT_STORAGE_BUCKET": "test-transcript-bucket",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": """{
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-key\\n-----END PRIVATE KEY-----\\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }"""
    }
    
    # Store original values
    originals = {}
    for var, value in test_env.items():
        originals[var] = os.environ.get(var)
        os.environ[var] = value
    
    try:
        validator = EnvironmentValidator("development")
        is_valid, report = validator.validate_all()
        validator.print_report(is_valid, report)
        
        if is_valid:
            print("\n✅ Test passed: All required variables validated successfully")
        else:
            print("\n❌ Test failed: Should have passed with valid variables")
            
    finally:
        # Restore original values
        for var, original_value in originals.items():
            if original_value is not None:
                os.environ[var] = original_value
            elif var in os.environ:
                del os.environ[var]


def main():
    """Run all validation tests."""
    print("🎯 Environment Variable Validation Tests")
    print("=" * 70)
    print("This script tests the environment validation functionality")
    print("that runs when the API server starts up.\n")
    
    # Run tests
    test_with_missing_vars()
    test_with_invalid_credentials() 
    test_production_mode()
    test_with_all_valid()
    
    print("\n" + "=" * 70)
    print("🎉 All validation tests completed!")
    print("\nTo test the actual startup validation, try:")
    print("1. Remove some variables from your .env file")
    print("2. Start the API server: python -m coaching_assistant.main")
    print("3. Observe the validation output")


if __name__ == "__main__":
    main()