"""
Authentication utilities for E2E tests.
Handles token generation and authentication setup for test scenarios.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from coaching_assistant.models.user import User, UserPlan


class E2EAuthHelper:
    """Helper class for E2E test authentication."""
    
    def __init__(self):
        """Initialize auth helper and load environment variables."""
        # Load .env file from project root if dotenv is available
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                '.env'
            )
            load_dotenv(env_path)
        except ImportError:
            pass  # dotenv not required for tests
        
        # Get secret key from environment
        self.secret_key = os.getenv('SECRET_KEY', 'test-secret-key-for-e2e-tests')
        self.algorithm = "HS256"
        
    def create_test_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Create a test token for testing.
        For E2E tests, we don't need real JWT, just override the dependency.
        
        Args:
            user_id: The user ID to include in the token
            expires_in: Token expiration time in seconds (default: 1 hour)
            
        Returns:
            Test token string
        """
        # For E2E tests, we just return a simple test token
        # The actual authentication is handled by dependency override
        return f"test-token-{user_id}"
    
    def create_test_user(
        self,
        db: Session,
        email: str,
        plan: UserPlan = UserPlan.FREE,
        **kwargs
    ) -> User:
        """
        Create a test user with default values.
        
        Args:
            db: Database session
            email: User email
            plan: User plan (default: FREE)
            **kwargs: Additional user attributes
            
        Returns:
            Created user object
        """
        user_data = {
            "email": email,
            "name": kwargs.get("name", "Test User"),
            "google_id": kwargs.get("google_id", f"google_{email}"),
            "plan": plan,
            "usage_minutes": kwargs.get("usage_minutes", 0),
            "session_count": kwargs.get("session_count", 0),
            "transcription_count": kwargs.get("transcription_count", 0),
            "current_month_start": kwargs.get(
                "current_month_start",
                datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            )
        }
        
        # Add any additional kwargs not in the defaults
        for key, value in kwargs.items():
            if key not in user_data:
                user_data[key] = value
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_auth_headers(self, user: User) -> Dict[str, str]:
        """
        Get authorization headers for a user.
        Note: For E2E tests, we override the auth dependency instead of using real tokens.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with Authorization header
        """
        token = self.create_test_token(str(user.id))
        return {"Authorization": f"Bearer {token}"}
    
    def override_auth_dependency(self, app, user: User):
        """
        Override FastAPI authentication dependency for testing.
        
        Args:
            app: FastAPI application instance
            user: User to authenticate as
        """
        from coaching_assistant.api.auth import get_current_user_dependency
        
        def override_get_current_user():
            return user
        
        app.dependency_overrides[get_current_user_dependency] = override_get_current_user
    
    def clear_auth_override(self, app):
        """
        Clear authentication override.
        
        Args:
            app: FastAPI application instance
        """
        from coaching_assistant.api.auth import get_current_user_dependency
        
        if get_current_user_dependency in app.dependency_overrides:
            del app.dependency_overrides[get_current_user_dependency]
    
    def setup_authenticated_client(self, client, user: User):
        """
        Setup client with authentication for a specific user.
        
        Args:
            client: TestClient instance
            user: User to authenticate as
            
        Returns:
            The client with authentication setup
        """
        from coaching_assistant.main import app
        self.override_auth_dependency(app, user)
        return client
    
    def create_users_with_different_plans(self, db: Session) -> Dict[str, User]:
        """
        Create test users with different plan types.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with users for each plan type
        """
        users = {
            "free": self.create_test_user(
                db,
                "free_user@test.com",
                UserPlan.FREE,
                name="Free User"
            ),
            "pro": self.create_test_user(
                db,
                "pro_user@test.com",
                UserPlan.PRO,
                name="Pro User"
            ),
            "enterprise": self.create_test_user(
                db,
                "enterprise_user@test.com",
                UserPlan.ENTERPRISE,
                name="Enterprise User"
            )
        }
        return users
    
    def simulate_usage_near_limit(self, db: Session, user: User, percentage: float = 0.8):
        """
        Set user usage to a percentage of their plan limits.
        
        Args:
            db: Database session
            user: User to update
            percentage: Percentage of limit to set (0.8 = 80%)
        """
        from coaching_assistant.services.plan_limits import PlanLimits
        
        limits = PlanLimits.get_limits(user.plan)
        
        if limits["max_sessions"] != -1:  # Not unlimited
            user.session_count = int(limits["max_sessions"] * percentage)
        
        if limits["max_total_minutes"] != -1:  # Not unlimited
            user.usage_minutes = int(limits["max_total_minutes"] * percentage)
        
        if limits["max_transcription_count"] != -1:  # Not unlimited
            user.transcription_count = int(limits["max_transcription_count"] * percentage)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_test_environment_config(self) -> Dict[str, Any]:
        """
        Get test environment configuration from .env file.
        
        Returns:
            Dictionary with environment configuration
        """
        return {
            "database_url": os.getenv("DATABASE_URL", "sqlite:///:memory:"),
            "redis_url": os.getenv("REDIS_URL"),
            "secret_key": self.secret_key,
            "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "stt_provider": os.getenv("STT_PROVIDER", "google"),
            "environment": os.getenv("ENVIRONMENT", "test"),
            "debug": os.getenv("DEBUG", "true").lower() == "true"
        }


# Create a singleton instance for easy import
auth_helper = E2EAuthHelper()