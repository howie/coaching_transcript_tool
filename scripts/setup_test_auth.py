#!/usr/bin/env python3
"""
Test Authentication Setup Script
Generates valid JWT tokens for testing payment system endpoints.

Usage:
    python scripts/setup_test_auth.py --create-test-user
    python scripts/setup_test_auth.py --generate-token --user-id=<uuid>
    python scripts/setup_test_auth.py --export-env --user-id=<uuid>
"""

import os
import sys
import uuid
import argparse
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Clear test environment variables before importing settings to avoid validation errors
test_env_vars = ['TEST_JWT_TOKEN', 'TEST_REFRESH_TOKEN', 'TEST_USER_ID', 'TEST_AUTH_HEADER']
saved_env_vars = {}
for var in test_env_vars:
    if var in os.environ:
        saved_env_vars[var] = os.environ[var]
        del os.environ[var]

try:
    from jose import jwt
    from coaching_assistant.core.config import settings
    from coaching_assistant.core.database import get_db
    from coaching_assistant.models.user import User, UserPlan
    from coaching_assistant.api.auth import create_access_token, create_refresh_token
    from sqlalchemy.orm import Session
    from sqlalchemy import select
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from project root and dependencies are installed")
    sys.exit(1)

# Restore saved environment variables after imports
for var, value in saved_env_vars.items():
    os.environ[var] = value


def create_test_user(db: Session, email: str = "test@example.com", name: str = "Test User") -> User:
    """Create a test user in the database."""
    
    # Check if test user already exists
    stmt = select(User).where(User.email == email)
    existing_user = db.execute(stmt).scalar_one_or_none()
    
    if existing_user:
        print(f"✅ Test user already exists: {existing_user.email} (ID: {existing_user.id})")
        return existing_user
    
    # Create new test user
    test_user = User(
        email=email,
        name=name,
        plan=UserPlan.PRO,  # Use PRO plan for testing payment features
        hashed_password=None,  # No password needed for testing
        google_id="test_google_id_123"
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
    return test_user


def generate_test_tokens(user_id: str) -> dict:
    """Generate access and refresh tokens for a test user."""
    
    try:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "token_type": "bearer"
        }
    except Exception as e:
        print(f"❌ Error generating tokens: {e}")
        return None


def export_environment_variables(tokens: dict):
    """Generate export commands for setting environment variables."""
    
    env_commands = [
        f"export TEST_JWT_TOKEN='{tokens['access_token']}'",
        f"export TEST_REFRESH_TOKEN='{tokens['refresh_token']}'",
        f"export TEST_USER_ID='{tokens['user_id']}'",
        f"export TEST_AUTH_HEADER='Bearer {tokens['access_token']}'",
    ]
    
    return env_commands


def validate_token(token: str) -> bool:
    """Validate that a JWT token can be decoded successfully."""
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        print(f"✅ Token valid - User ID: {payload.get('sub')}, Type: {payload.get('type')}")
        return True
        
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup test authentication for payment system tests")
    parser.add_argument("--create-test-user", action="store_true", help="Create a test user in database")
    parser.add_argument("--generate-token", action="store_true", help="Generate JWT tokens")
    parser.add_argument("--user-id", help="User ID to generate tokens for")
    parser.add_argument("--export-env", action="store_true", help="Output environment variable exports")
    parser.add_argument("--email", default="test@example.com", help="Test user email")
    parser.add_argument("--name", default="Test User", help="Test user name")
    parser.add_argument("--validate", help="Validate an existing JWT token")
    
    args = parser.parse_args()
    
    print("🔑 Payment System Test Authentication Setup")
    print("=" * 60)
    
    # Validate configuration
    if not settings.SECRET_KEY:
        print("❌ SECRET_KEY not configured in environment")
        sys.exit(1)
    
    print(f"✅ JWT Algorithm: {settings.JWT_ALGORITHM}")
    print(f"✅ Secret Key: {'*' * 20}...{settings.SECRET_KEY[-4:]}")
    
    # Handle token validation
    if args.validate:
        validate_token(args.validate)
        return
    
    # Create test user if requested
    user_id = args.user_id
    if args.create_test_user:
        try:
            db = next(get_db())
            test_user = create_test_user(db, args.email, args.name)
            user_id = str(test_user.id)
            db.close()
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            sys.exit(1)
    
    # Generate tokens if requested or if we just created a user
    if args.generate_token or args.create_test_user:
        if not user_id:
            print("❌ User ID required. Use --user-id or --create-test-user")
            sys.exit(1)
        
        print(f"\n🎫 Generating tokens for user: {user_id}")
        tokens = generate_test_tokens(user_id)
        
        if not tokens:
            sys.exit(1)
        
        print("✅ Tokens generated successfully!")
        
        # Validate the generated token
        if validate_token(tokens["access_token"]):
            print("✅ Token validation passed")
        
        # Export environment variables if requested
        if args.export_env or not args.generate_token:
            print(f"\n📋 Environment Variables:")
            print("-" * 40)
            env_commands = export_environment_variables(tokens)
            for cmd in env_commands:
                print(cmd)
            
            print(f"\n💡 Run these commands in your terminal:")
            print(f"{''.join(f'{cmd}; ' for cmd in env_commands)}")
            
            print(f"\n🧪 Test the authentication:")
            print(f"curl -H \"Authorization: Bearer {tokens['access_token'][:50]}...\" \\")
            print(f"     http://localhost:8000/api/v1/auth/me")
    
    print(f"\n✅ Authentication setup complete!")
    print(f"🔥 You can now run authenticated payment tests:")
    print(f"   python tests/run_payment_qa_tests.py --suite e2e")


if __name__ == "__main__":
    main()