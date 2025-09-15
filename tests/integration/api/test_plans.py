"""Tests for plan management API endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.api.v1.plans import PLAN_CONFIGS


class TestPlansAPI:
    """Test suite for plan management endpoints."""
    
    def test_get_available_plans(self, client: TestClient, db_session: Session):
        """Test GET /api/plans/ returns all available plans."""
        response = client.get("/api/plans/")
        assert response.status_code == 200
        
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 3  # Free, Pro, Business
        
        # Verify plan structure
        for plan in data["plans"]:
            assert "planName" in plan
            assert "displayName" in plan
            assert "limits" in plan
            assert "pricing" in plan
            assert "features" in plan
            
        # Verify plan order
        plan_names = [p["planName"] for p in data["plans"]]
        assert plan_names == ["free", "pro", "business"]
        
        # Verify unlimited values are converted to -1
        business_plan = next(p for p in data["plans"] if p["planName"] == "business")
        assert business_plan["limits"]["maxSessions"] == -1
        assert business_plan["limits"]["maxTotalMinutes"] == -1
    
    def test_get_current_plan_status_free_user(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test GET /api/plans/current for free tier user."""
        # Set user to free plan with some usage
        test_user.plan = UserPlan.FREE
        test_user.session_count = 5
        test_user.usage_minutes = 60
        test_user.transcription_count = 10
        test_user.current_month_start = datetime.now().replace(day=1)
        db_session.commit()

        response = authenticated_client.get("/api/plans/current")
        assert response.status_code == 200

        data = response.json()

        # DEBUG: Print the actual response structure to understand what we get
        import json
        print(f"\n📊 DEBUG: Full Response Structure:")
        print(json.dumps(data, indent=2, default=str))

        # Check for enum.value errors
        response_str = json.dumps(data)
        if ".value" in response_str:
            print(f"\n❌ ENUM ERROR: Response contains '.value' strings")
        else:
            print(f"\n✅ ENUM CHECK: No '.value' strings found")

        # Show current plan structure specifically
        current_plan = data.get("currentPlan", {})
        print(f"\n📊 Current Plan Structure:")
        print(json.dumps(current_plan, indent=2, default=str))

        # Show usage status structure
        usage_status = data.get("usageStatus", {})
        print(f"\n📈 Usage Status Structure:")
        print(json.dumps(usage_status, indent=2, default=str))

        # Updated assertion based on actual response structure
        # The response structure has changed - let's check what we actually get
        assert "currentPlan" in data
        assert "usageStatus" in data
        assert "subscriptionInfo" in data
        assert data["usageStatus"]["currentUsage"]["sessions"] == 5
        assert data["usageStatus"]["currentUsage"]["minutes"] == 60
        assert data["usageStatus"]["currentUsage"]["transcriptions"] == 10
        
        # Check usage percentages
        assert data["usageStatus"]["usagePercentages"]["sessions"] == 50.0  # 5/10
        assert data["usageStatus"]["usagePercentages"]["minutes"] == 50.0  # 60/120
        
        # Check approaching limits (80% threshold)
        assert data["usageStatus"]["approachingLimits"]["sessions"] is False
        assert data["usageStatus"]["approachingLimits"]["minutes"] is False
    
    def test_get_current_plan_status_approaching_limits(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test upgrade suggestion when approaching limits."""
        # Set user close to limits
        test_user.plan = UserPlan.FREE
        test_user.session_count = 9  # 90% of limit
        test_user.usage_minutes = 100  # 83% of limit
        test_user.transcription_count = 18  # 90% of limit
        db_session.commit()
        
        response = authenticated_client.get("/api/plans/current")
        assert response.status_code == 200
        
        data = response.json()
        assert data["usageStatus"]["approachingLimits"]["sessions"] is True
        assert data["usageStatus"]["approachingLimits"]["minutes"] is True
        assert "upgradeSuggestion" in data["usageStatus"]
        assert data["usageStatus"]["upgradeSuggestion"]["suggestedPlan"] == "pro"
    
    def test_get_current_plan_status_pro_user(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test GET /api/plans/current for pro tier user."""
        test_user.plan = UserPlan.PRO
        test_user.session_count = 50
        test_user.usage_minutes = 600
        test_user.transcription_count = 100
        db_session.commit()
        
        response = authenticated_client.get("/api/plans/current")
        assert response.status_code == 200
        
        data = response.json()
        assert data["currentPlan"]["planName"] == "pro"
        assert data["usageStatus"]["currentUsage"]["sessions"] == 50
        assert data["usageStatus"]["usagePercentages"]["sessions"] == 50.0  # 50/100
    
    def test_get_current_plan_status_enterprise_user(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test GET /api/plans/current for enterprise user with unlimited limits."""
        test_user.plan = UserPlan.ENTERPRISE
        test_user.session_count = 1000
        test_user.usage_minutes = 10000
        test_user.transcription_count = 5000
        db_session.commit()
        
        response = authenticated_client.get("/api/plans/current")
        assert response.status_code == 200
        
        data = response.json()
        assert data["currentPlan"]["planName"] == "business"
        assert data["currentPlan"]["limits"]["maxSessions"] == -1  # Unlimited
        assert data["usageStatus"]["usagePercentages"]["sessions"] is None  # No percentage for unlimited
        assert "upgradeSuggestion" not in data["usageStatus"]  # No upgrade from enterprise
    
    def test_compare_plans(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test GET /api/plans/compare endpoint."""
        test_user.plan = UserPlan.FREE
        db_session.commit()
        
        response = authenticated_client.get("/api/plans/compare")
        assert response.status_code == 200
        
        data = response.json()
        assert data["currentPlan"] == "free"
        assert len(data["plans"]) == 3
        
        # Check current plan is marked
        free_plan = next(p for p in data["plans"] if p["planName"] == "free")
        assert free_plan["isCurrent"] is True
        
        pro_plan = next(p for p in data["plans"] if p["planName"] == "pro")
        assert pro_plan["isCurrent"] is False
        
        # Check recommended upgrade
        assert data["recommendedUpgrade"] is not None
        assert data["recommendedUpgrade"]["suggestedPlan"] == "pro"
    
    def test_validate_action_create_session_allowed(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for allowed session creation."""
        test_user.plan = UserPlan.FREE
        test_user.session_count = 5  # Under limit of 10
        db_session.commit()
        
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is True
        assert data["message"] == "Action permitted"
    
    def test_validate_action_create_session_blocked(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for blocked session creation."""
        test_user.plan = UserPlan.FREE
        test_user.session_count = 10  # At limit
        db_session.commit()
        
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "create_session"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is False
        assert "Session limit exceeded" in data["message"]
        assert data["limitInfo"]["type"] == "maxSessions"
        assert data["limitInfo"]["current"] == 10
        assert data["limitInfo"]["limit"] == 10
        assert "upgradeSuggestion" in data
    
    def test_validate_action_upload_file_size_check(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for file size validation."""
        test_user.plan = UserPlan.FREE
        db_session.commit()
        
        # Test file too large
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "upload_file", "file_size_mb": 100}  # Free limit is 50MB
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is False
        assert "File size exceeds limit" in data["message"]
        assert data["limitInfo"]["limit"] == 50
        
        # Test file within limit
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "upload_file", "file_size_mb": 30}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is True
    
    def test_validate_action_export_format_check(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for export format validation."""
        test_user.plan = UserPlan.FREE
        db_session.commit()
        
        # Test unavailable format
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "export_transcript", "format": "xlsx"}  # Not available in free
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is False
        assert "not available" in data["message"]
        assert "xlsx" in data["limitInfo"]["requested"]
        
        # Test available format
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "export_transcript", "format": "json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is True
    
    def test_validate_action_transcribe_limit(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for transcription limit."""
        test_user.plan = UserPlan.FREE
        test_user.transcription_count = 20  # At limit
        db_session.commit()
        
        response = authenticated_client.post(
            "/api/plans/validate",
            json={"action": "transcribe"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["allowed"] is False
        assert "Transcription limit exceeded" in data["message"]
    
    def test_validate_action_enterprise_unlimited(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test POST /api/plans/validate for enterprise user with unlimited limits."""
        test_user.plan = UserPlan.ENTERPRISE
        test_user.session_count = 10000
        test_user.transcription_count = 50000
        db_session.commit()
        
        # All actions should be allowed
        actions = [
            {"action": "create_session"},
            {"action": "transcribe"},
            {"action": "export_transcript", "format": "xlsx"},
            {"action": "upload_file", "file_size_mb": 400}
        ]
        
        for action_data in actions:
            response = authenticated_client.post(
                "/api/plans/validate",
                json=action_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True, f"Action {action_data} should be allowed for enterprise"
    
    def test_get_upgrade_benefits(self):
        """Test the _get_upgrade_benefits helper function."""
        from coaching_assistant.api.plans import _get_upgrade_benefits
        
        # Free to Pro benefits
        benefits = _get_upgrade_benefits(UserPlan.FREE, UserPlan.PRO)
        assert len(benefits) > 0
        assert "10x more sessions" in benefits[0]
        
        # Pro to Enterprise benefits
        benefits = _get_upgrade_benefits(UserPlan.PRO, UserPlan.ENTERPRISE)
        assert len(benefits) > 0
        assert "Unlimited" in benefits[0]
        
        # Free to Enterprise benefits
        benefits = _get_upgrade_benefits(UserPlan.FREE, UserPlan.ENTERPRISE)
        assert len(benefits) > 0
        assert "Unlimited everything" in benefits[0]
    
    def test_next_reset_date_calculation(
        self, authenticated_client: TestClient, test_user: User, db_session: Session
    ):
        """Test that next reset date is calculated correctly."""
        # Set current month start to a specific date
        test_user.plan = UserPlan.FREE
        test_user.current_month_start = datetime(2025, 8, 1)
        db_session.commit()
        
        response = authenticated_client.get("/api/plans/current")
        assert response.status_code == 200
        
        data = response.json()
        # Next reset should be September 1, 2025
        assert data["usageStatus"]["nextReset"] == "2025-09-01T00:00:00"
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/plans/current",
            "/api/plans/compare"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
        
        # Test POST endpoint
        response = client.post("/api/plans/validate", json={"action": "create_session"})
        assert response.status_code == 401