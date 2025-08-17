"""
Comprehensive authentication tests for the Coaching Assistant API.

Tests cover:
- Unit tests for password hashing and JWT token functions
- Integration tests for all authentication endpoints
- Mock tests for Google OAuth flow
- Error handling and edge cases
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
import httpx

from coaching_assistant.main import app
from coaching_assistant.core.database import get_db
from coaching_assistant.models import Base
from coaching_assistant.api.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    pwd_context,
)
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.core.config import settings


class TestConfig:
    """Test configuration and fixtures"""

    @pytest.fixture(scope="function")
    def test_db_engine(self):
        """Create a temporary SQLite database for each test"""
        # Create a temporary file for the test database
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)

        try:
            # Create engine with the temporary database
            engine = create_engine(
                f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
            )

            # Create all tables
            Base.metadata.create_all(bind=engine)

            yield engine

        finally:
            # Clean up: remove the temporary database file
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.fixture(scope="function")
    def test_db_session(self, test_db_engine):
        """Create a database session for testing"""
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=test_db_engine
        )

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        # Override the dependency
        app.dependency_overrides[get_db] = override_get_db

        yield TestingSessionLocal()

        # Clean up the override
        app.dependency_overrides.clear()

    @pytest.fixture(scope="function")
    def test_client(self, test_db_session):
        """Create a test client with the test database"""
        # Disable reCAPTCHA for tests
        from coaching_assistant.core.config import settings
        original_recaptcha_enabled = settings.RECAPTCHA_ENABLED
        settings.RECAPTCHA_ENABLED = False
        
        with TestClient(app) as client:
            yield client
            
        # Restore original setting
        settings.RECAPTCHA_ENABLED = original_recaptcha_enabled

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "name": "Test User",
        }

    @pytest.fixture
    def created_user(self, test_client, sample_user_data):
        """Create a user and return the response data"""
        response = test_client.post("/api/v1/auth/signup", json=sample_user_data)
        assert response.status_code == 200
        return response.json()

    @pytest.fixture
    def auth_headers(self, test_client, sample_user_data):
        """Create a user, login, and return auth headers"""
        # Create user
        test_client.post("/api/v1/auth/signup", json=sample_user_data)

        # Login
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


class TestPasswordHashing(TestConfig):
    """Unit tests for password hashing functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        # Check that the hash is different from the original password
        assert hashed != password

        # Check that we can verify the password
        assert verify_password(password, hashed) is True

        # Check that wrong passwords fail
        assert verify_password("WrongPassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "Password1"
        password2 = "Password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that the same password produces different hashes (salt)"""
        password = "SamePassword"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Due to salt, hashes should be different
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens(TestConfig):
    """Unit tests for JWT token functions"""

    def test_create_access_token(self):
        """Test access token creation"""
        user_id = str(uuid4())
        token = create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify the token manually
        from jose import jwt

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_id = str(uuid4())
        token = create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify the token manually
        from jose import jwt

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_token_expiration_times(self):
        """Test that access and refresh tokens have correct expiration times"""
        user_id = str(uuid4())

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        from jose import jwt

        access_payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        refresh_payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]


class TestSignupEndpoint(TestConfig):
    """Integration tests for the signup endpoint"""

    def test_successful_signup(self, test_client, sample_user_data):
        """Test successful user registration"""
        response = test_client.post("/api/v1/auth/signup", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["name"]
        assert data["plan"] == "free"  # Default plan
        assert "id" in data

        # Password should not be in the response
        assert "password" not in data
        assert "hashed_password" not in data

    def test_signup_duplicate_email(self, test_client, sample_user_data):
        """Test signup with duplicate email"""
        # Create first user
        response = test_client.post("/api/v1/auth/signup", json=sample_user_data)
        assert response.status_code == 200

        # Try to create second user with same email
        response = test_client.post("/api/v1/auth/signup", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_signup_invalid_email(self, test_client):
        """Test signup with invalid email"""
        invalid_data = {
            "email": "invalid-email",
            "password": "password",
            "name": "Test User",
        }

        response = test_client.post("/api/v1/auth/signup", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_signup_missing_fields(self, test_client):
        """Test signup with missing required fields"""
        incomplete_data = {
            "email": "test@example.com"
            # Missing password and name
        }

        response = test_client.post("/api/v1/auth/signup", json=incomplete_data)
        assert response.status_code == 422  # Validation error


class TestLoginEndpoint(TestConfig):
    """Integration tests for the login endpoint"""

    def test_successful_login(self, test_client, created_user, sample_user_data):
        """Test successful login"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, test_client, created_user, sample_user_data):
        """Test login with wrong password"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["email"], "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials"""
        response = test_client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422  # Validation error


class TestCurrentUserEndpoint(TestConfig):
    """Integration tests for the current user endpoint"""

    def test_get_current_user_success(
        self, test_client, auth_headers, sample_user_data
    ):
        """Test getting current user with valid token"""
        response = test_client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["name"]
        assert data["plan"] == "free"
        assert "id" in data

    def test_get_current_user_no_token(self, test_client):
        """Test getting current user without token"""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, test_client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, test_client):
        """Test getting current user with malformed authorization header"""
        headers = {"Authorization": "NotBearer token"}
        response = test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestRefreshTokenEndpoint(TestConfig):
    """Integration tests for the refresh token endpoint"""

    def test_refresh_token_success(self, test_client, created_user):
        """Test successful token refresh"""
        user_id = created_user["id"]
        refresh_token = create_refresh_token(user_id)

        response = test_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, test_client):
        """Test refresh with invalid token"""
        response = test_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    def test_refresh_token_wrong_type(self, test_client, created_user):
        """Test refresh with access token instead of refresh token"""
        user_id = created_user["id"]
        access_token = create_access_token(user_id)  # Wrong type of token

        response = test_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": access_token}
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]


class TestGoogleOAuthEndpoints(TestConfig):
    """Integration tests for Google OAuth endpoints with mocking"""

    def test_google_login_redirect(self, test_client):
        """Test Google login redirects to Google OAuth"""
        response = test_client.get("/api/v1/auth/google/login", follow_redirects=False)

        assert response.status_code == 307  # Temporary Redirect

        location = response.headers["location"]
        assert "accounts.google.com" in location
        assert "oauth2" in location
        assert settings.GOOGLE_CLIENT_ID in location

    def test_google_login_no_client_id(self, test_client):
        """Test Google login when client ID is not configured"""
        with patch("coaching_assistant.core.config.settings.GOOGLE_CLIENT_ID", ""):
            response = test_client.get("/api/v1/auth/google/login")
            assert response.status_code == 500
            assert "not configured" in response.json()["detail"]

    @patch("httpx.AsyncClient")
    def test_google_callback_success_new_user(self, mock_client, test_client):
        """Test Google OAuth callback for new user"""
        # Mock Google's responses
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake_access_token"}

        mock_userinfo_response = Mock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "email": "google.user@example.com",
            "name": "Google User",
            "id": "google_user_id",
            "picture": "https://example.com/avatar.jpg",
            "verified_email": True,
        }

        # Configure the mock client
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_userinfo_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test the callback
        response = test_client.get(
            "/api/v1/auth/google/callback?code=fake_auth_code", follow_redirects=False
        )

        assert response.status_code == 307  # Redirect to frontend

        location = response.headers["location"]
        assert "localhost:3000" in location  # Development frontend URL
        assert "access_token=" in location
        assert "refresh_token=" in location

    @patch("httpx.AsyncClient")
    def test_google_callback_success_existing_user(
        self, mock_client, test_client, created_user
    ):
        """Test Google OAuth callback for existing user"""
        # First, create a user manually with the same email that Google will return
        google_email = created_user["email"]  # Use the same email

        # Mock Google's responses
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "fake_access_token"}

        mock_userinfo_response = Mock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = {
            "email": google_email,
            "name": "Updated Google User",
            "id": "google_user_id",
            "picture": "https://example.com/new_avatar.jpg",
            "verified_email": True,
        }

        # Configure the mock client
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client_instance.get = AsyncMock(return_value=mock_userinfo_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        # Test the callback
        response = test_client.get(
            "/api/v1/auth/google/callback?code=fake_auth_code", follow_redirects=False
        )

        assert response.status_code == 307  # Redirect to frontend

    @patch("httpx.AsyncClient")
    def test_google_callback_network_error(self, mock_client, test_client):
        """Test Google OAuth callback with network error"""
        # Configure mock to raise a connection timeout
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.ConnectTimeout("Connection timeout")
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = test_client.get("/api/v1/auth/google/callback?code=fake_auth_code")

        assert response.status_code == 503
        assert "Unable to connect to Google services" in response.json()["detail"]

    @patch("httpx.AsyncClient")
    def test_google_callback_google_error(self, mock_client, test_client):
        """Test Google OAuth callback when Google returns an error"""
        # Mock Google returning an error
        mock_token_response = Mock()
        mock_token_response.status_code = 400
        mock_token_response.text = "Invalid authorization code"

        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_token_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        response = test_client.get("/api/v1/auth/google/callback?code=invalid_code")

        assert response.status_code == 400
        assert "Failed to exchange authorization code" in response.json()["detail"]


class TestErrorHandling(TestConfig):
    """Test error handling and edge cases"""

    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON in requests"""
        response = test_client.post(
            "/api/v1/auth/signup",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_sql_injection_attempt(self, test_client):
        """Test that SQL injection attempts are safely handled"""
        malicious_data = {
            "email": "test@example.com'; DROP TABLE user; --",
            "password": "password",
            "name": "Hacker",
        }

        # This should either fail validation or be safely escaped
        response = test_client.post("/api/v1/auth/signup", json=malicious_data)
        # The response might be 422 (validation error) or 200 (safely handled)
        assert response.status_code in [200, 422]

        # If it's 200, the email should be safely stored
        if response.status_code == 200:
            data = response.json()
            assert data["email"] == malicious_data["email"]  # Should be safely stored

    def test_extremely_long_input(self, test_client):
        """Test handling of extremely long input strings"""
        long_string = "a" * 10000

        malicious_data = {
            "email": f"{long_string}@example.com",
            "password": long_string,
            "name": long_string,
        }

        response = test_client.post("/api/v1/auth/signup", json=malicious_data)
        # Should either be rejected by validation or handled gracefully
        assert response.status_code in [200, 422]


# Utility functions for running tests
def run_unit_tests():
    """Run only unit tests"""
    pytest.main(["-v", "-k", "TestPasswordHashing or TestJWTTokens"])


def run_integration_tests():
    """Run only integration tests"""
    pytest.main(["-v", "-k", "not (TestPasswordHashing or TestJWTTokens)"])


def run_all_tests():
    """Run all tests"""
    pytest.main(["-v"])


if __name__ == "__main__":
    run_all_tests()
