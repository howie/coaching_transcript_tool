"""
Tests for session API JSON serialization and upload URL functionality.

These tests protect against regressions in:
1. HTTPException JSON serialization with UserPlan enums
2. Upload URL endpoint requiring file_size_mb parameter
3. Plan limit enforcement with proper error responses
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from coaching_assistant.main import app
from coaching_assistant.core.database import get_db
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.models.session import Session as SessionModel
from tests.conftest import override_get_db
from tests.fixtures.auth_utils import AuthTestUtils


class TestSessionJSONSerialization:
    """Test that HTTPExceptions with UserPlan enums are properly JSON serialized."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.client = TestClient(app)
        self.auth = AuthTestUtils()
        
        # Override database dependency
        app.dependency_overrides[get_db] = override_get_db
        self.db = next(override_get_db())
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
        self.db.close()

    def test_session_limit_exceeded_json_serialization(self):
        """Test that session limit exceeded error is properly JSON serialized."""
        # Create a FREE user with maximum sessions (3)
        user = self.auth.create_test_user(
            self.db,
            "session_limit@test.com", 
            UserPlan.FREE,
            session_count=3  # At FREE limit
        )
        self.auth.override_auth_dependency(app, user)
        
        # Attempt to create a new session (should fail)
        response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        
        # Should return 403 with properly serialized JSON
        assert response.status_code == 403
        
        # The response should be valid JSON (not throw serialization error)
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "session_limit_exceeded"
        assert detail["current_usage"] == 3
        assert detail["limit"] == 3
        assert detail["plan"] == "free"  # Should be string, not enum object
        assert isinstance(detail["plan"], str)  # Verify it's serialized as string

    def test_transcription_limit_exceeded_json_serialization(self):
        """Test that transcription limit exceeded error is properly JSON serialized."""
        # Create a FREE user with maximum transcriptions (5)
        user = self.auth.create_test_user(
            self.db,
            "transcription_limit@test.com",
            UserPlan.FREE,
            session_count=0,  # Allow session creation
            transcription_count=5  # At FREE transcription limit
        )
        self.auth.override_auth_dependency(app, user)
        
        # Create a session first
        session_response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US", 
                "stt_provider": "google"
            }
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # Attempt to start transcription (should fail due to limit)
        response = self.client.post(f"/api/v1/sessions/{session_id}/start-transcription")
        
        # Should return 403 with properly serialized JSON
        assert response.status_code == 403
        
        # The response should be valid JSON
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "transcription_limit_exceeded"
        assert detail["current_usage"] == 5
        assert detail["limit"] == 5
        assert detail["plan"] == "free"  # Should be string, not enum object
        assert isinstance(detail["plan"], str)

    def test_file_size_exceeded_json_serialization(self):
        """Test that file size exceeded error is properly JSON serialized."""
        # Create a FREE user
        user = self.auth.create_test_user(
            self.db,
            "filesize_limit@test.com",
            UserPlan.FREE
        )
        self.auth.override_auth_dependency(app, user)
        
        # Create a session
        session_response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # Attempt to get upload URL with file size exceeding FREE limit (25MB)
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={
                "filename": "large_file.mp3",
                "file_size_mb": 50  # Exceeds FREE limit of 25MB
            }
        )
        
        # Should return 413 with properly serialized JSON
        assert response.status_code == 413
        
        # The response should be valid JSON
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"] == "file_size_exceeded"
        assert detail["file_size_mb"] == 50
        assert detail["limit_mb"] == 25
        assert detail["plan"] == "free"  # Should be string, not enum object
        assert isinstance(detail["plan"], str)


class TestUploadURLRequirements:
    """Test that upload URL endpoint properly requires file_size_mb parameter."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.client = TestClient(app)
        self.auth = AuthTestUtils()
        
        # Override database dependency
        app.dependency_overrides[get_db] = override_get_db
        self.db = next(override_get_db())
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
        self.db.close()

    def test_upload_url_requires_file_size_mb_parameter(self):
        """Test that upload URL endpoint requires file_size_mb parameter."""
        # Create a user
        user = self.auth.create_test_user(self.db, "upload_test@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, user)
        
        # Create a session
        session_response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # Attempt to get upload URL without file_size_mb parameter (should fail)
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={"filename": "test.mp3"}  # Missing file_size_mb
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
        
        # Verify it's a validation error for missing file_size_mb
        data = response.json()
        assert "detail" in data
        # FastAPI validation errors have specific structure
        validation_errors = data["detail"]
        assert isinstance(validation_errors, list)
        
        # Check that file_size_mb is in the missing fields
        missing_fields = [error["loc"][-1] for error in validation_errors if error["type"] == "missing"]
        assert "file_size_mb" in missing_fields

    def test_upload_url_success_with_file_size_mb(self):
        """Test that upload URL works when file_size_mb is provided."""
        # Create a user  
        user = self.auth.create_test_user(self.db, "upload_success@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, user)
        
        # Create a session
        session_response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # Get upload URL with proper parameters
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={
                "filename": "test.mp3",
                "file_size_mb": 10  # Within FREE limit
            }
        )
        
        # Should succeed
        assert response.status_code == 200
        
        # Verify response structure
        data = response.json()
        assert "upload_url" in data
        assert "expires_at" in data

    def test_upload_url_filename_validation(self):
        """Test that upload URL validates filename extensions."""
        # Create a user
        user = self.auth.create_test_user(self.db, "filename_test@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, user)
        
        # Create a session
        session_response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]
        
        # Test invalid file extension
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={
                "filename": "test.txt",  # Invalid extension
                "file_size_mb": 10
            }
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
        
        # Test valid file extensions
        valid_extensions = ["mp3", "wav", "flac", "ogg", "mp4", "m4a"]
        for ext in valid_extensions:
            response = self.client.post(
                f"/api/v1/sessions/{session_id}/upload-url",
                params={
                    "filename": f"test.{ext}",
                    "file_size_mb": 10
                }
            )
            assert response.status_code == 200, f"Failed for extension: {ext}"


class TestPlanLimitEnforcement:
    """Test that plan limits are properly enforced with correct error responses."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.client = TestClient(app)
        self.auth = AuthTestUtils()
        
        # Override database dependency
        app.dependency_overrides[get_db] = override_get_db
        self.db = next(override_get_db())
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
        self.db.close()

    def test_free_plan_limits_are_enforced(self):
        """Test that FREE plan limits are correctly enforced."""
        # Create FREE user at various limit stages
        user = self.auth.create_test_user(
            self.db,
            "free_limits@test.com",
            UserPlan.FREE,
            session_count=2  # Just under limit
        )
        self.auth.override_auth_dependency(app, user)
        
        # Should be able to create one more session
        response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert response.status_code == 201
        
        # Update user to be at limit
        user.session_count = 3
        self.db.commit()
        
        # Should not be able to create another session
        response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "Another Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "session_limit_exceeded"

    def test_pro_plan_higher_limits(self):
        """Test that PRO plan has higher limits than FREE."""
        # Create PRO user 
        user = self.auth.create_test_user(
            self.db,
            "pro_limits@test.com",
            UserPlan.PRO,
            session_count=10  # Would exceed FREE limit but within PRO
        )
        self.auth.override_auth_dependency(app, user)
        
        # Should be able to create sessions (PRO limit is 25)
        response = self.client.post(
            "/api/v1/sessions",
            json={
                "title": "PRO Session",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert response.status_code == 201

    def test_file_size_limits_by_plan(self):
        """Test file size limits are enforced correctly by plan."""
        # Test FREE plan file size limit (25MB)
        free_user = self.auth.create_test_user(self.db, "free_file@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, free_user)
        
        session_response = self.client.post(
            "/api/v1/sessions",
            json={"title": "FREE Session", "language": "en-US", "stt_provider": "google"}
        )
        session_id = session_response.json()["id"]
        
        # File within limit should work
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={"filename": "small.mp3", "file_size_mb": 20}
        )
        assert response.status_code == 200
        
        # File exceeding limit should fail
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={"filename": "large.mp3", "file_size_mb": 30}
        )
        assert response.status_code == 413
        
        # Test PRO plan file size limit (100MB)
        pro_user = self.auth.create_test_user(self.db, "pro_file@test.com", UserPlan.PRO)
        self.auth.override_auth_dependency(app, pro_user)
        
        session_response = self.client.post(
            "/api/v1/sessions",
            json={"title": "PRO Session", "language": "en-US", "stt_provider": "google"}
        )
        session_id = session_response.json()["id"]
        
        # Larger file should work for PRO
        response = self.client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={"filename": "medium.mp3", "file_size_mb": 50}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])