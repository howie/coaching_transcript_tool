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


# Helper for testing with overridden database
def override_get_db():
    """Override database dependency for testing."""
    from tests.conftest import engine
    from sqlalchemy.orm import sessionmaker
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine())
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class AuthTestUtils:
    """Utility class for authentication testing."""
    
    def create_test_user(self, db, email, plan, session_count=0, transcription_count=0):
        """Create a test user with specified plan and usage."""
        import uuid
        from datetime import datetime
        
        user = User(
            id=uuid.uuid4(),
            email=email,
            name="Test User",
            google_id=f"google-{uuid.uuid4()}",
            plan=plan,
            usage_minutes=0,
            session_count=session_count,
            transcription_count=transcription_count,
            current_month_start=datetime.now().replace(day=1),
            created_at=datetime.now()
        )
        db.add(user)
        db.commit()
        return user
    
    def override_auth_dependency(self, app, user):
        """Override authentication dependency with test user."""
        from coaching_assistant.api.auth import get_current_user_dependency
        
        def override_get_current_user():
            return user
        
        app.dependency_overrides[get_current_user_dependency] = override_get_current_user


def test_session_limit_exceeded_json_serialization(authenticated_client, db_session, test_user):
    """Test that session limit exceeded error is properly JSON serialized."""
    # Set user to FREE plan with maximum sessions (3)
    test_user.plan = UserPlan.FREE
    test_user.session_count = 3  # At FREE limit
    db_session.commit()
    
    # Attempt to create a new session (should fail)
    response = authenticated_client.post(
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


def test_file_size_exceeded_json_serialization(authenticated_client, db_session, test_user):
    """Test that file size exceeded error is properly JSON serialized."""
    # Set user to FREE plan
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0  # Allow session creation
    db_session.commit()
    
    # Create a session
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # Attempt to get upload URL with file size exceeding FREE limit (25MB)
    response = authenticated_client.post(
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


def test_transcription_limit_exceeded_json_serialization(authenticated_client, db_session, test_user):
    """Test that transcription limit exceeded error is properly JSON serialized."""
    # Set user to FREE plan with maximum transcriptions (5)
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0  # Allow session creation
    test_user.transcription_count = 5  # At FREE transcription limit
    db_session.commit()
    
    # Create a session first
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US", 
            "stt_provider": "google"
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # Attempt to start transcription (should fail due to limit)
    response = authenticated_client.post(f"/api/v1/sessions/{session_id}/start-transcription")
    
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


def test_upload_url_requires_file_size_mb_parameter(authenticated_client, db_session, test_user):
    """Test that upload URL endpoint requires file_size_mb parameter."""
    # Set user to FREE plan
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0  # Allow session creation
    db_session.commit()
    
    # Create a session
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # Attempt to get upload URL without file_size_mb parameter (should fail)
    response = authenticated_client.post(
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


def test_upload_url_success_with_file_size_mb(authenticated_client, db_session, test_user):
    """Test that upload URL works when file_size_mb is provided."""
    # Set user to FREE plan
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0  # Allow session creation
    db_session.commit()
    
    # Create a session
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # Get upload URL with proper parameters
    response = authenticated_client.post(
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


def test_upload_url_filename_validation(authenticated_client, db_session, test_user):
    """Test that upload URL validates filename extensions."""
    # Set user to FREE plan
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0  # Allow session creation
    db_session.commit()
    
    # Create a session
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]
    
    # Test invalid file extension
    response = authenticated_client.post(
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
        response = authenticated_client.post(
            f"/api/v1/sessions/{session_id}/upload-url",
            params={
                "filename": f"test.{ext}",
                "file_size_mb": 10
            }
        )
        assert response.status_code == 200, f"Failed for extension: {ext}"


def test_free_plan_limits_are_enforced(authenticated_client, db_session, test_user):
    """Test that FREE plan limits are correctly enforced."""
    # Set user to FREE plan just under limit
    test_user.plan = UserPlan.FREE
    test_user.session_count = 2  # Just under limit
    db_session.commit()
    
    # Should be able to create one more session
    response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert response.status_code == 200
    
    # Update user to be at limit
    test_user.session_count = 3
    db_session.commit()
    
    # Should not be able to create another session
    response = authenticated_client.post(
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


def test_pro_plan_higher_limits(authenticated_client, db_session, test_user):
    """Test that PRO plan has higher limits than FREE."""
    # Set user to PRO plan
    test_user.plan = UserPlan.PRO
    test_user.session_count = 10  # Would exceed FREE limit but within PRO
    db_session.commit()
    
    # Should be able to create sessions (PRO limit is 25)
    response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "PRO Session",
            "language": "en-US",
            "stt_provider": "google"
        }
    )
    assert response.status_code == 200


def test_file_size_limits_by_plan(authenticated_client, db_session, test_user):
    """Test file size limits are enforced correctly by plan."""
    # Test FREE plan file size limit (25MB)
    test_user.plan = UserPlan.FREE
    test_user.session_count = 0
    db_session.commit()
    
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={"title": "FREE Session", "language": "en-US", "stt_provider": "google"}
    )
    session_id = session_response.json()["id"]
    
    # File within limit should work
    response = authenticated_client.post(
        f"/api/v1/sessions/{session_id}/upload-url",
        params={"filename": "small.mp3", "file_size_mb": 20}
    )
    assert response.status_code == 200
    
    # File exceeding limit should fail
    response = authenticated_client.post(
        f"/api/v1/sessions/{session_id}/upload-url",
        params={"filename": "large.mp3", "file_size_mb": 30}
    )
    assert response.status_code == 413
    
    # Test PRO plan file size limit (100MB) - update same user
    test_user.plan = UserPlan.PRO
    db_session.commit()
    
    session_response = authenticated_client.post(
        "/api/v1/sessions",
        json={"title": "PRO Session", "language": "en-US", "stt_provider": "google"}
    )
    session_id = session_response.json()["id"]
    
    # Larger file should work for PRO
    response = authenticated_client.post(
        f"/api/v1/sessions/{session_id}/upload-url",
        params={"filename": "medium.mp3", "file_size_mb": 50}
    )
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])