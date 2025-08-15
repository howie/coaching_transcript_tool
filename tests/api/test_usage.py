"""Tests for usage tracking API endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.models.usage_log import UsageLog
from coaching_assistant.models.usage_analytics import UsageAnalytics


class TestUsageAPI:
    """Test suite for usage tracking endpoints."""
    
    def test_get_current_month_usage(
        self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session
    ):
        """Test GET /api/usage/current-month endpoint."""
        # Set up user with some usage
        test_user.plan = UserPlan.PRO
        test_user.usage_minutes = 600
        test_user.session_count = 50
        test_user.transcription_count = 100
        test_user.current_month_start = datetime.now().replace(day=1)
        db_session.commit()
        
        response = client.get("/api/usage/current-month", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == str(test_user.id)
        assert data["plan"] == "pro"
        assert data["current_month"]["usage_minutes"] == 600
        assert data["current_month"]["session_count"] == 50
        assert data["current_month"]["transcription_count"] == 100
        assert data["usage_percentage"] == 50.0  # 600/1200 minutes
        assert data["minutes_remaining"] == 600
        assert data["can_create_session"] is True
    
    def test_get_current_month_usage_unlimited_plan(
        self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session
    ):
        """Test current month usage for enterprise user with unlimited limits."""
        test_user.plan = UserPlan.ENTERPRISE
        test_user.usage_minutes = 10000
        test_user.session_count = 1000
        db_session.commit()
        
        response = client.get("/api/usage/current-month", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan"] == "enterprise"
        assert data["usage_percentage"] == 0  # No percentage for unlimited
        assert data["minutes_remaining"] == float("inf")
        assert data["can_create_session"] is True
    
    @patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_usage_summary')
    def test_get_usage_summary(
        self, mock_get_summary, client: TestClient, auth_headers: dict, test_user: User
    ):
        """Test GET /api/usage/summary endpoint."""
        # Mock the service response
        mock_summary = {
            "user_id": str(test_user.id),
            "current_month": {
                "sessions": 10,
                "minutes": 120,
                "transcriptions": 20
            },
            "lifetime": {
                "sessions": 50,
                "minutes": 600,
                "transcriptions": 100
            },
            "recent_activity": [],
            "monthly_trend": []
        }
        mock_get_summary.return_value = mock_summary
        
        response = client.get("/api/usage/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data == mock_summary
        mock_get_summary.assert_called_once()
    
    @patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_usage_summary')
    def test_get_usage_summary_error_handling(
        self, mock_get_summary, client: TestClient, auth_headers: dict
    ):
        """Test error handling in usage summary endpoint."""
        mock_get_summary.side_effect = Exception("Database error")
        
        response = client.get("/api/usage/summary", headers=auth_headers)
        assert response.status_code == 500
        assert "Failed to get usage summary" in response.json()["detail"]
    
    @patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_usage_history')
    def test_get_usage_history(
        self, mock_get_history, client: TestClient, auth_headers: dict, test_user: User
    ):
        """Test GET /api/usage/history endpoint."""
        mock_history = {
            "user_id": str(test_user.id),
            "months_requested": 3,
            "history": [
                {
                    "month": "2025-08",
                    "sessions": 10,
                    "minutes": 120,
                    "transcriptions": 20
                },
                {
                    "month": "2025-07",
                    "sessions": 8,
                    "minutes": 100,
                    "transcriptions": 16
                }
            ]
        }
        mock_get_history.return_value = mock_history
        
        response = client.get("/api/usage/history?months=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data == mock_history
        mock_get_history.assert_called_once_with(str(test_user.id), 3)
    
    def test_get_usage_history_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test usage history parameter validation."""
        # Test invalid months parameter
        response = client.get("/api/usage/history?months=0", headers=auth_headers)
        assert response.status_code == 422  # Validation error
        
        response = client.get("/api/usage/history?months=13", headers=auth_headers)
        assert response.status_code == 422  # Validation error
        
        # Test default value
        with patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_usage_history') as mock:
            mock.return_value = {"history": []}
            response = client.get("/api/usage/history", headers=auth_headers)
            assert response.status_code == 200
            mock.assert_called_with(pytest.any(str), 3)  # Default is 3 months
    
    @patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_analytics')
    def test_get_user_analytics(
        self, mock_get_analytics, client: TestClient, auth_headers: dict, test_user: User
    ):
        """Test GET /api/usage/analytics endpoint."""
        mock_analytics = {
            "user_id": str(test_user.id),
            "period": "12_months",
            "monthly_data": [
                {
                    "month": "2025-08",
                    "transcriptions_by_type": {"new": 5, "retry": 2},
                    "minutes_by_provider": {"google": 100, "assemblyai": 20},
                    "cost_breakdown": {"google": 5.0, "assemblyai": 2.0},
                    "average_duration": 12.0
                }
            ],
            "totals": {
                "total_transcriptions": 100,
                "total_minutes": 1200,
                "total_cost": 60.0
            }
        }
        mock_get_analytics.return_value = mock_analytics
        
        response = client.get("/api/usage/analytics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data == mock_analytics
        mock_get_analytics.assert_called_once_with(str(test_user.id))
    
    def test_admin_analytics_requires_admin(
        self, client: TestClient, auth_headers: dict, test_user: User, db_session: Session
    ):
        """Test that admin endpoints require admin privileges."""
        # Regular user should be denied
        test_user.is_admin = False
        db_session.commit()
        
        response = client.get("/api/usage/admin/analytics", headers=auth_headers)
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]
    
    @patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_admin_analytics')
    def test_admin_analytics_success(
        self, mock_get_analytics, client: TestClient, admin_headers: dict, admin_user: User
    ):
        """Test GET /api/usage/admin/analytics with admin user."""
        mock_analytics = {
            "total_users": 100,
            "total_transcriptions": 5000,
            "total_minutes": 60000,
            "plan_distribution": {
                "free": 70,
                "pro": 25,
                "enterprise": 5
            }
        }
        mock_get_analytics.return_value = mock_analytics
        
        response = client.get("/api/usage/admin/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data == mock_analytics
        mock_get_analytics.assert_called_once()
    
    def test_admin_analytics_with_filters(
        self, client: TestClient, admin_headers: dict
    ):
        """Test admin analytics with date and plan filters."""
        with patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_admin_analytics') as mock:
            mock.return_value = {"filtered_data": True}
            
            # Test with date filters
            response = client.get(
                "/api/usage/admin/analytics"
                "?start_date=2025-08-01T00:00:00"
                "&end_date=2025-08-31T23:59:59",
                headers=admin_headers
            )
            assert response.status_code == 200
            
            # Test with plan filter
            response = client.get(
                "/api/usage/admin/analytics?plan_filter=pro",
                headers=admin_headers
            )
            assert response.status_code == 200
    
    def test_admin_get_specific_user_usage(
        self, client: TestClient, admin_headers: dict, test_user: User, db_session: Session
    ):
        """Test GET /api/usage/admin/user/{user_id} endpoint."""
        with patch('coaching_assistant.services.usage_tracking.UsageTrackingService.get_user_usage_summary') as mock:
            mock.return_value = {"user_id": str(test_user.id), "usage": "data"}
            
            response = client.get(
                f"/api/usage/admin/user/{test_user.id}",
                headers=admin_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["user_id"] == str(test_user.id)
            mock.assert_called_once_with(str(test_user.id))
    
    def test_admin_get_nonexistent_user_usage(
        self, client: TestClient, admin_headers: dict
    ):
        """Test admin endpoint with non-existent user."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/api/usage/admin/user/{fake_user_id}",
            headers=admin_headers
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_admin_monthly_report(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test GET /api/usage/admin/monthly-report endpoint."""
        # Create test analytics data
        analytics1 = UsageAnalytics(
            user_id="user1",
            month_year="2025-08",
            transcriptions_completed=10,
            total_minutes_processed=120.5,
            total_cost_usd=6.0,
            primary_plan="pro",
            google_stt_minutes=100.0,
            assemblyai_minutes=20.5,
            period_start=datetime(2025, 8, 1),
            period_end=datetime(2025, 8, 31)
        )
        analytics2 = UsageAnalytics(
            user_id="user2",
            month_year="2025-08",
            transcriptions_completed=5,
            total_minutes_processed=60.0,
            total_cost_usd=3.0,
            primary_plan="free",
            google_stt_minutes=60.0,
            assemblyai_minutes=0.0,
            period_start=datetime(2025, 8, 1),
            period_end=datetime(2025, 8, 31)
        )
        db_session.add_all([analytics1, analytics2])
        db_session.commit()
        
        response = client.get(
            "/api/usage/admin/monthly-report?month_year=2025-08",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["month_year"] == "2025-08"
        assert data["total_users"] == 2
        assert data["summary"]["total_transcriptions"] == 15
        assert data["summary"]["total_minutes"] == 180.5
        assert data["summary"]["total_cost_usd"] == 9.0
        
        # Check plan breakdown
        assert "pro" in data["plan_breakdown"]
        assert data["plan_breakdown"]["pro"]["users"] == 1
        assert data["plan_breakdown"]["pro"]["transcriptions"] == 10
        
        # Check provider breakdown
        assert data["provider_breakdown"]["google"]["minutes"] == 160.0
        assert data["provider_breakdown"]["assemblyai"]["minutes"] == 20.5
    
    def test_admin_monthly_report_invalid_format(
        self, client: TestClient, admin_headers: dict
    ):
        """Test monthly report with invalid date format."""
        response = client.get(
            "/api/usage/admin/monthly-report?month_year=2025-13",  # Invalid month
            headers=admin_headers
        )
        assert response.status_code == 400
        assert "Invalid month format" in response.json()["detail"]
        
        response = client.get(
            "/api/usage/admin/monthly-report?month_year=2025/08",  # Wrong separator
            headers=admin_headers
        )
        assert response.status_code == 400
    
    def test_admin_monthly_report_no_data(
        self, client: TestClient, admin_headers: dict, db_session: Session
    ):
        """Test monthly report when no data exists for the month."""
        response = client.get(
            "/api/usage/admin/monthly-report?month_year=2024-01",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["month_year"] == "2024-01"
        assert data["total_users"] == 0
        assert "No data available" in data["message"]
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/usage/summary",
            "/api/usage/history",
            "/api/usage/analytics",
            "/api/usage/current-month"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an admin user for testing."""
    admin = User(
        id="admin-user-id",
        email="admin@example.com",
        name="Admin User",
        is_admin=True,
        plan=UserPlan.ENTERPRISE
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Create auth headers for admin user."""
    # In a real test, you'd generate a proper JWT token
    # This is a simplified version
    return {"Authorization": f"Bearer admin-token-for-{admin_user.id}"}