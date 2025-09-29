#!/usr/bin/env python3
"""
Simplified Test JWT Token Generator
Generates valid JWT tokens for testing without importing full settings.

Usage:
    python scripts/generate_test_token.py
    python scripts/generate_test_token.py --user-id <uuid>
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from jose import jwt
except ImportError:
    print(
        "❌ jose library not found. Install with: pip install python-jose[cryptography]"
    )
    sys.exit(1)


def get_settings():
    """Get settings directly from environment without pydantic validation."""
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        print("⚠️  SECRET_KEY not found in environment, using default for testing")
        secret_key = "test_secret_key_for_jwt_testing_only_not_for_production"

    return {
        "SECRET_KEY": secret_key,
        "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
        "REFRESH_TOKEN_EXPIRE_DAYS": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")),
    }


def create_test_access_token(user_id: str, settings: dict) -> str:
    """Create access token for testing."""
    expire = datetime.utcnow() + timedelta(
        minutes=settings["ACCESS_TOKEN_EXPIRE_MINUTES"]
    )
    to_encode = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(
        to_encode, settings["SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"]
    )


def create_test_refresh_token(user_id: str, settings: dict) -> str:
    """Create refresh token for testing."""
    expire = datetime.utcnow() + timedelta(days=settings["REFRESH_TOKEN_EXPIRE_DAYS"])
    to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(
        to_encode, settings["SECRET_KEY"], algorithm=settings["JWT_ALGORITHM"]
    )


def validate_test_token(token: str, settings: dict) -> bool:
    """Validate a JWT token."""
    try:
        payload = jwt.decode(
            token, settings["SECRET_KEY"], algorithms=[settings["JWT_ALGORITHM"]]
        )
        print(
            f"✅ Token valid - User ID: {payload.get('sub')}, Type: {payload.get('type')}"
        )
        exp = payload.get("exp")
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            print(f"✅ Expires: {exp_date}")
        return True
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate JWT tokens for testing")
    parser.add_argument(
        "--user-id", help="User ID for token (generates random UUID if not provided)"
    )
    parser.add_argument("--validate", help="Validate an existing token")

    args = parser.parse_args()

    print("🔑 Test JWT Token Generator")
    print("=" * 50)

    settings = get_settings()
    print(f"✅ Algorithm: {settings['JWT_ALGORITHM']}")
    print(f"✅ Secret Key: {'*' * 20}...{settings['SECRET_KEY'][-4:]}")

    if args.validate:
        print("\n🔍 Validating token...")
        validate_test_token(args.validate, settings)
        return

    # Generate user ID if not provided
    user_id = args.user_id or str(uuid4())
    print(f"\n👤 User ID: {user_id}")

    # Generate tokens
    access_token = create_test_access_token(user_id, settings)
    refresh_token = create_test_refresh_token(user_id, settings)

    print("\n🎫 Tokens generated:")
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")

    # Validate the generated token
    print("\n🔍 Validating access token...")
    if validate_test_token(access_token, settings):
        print("✅ Token validation successful!")

    # Export commands
    print("\n📋 Environment Variables:")
    print("-" * 40)
    print(f"export TEST_JWT_TOKEN='{access_token}'")
    print(f"export TEST_REFRESH_TOKEN='{refresh_token}'")
    print(f"export TEST_USER_ID='{user_id}'")
    print(f"export TEST_AUTH_HEADER='Bearer {access_token}'")

    print("\n💡 Run these commands to set up authentication:")
    print(f"export TEST_JWT_TOKEN='{access_token}' && \\")
    print(f"export TEST_REFRESH_TOKEN='{refresh_token}' && \\")
    print(f"export TEST_USER_ID='{user_id}' && \\")
    print(f"export TEST_AUTH_HEADER='Bearer {access_token}'")

    print("\n🧪 Test the token:")
    print(f'curl -H "Authorization: Bearer {access_token[:50]}..." \\')
    print("     http://localhost:8000/api/v1/auth/me")

    print("\n✅ JWT tokens ready for testing!")


if __name__ == "__main__":
    main()
