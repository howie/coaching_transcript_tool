"""
Integration tests for session persistence and immediate retrieval.

These tests verify that sessions are properly committed to the database
and immediately available for retrieval, preventing "Session not found" errors.
"""

from datetime import datetime

import pytest

from coaching_assistant.models.user import User, UserPlan


# Helper for testing with overridden database
def override_get_db():
    """Override database dependency for testing."""
    from sqlalchemy.orm import sessionmaker

    from tests.conftest import engine

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
            current_month_start=datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=datetime.now(),
        )
        db.add(user)
        db.commit()
        return user

    def override_auth_dependency(self, app, user):
        """Override authentication dependency with test user."""
        from coaching_assistant.api.auth import get_current_user_dependency

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user_dependency] = (
            override_get_current_user
        )


def test_session_creation_and_immediate_retrieval(
    authenticated_client, db_session, test_user
):
    """Test that created session is immediately retrievable (no 404 errors)."""
    # Set user to have available session quota
    test_user.plan = UserPlan.PRO
    test_user.session_count = 0  # Allow session creation
    test_user.current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_session.commit()

    # Create a session
    create_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session for Persistence",
            "language": "en-US",
            "stt_provider": "google",
        },
    )

    # Should succeed
    assert create_response.status_code == 200
    session_data = create_response.json()
    session_id = session_data["id"]
    assert session_id is not None

    # Immediately try to retrieve the session (should not be 404)
    get_response = authenticated_client.get(f"/api/v1/sessions/{session_id}")

    # Should succeed immediately without 404
    assert get_response.status_code == 200
    retrieved_session = get_response.json()
    assert retrieved_session["id"] == session_id
    assert retrieved_session["title"] == "Test Session for Persistence"


def test_upload_url_generation_after_session_creation(
    authenticated_client, db_session, test_user
):
    """Test that upload URL can be generated immediately after session creation."""
    # Set user to have available quota
    test_user.plan = UserPlan.PRO
    test_user.session_count = 0
    test_user.current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_session.commit()

    # Create a session
    create_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session for Upload",
            "language": "en-US",
            "stt_provider": "google",
        },
    )

    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    # Immediately try to get upload URL (should not be 500 error)
    upload_url_response = authenticated_client.post(
        f"/api/v1/sessions/{session_id}/upload-url",
        params={
            "filename": "test.mp3",
            "file_size_mb": 10,  # Within PRO limits
        },
    )

    # Should succeed without "'PlanLimits' object has no attribute 'get'" error
    assert upload_url_response.status_code == 200
    upload_data = upload_url_response.json()
    assert "upload_url" in upload_data
    assert "expires_at" in upload_data


def test_session_status_check_after_creation(
    authenticated_client, db_session, test_user
):
    """Test that session status can be checked immediately after creation."""
    # Set user to have available quota
    test_user.plan = UserPlan.PRO
    test_user.session_count = 0
    test_user.current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_session.commit()

    # Create a session
    create_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Test Session for Status",
            "language": "en-US",
            "stt_provider": "google",
        },
    )

    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    # Immediately check session status (should not be 404)
    status_response = authenticated_client.get(f"/api/v1/sessions/{session_id}/status")

    # Should succeed
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "uploading"  # Initial status


def test_complete_session_workflow_without_errors(
    authenticated_client, db_session, test_user
):
    """Test complete workflow: create -> upload URL -> status check."""
    # Set user to have available quota
    test_user.plan = UserPlan.PRO
    test_user.session_count = 0
    test_user.current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_session.commit()

    # Step 1: Create session
    create_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Complete Workflow Test",
            "language": "en-US",
            "stt_provider": "google",
        },
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    # Step 2: Get upload URL
    upload_url_response = authenticated_client.post(
        f"/api/v1/sessions/{session_id}/upload-url",
        params={"filename": "workflow_test.mp3", "file_size_mb": 15},
    )
    assert upload_url_response.status_code == 200

    # Step 3: Check status
    status_response = authenticated_client.get(f"/api/v1/sessions/{session_id}/status")
    assert status_response.status_code == 200

    # Step 4: Retrieve session details
    get_response = authenticated_client.get(f"/api/v1/sessions/{session_id}")
    assert get_response.status_code == 200

    # All steps should succeed without any 404 or 500 errors


def test_session_persistence_across_multiple_requests(
    authenticated_client, db_session, test_user
):
    """Test that session persists across multiple separate requests."""
    # Set user to have available quota
    test_user.plan = UserPlan.PRO
    test_user.session_count = 0
    test_user.current_month_start = datetime.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    db_session.commit()

    # Create session
    create_response = authenticated_client.post(
        "/api/v1/sessions",
        json={
            "title": "Persistence Test Session",
            "language": "en-US",
            "stt_provider": "google",
        },
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    # Make multiple requests to verify persistence
    for i in range(5):
        get_response = authenticated_client.get(f"/api/v1/sessions/{session_id}")
        assert get_response.status_code == 200
        session_data = get_response.json()
        assert session_data["id"] == session_id
        assert session_data["title"] == "Persistence Test Session"


if __name__ == "__main__":
    pytest.main([__file__])
