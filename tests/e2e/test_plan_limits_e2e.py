"""
Simplified E2E tests for plan limits and validation.
Tests only the endpoints that actually exist in the implementation.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.models.session import Session as CoachingSession
from coaching_assistant.main import app

from tests.e2e.auth_utils import auth_helper


class TestPlanLimitsE2E:
    """End-to-end tests for plan limits and validation."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient):
        """Set up test environment."""
        self.db = db_session
        self.client = client
        self.auth = auth_helper
        
        # Clear any existing auth overrides
        app.dependency_overrides.clear()
        
        yield
        
        # Cleanup after tests
        app.dependency_overrides.clear()

    def test_plan_comparison_endpoint(self):
        """Test that users can view and compare available plans."""
        user = self.auth.create_test_user(self.db, "compare_test@test.com", UserPlan.FREE)
        
        # Setup authentication for this user
        self.auth.override_auth_dependency(app, user)
        
        # Get available plans (no auth required for public endpoint)
        response = self.client.get("/api/plans/")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) >= 3  # Free, Pro, Business
        
        # Get plan comparison (auth required)
        response = self.client.get("/api/plans/compare")
        assert response.status_code == 200
        data = response.json()
        assert "currentPlan" in data
        assert data["currentPlan"] == "free"
        assert "plans" in data

    def test_current_plan_status(self):
        """Test viewing current plan status and usage."""
        # Test Free user
        free_user = self.auth.create_test_user(
            self.db, 
            "free_status@test.com", 
            UserPlan.FREE,
            session_count=5,
            usage_minutes=60
        )
        
        self.auth.override_auth_dependency(app, free_user)
        
        response = self.client.get("/api/plans/current")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "currentPlan" in data
        assert "usageStatus" in data
        assert data["usageStatus"]["currentUsage"]["sessions"] == 5
        assert data["usageStatus"]["currentUsage"]["minutes"] == 60
        
        # Test Pro user
        pro_user = self.auth.create_test_user(self.db, "pro_status@test.com", UserPlan.PRO)
        self.auth.override_auth_dependency(app, pro_user)
        
        response = self.client.get("/api/plans/current")
        assert response.status_code == 200
        data = response.json()
        assert data["currentPlan"]["planName"] == "pro"

    def test_plan_validation_endpoint(self):
        """Test action validation based on plan limits."""
        user = self.auth.create_test_user(self.db, "validation_test@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, user)
        
        # Test session creation validation - should be allowed
        response = self.client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        
        # Set user at session limit
        user.session_count = 10  # Free plan limit
        self.db.commit()
        
        # Test session creation validation - should be blocked
        response = self.client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "upgradeSuggestion" in data

    def test_v1_plan_validation_endpoint(self):
        """Test the v1 plan validation endpoint."""
        user = self.auth.create_test_user(self.db, "v1_validation@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, user)
        
        # Test the /api/v1/plan/validate-action endpoint
        response = self.client.post(
            "/api/v1/plan/validate-action",
            json={
                "action": "create_session",
                "params": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
        assert "limit_info" in data
        
        # Test file upload validation
        response = self.client.post(
            "/api/v1/plan/validate-action",
            json={
                "action": "upload_file",
                "params": {"file_size_mb": 30}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True  # 30MB is under Free limit of 50MB
        
        # Test file too large
        response = self.client.post(
            "/api/v1/plan/validate-action",
            json={
                "action": "upload_file",
                "params": {"file_size_mb": 60}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "upgrade_suggestion" in data

    def test_v1_current_usage_endpoint(self):
        """Test the v1 current usage endpoint."""
        user = self.auth.create_test_user(
            self.db,
            "v1_usage@test.com",
            UserPlan.PRO,
            session_count=25,
            usage_minutes=300,
            transcription_count=50
        )
        
        self.auth.override_auth_dependency(app, user)
        
        response = self.client.get("/api/v1/plan/current-usage")
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan"] == "PRO"
        assert data["usage"]["sessions"]["current"] == 25
        assert data["usage"]["minutes"]["current"] == 300
        assert data["usage"]["transcriptions"]["current"] == 50
        assert "reset_date" in data

    def test_session_creation_with_limits(self):
        """Test creating sessions respects plan limits."""
        user = self.auth.create_test_user(
            self.db,
            "session_limit@test.com",
            UserPlan.FREE,
            session_count=9  # Near the limit
        )
        
        self.auth.override_auth_dependency(app, user)
        
        # Create sessions in database to match count
        for i in range(9):
            session = CoachingSession(
                user_id=user.id,
                title=f"Session {i+1}",
                status="completed"
            )
            self.db.add(session)
        self.db.commit()
        
        # Validate before creating 10th session
        response = self.client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        assert response.json()["allowed"] is True
        
        # Simulate creating 10th session (at limit)
        user.session_count = 10
        self.db.commit()
        
        # Validate creating 11th session - should fail
        response = self.client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "limit" in data.get("message", "").lower()

    def test_export_format_validation(self):
        """Test export format restrictions by plan."""
        # Free user
        free_user = self.auth.create_test_user(self.db, "free_export@test.com", UserPlan.FREE)
        self.auth.override_auth_dependency(app, free_user)
        
        # Test allowed format for free user
        response = self.client.post(
            "/api/plans/validate",
            json={
                "action": "export_transcript",
                "format": "txt"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        
        # Test restricted format for free user
        response = self.client.post(
            "/api/plans/validate",
            json={
                "action": "export_transcript",
                "format": "xlsx"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        
        # Pro user should have access to more formats
        pro_user = self.auth.create_test_user(self.db, "pro_export@test.com", UserPlan.PRO)
        self.auth.override_auth_dependency(app, pro_user)
        
        response = self.client.post(
            "/api/plans/validate",
            json={
                "action": "export_transcript",
                "format": "vtt"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True

    def test_usage_approaching_limits(self):
        """Test warning when approaching plan limits."""
        user = self.auth.create_test_user(
            self.db,
            "approaching@test.com",
            UserPlan.FREE,
            session_count=8,  # 80% of 10
            usage_minutes=96  # 80% of 120
        )
        
        self.auth.override_auth_dependency(app, user)
        
        response = self.client.get("/api/plans/current")
        assert response.status_code == 200
        data = response.json()
        
        # Check for approaching limits warnings
        assert data["usageStatus"]["approachingLimits"]["sessions"] is True
        assert data["usageStatus"]["approachingLimits"]["minutes"] is True
        
        # Should have upgrade suggestion
        if "upgradeSuggestion" in data["usageStatus"]:
            assert data["usageStatus"]["upgradeSuggestion"]["suggestedPlan"] == "pro"

    def test_enterprise_unlimited_features(self):
        """Test that enterprise users have unlimited features."""
        user = self.auth.create_test_user(
            self.db,
            "enterprise@test.com",
            UserPlan.ENTERPRISE,
            session_count=1000,  # Way over free/pro limits
            usage_minutes=10000
        )
        
        self.auth.override_auth_dependency(app, user)
        
        # Should still be able to create sessions
        response = self.client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        assert response.json()["allowed"] is True
        
        # Should have access to all export formats
        for format in ["txt", "json", "vtt", "srt", "xlsx"]:
            response = self.client.post(
                "/api/plans/validate",
                json={
                    "action": "export_transcript",
                    "format": format
                }
            )
            assert response.status_code == 200
            assert response.json()["allowed"] is True

    def test_multiple_users_with_different_plans(self):
        """Test multiple users with different plans work correctly."""
        # Create users with different plans
        users = self.auth.create_users_with_different_plans(self.db)
        
        # Test each user's plan access
        for plan_name, user in users.items():
            self.auth.override_auth_dependency(app, user)
            
            response = self.client.get("/api/plans/current")
            assert response.status_code == 200
            data = response.json()
            
            if plan_name == "free":
                assert data["currentPlan"]["planName"] == "free"
                assert data["currentPlan"]["limits"]["maxSessions"] == 10
            elif plan_name == "pro":
                assert data["currentPlan"]["planName"] == "pro"
                assert data["currentPlan"]["limits"]["maxSessions"] == 100
            elif plan_name == "enterprise":
                assert data["currentPlan"]["planName"] == "enterprise"
                assert data["currentPlan"]["limits"]["maxSessions"] == -1  # Unlimited

    def test_usage_near_limit_helper(self):
        """Test the usage near limit helper function."""
        user = self.auth.create_test_user(self.db, "helper_test@test.com", UserPlan.FREE)
        
        # Set usage to 90% of limits
        self.auth.simulate_usage_near_limit(self.db, user, 0.9)
        
        assert user.session_count == 9  # 90% of 10
        assert user.usage_minutes == 108  # 90% of 120
        
        self.auth.override_auth_dependency(app, user)
        
        # Verify the API recognizes approaching limits
        response = self.client.get("/api/plans/current")
        assert response.status_code == 200
        data = response.json()
        
        assert data["usageStatus"]["approachingLimits"]["sessions"] is True
        assert data["usageStatus"]["approachingLimits"]["minutes"] is True