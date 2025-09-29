"""Integration tests for billing analytics API endpoints."""

from datetime import datetime, UTC, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from coaching_assistant.main import app
from coaching_assistant.models.billing_analytics import BillingAnalytics
from coaching_assistant.models.user import User, UserPlan, UserRole


class TestBillingAnalyticsAPI:
    """Test billing analytics API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def admin_user(self):
        """Create admin user for testing."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.email = "admin@test.com"
        user.name = "Admin User"
        user.role = UserRole.ADMIN
        user.plan = UserPlan.ENTERPRISE
        return user

    @pytest.fixture
    def mock_auth_admin(self, admin_user):
        """Mock authentication to return admin user."""
        with patch(
            "coaching_assistant.api.dependencies.require_admin"
        ) as mock_require_admin:
            mock_require_admin.return_value = admin_user
            yield mock_require_admin

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch("coaching_assistant.core.database.get_db") as mock_get_db:
            db = Mock()
            mock_get_db.return_value = db
            yield db

    @pytest.fixture
    def sample_billing_data(self):
        """Create sample billing analytics data."""
        period_start = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        return [
            BillingAnalytics(
                id=uuid4(),
                user_id=uuid4(),
                period_type="monthly",
                period_start=period_start,
                period_end=period_start + timedelta(days=30),
                plan_name="PRO",
                total_revenue_usd=Decimal("99.99"),
                subscription_revenue_usd=Decimal("99.99"),
                total_minutes_processed=Decimal("500.0"),
                sessions_created=20,
                transcriptions_completed=25,
                plan_utilization_percentage=Decimal("75.0"),
                churn_risk_score=Decimal("0.2"),
                success_rate_percentage=Decimal("95.0"),
            )
        ]

    def test_get_billing_analytics_overview_success(
        self, client, mock_auth_admin, mock_db, sample_billing_data
    ):
        """Test successful billing analytics overview request."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_admin_overview.return_value = {
                "revenue_metrics": {
                    "total_revenue": 99.99,
                    "subscription_revenue": 99.99,
                    "overage_revenue": 0.0,
                    "one_time_fees": 0.0,
                    "gross_margin": 74.99,
                    "gross_margin_percentage": 75.0,
                    "avg_revenue_per_user": 99.99,
                    "avg_revenue_per_minute": 0.2,
                },
                "usage_metrics": {
                    "total_sessions": 20,
                    "total_transcriptions": 25,
                    "total_minutes": 500.0,
                    "total_hours": 8.33,
                    "avg_session_duration": 20.0,
                    "success_rate": 95.0,
                    "unique_active_users": 1,
                },
                "customer_segments": [
                    {
                        "segment": "power",
                        "user_count": 1,
                        "total_revenue": 99.99,
                        "avg_revenue_per_user": 99.99,
                        "avg_utilization": 75.0,
                        "churn_risk_users": 0,
                    }
                ],
                "top_users": [
                    {
                        "id": str(uuid4()),
                        "user_id": str(uuid4()),
                        "user_email": "test@example.com",
                        "user_name": "Test User",
                        "period_type": "monthly",
                        "period_start": datetime.now(UTC),
                        "period_end": datetime.now(UTC) + timedelta(days=30),
                        "plan_name": "PRO",
                        "total_revenue_usd": 99.99,
                        "total_minutes_processed": 500.0,
                        "plan_utilization_percentage": 75.0,
                        "churn_risk_score": 0.2,
                        "customer_health_score": 85.0,
                        "is_power_user": True,
                        "is_at_risk": False,
                    }
                ],
                "trend_data": [
                    {
                        "date": "2024-01-01",
                        "revenue": 99.99,
                        "users": 1,
                        "sessions": 20,
                        "minutes": 500.0,
                        "new_signups": 1,
                        "churned_users": 0,
                    }
                ],
            }

            response = client.get("/api/v1/admin/billing-analytics/overview")

            assert response.status_code == 200
            data = response.json()

            assert "period_start" in data
            assert "period_end" in data
            assert "revenue_metrics" in data
            assert "usage_metrics" in data
            assert "customer_segments" in data
            assert "top_users" in data
            assert "trend_data" in data

            # Verify revenue metrics structure
            revenue_metrics = data["revenue_metrics"]
            assert revenue_metrics["total_revenue"] == 99.99
            assert revenue_metrics["gross_margin"] == 74.99

            # Verify usage metrics structure
            usage_metrics = data["usage_metrics"]
            assert usage_metrics["total_sessions"] == 20
            assert usage_metrics["unique_active_users"] == 1

    def test_get_billing_analytics_overview_with_parameters(
        self, client, mock_auth_admin, mock_db
    ):
        """Test billing analytics overview with custom parameters."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_admin_overview.return_value = {
                "revenue_metrics": {},
                "usage_metrics": {},
                "customer_segments": [],
                "top_users": [],
                "trend_data": [],
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/overview"
                "?period_type=weekly&period_count=4&end_date=2024-01-31T23:59:59"
            )

            assert response.status_code == 200
            mock_service.get_admin_overview.assert_called_once()

    def test_get_revenue_trends(self, client, mock_auth_admin, mock_db):
        """Test revenue trends endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_revenue_trends.return_value = [
                {
                    "date": "2024-01-01",
                    "revenue": 99.99,
                    "users": 1,
                    "sessions": 20,
                    "minutes": 500.0,
                }
            ]

            response = client.get(
                "/api/v1/admin/billing-analytics/revenue-trends"
                "?period_type=monthly&months=12&plan_filter=pro"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["period_type"] == "monthly"
            assert data["months_included"] == 12
            assert data["plan_filter"] == "pro"
            assert "data" in data
            assert len(data["data"]) == 1

    def test_get_customer_segmentation(self, client, mock_auth_admin, mock_db):
        """Test customer segmentation endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_customer_segmentation.return_value = [
                {
                    "segment": "power",
                    "user_count": 5,
                    "total_revenue": 499.95,
                    "avg_revenue_per_user": 99.99,
                }
            ]

            response = client.get("/api/v1/admin/billing-analytics/customer-segments")

            assert response.status_code == 200
            data = response.json()

            assert "period_start" in data
            assert "period_end" in data
            assert "segments" in data
            assert len(data["segments"]) == 1
            assert data["segments"][0]["segment"] == "power"

    def test_get_user_analytics_detail(self, client, mock_auth_admin, mock_db):
        """Test detailed user analytics endpoint."""
        user_id = uuid4()

        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_user_analytics_detail.return_value = {
                "user_id": user_id,
                "user_email": "test@example.com",
                "user_name": "Test User",
                "current_plan": "pro",
                "total_revenue": 299.97,
                "lifetime_value": 449.95,
                "tenure_days": 180,
                "historical_data": [],
                "predictions": {"predicted_sessions": 30},
                "insights": [],
            }

            response = client.get(
                f"/api/v1/admin/billing-analytics/users/{user_id}/analytics"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == str(user_id)
            assert data["user_email"] == "test@example.com"
            assert data["current_plan"] == "pro"
            assert "historical_data" in data
            assert "predictions" in data
            assert "insights" in data

    def test_get_user_analytics_detail_user_not_found(
        self, client, mock_auth_admin, mock_db
    ):
        """Test user analytics detail when user doesn't exist."""
        user_id = uuid4()

        # Mock User query returning None
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = None
        mock_db.query.return_value = mock_user_query

        response = client.get(
            f"/api/v1/admin/billing-analytics/users/{user_id}/analytics"
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_get_cohort_analysis(self, client, mock_auth_admin, mock_db):
        """Test cohort analysis endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_cohort_analysis.return_value = {
                "cohort_type": "monthly",
                "metric": "revenue",
                "cohorts": [
                    {
                        "cohort_period": "2024-01",
                        "initial_users": 10,
                        "metric_data": [],
                    }
                ],
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/cohort-analysis"
                "?cohort_type=monthly&cohort_size=12&metric=revenue"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["cohort_type"] == "monthly"
            assert data["metric"] == "revenue"
            assert "data" in data

    def test_get_churn_analysis(self, client, mock_auth_admin, mock_db):
        """Test churn analysis endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_churn_analysis.return_value = {
                "summary": {
                    "total_at_risk": 5,
                    "high_risk_count": 2,
                    "medium_risk_count": 3,
                    "potential_revenue_at_risk": 499.95,
                },
                "at_risk_users": [],
                "recommendations": [],
                "predictions": {
                    "predicted_churn_30_days": 1.5,
                    "predicted_revenue_loss": 149.99,
                },
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/churn-analysis"
                "?risk_threshold=0.7&period_months=6&include_predictions=true"
            )

            assert response.status_code == 200
            data = response.json()

            assert "analysis_period" in data
            assert data["risk_threshold"] == 0.7
            assert "summary" in data
            assert "at_risk_users" in data
            assert "predictions" in data

    def test_get_plan_performance(self, client, mock_auth_admin, mock_db):
        """Test plan performance analysis endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_plan_performance_analysis.return_value = {
                "plans": {
                    "FREE": {"user_count": 100, "total_revenue": 0},
                    "PRO": {"user_count": 50, "total_revenue": 4999.50},
                    "ENTERPRISE": {"user_count": 10, "total_revenue": 2999.90},
                },
                "upgrade_patterns": {
                    "free_to_pro": 10,
                    "pro_to_enterprise": 3,
                },
                "recommendations": ["Focus on converting FREE users"],
                "forecasts": {"PRO": {"forecasted_revenue": 6000, "growth_rate": 20}},
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/plan-performance"
                "?period_months=12&include_forecasts=true"
            )

            assert response.status_code == 200
            data = response.json()

            assert "analysis_period" in data
            assert "plan_performance" in data
            assert "upgrade_patterns" in data
            assert "forecasts" in data

    def test_export_billing_analytics(self, client, mock_auth_admin, mock_db):
        """Test analytics data export endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.export_analytics_data.return_value = {
                "format": "csv",
                "data": "id,user_id,revenue\n1,user1,99.99\n",
                "total_records": 1,
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/export"
                "?format=csv&include_user_details=true"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["format"] == "csv"
            assert "data" in data
            assert data["total_records"] == 1

    def test_refresh_billing_analytics_single_user(
        self, client, mock_auth_admin, mock_db
    ):
        """Test refreshing analytics for a single user."""
        user_id = uuid4()

        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.refresh_user_analytics.return_value = {"records_updated": 1}

            response = client.post(
                f"/api/v1/admin/billing-analytics/refresh-analytics"
                f"?user_id={user_id}&period_type=monthly&force_rebuild=false"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert f"Analytics refreshed for user {user_id}" in data["message"]
            assert data["records_updated"] == 1

    def test_refresh_billing_analytics_all_users(
        self, client, mock_auth_admin, mock_db
    ):
        """Test refreshing analytics for all users."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.refresh_all_analytics.return_value = {
                "users_processed": 50,
                "records_updated": 50,
            }

            response = client.post(
                "/api/v1/admin/billing-analytics/refresh-analytics"
                "?period_type=monthly&force_rebuild=false"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "Analytics refreshed for all users" in data["message"]
            assert data["users_processed"] == 50
            assert data["records_updated"] == 50

    def test_refresh_analytics_service_error(self, client, mock_auth_admin, mock_db):
        """Test analytics refresh when service throws an error."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.refresh_all_analytics.side_effect = Exception("Service error")

            response = client.post("/api/v1/admin/billing-analytics/refresh-analytics")

            assert response.status_code == 500
            assert "Failed to refresh analytics" in response.json()["detail"]

    def test_get_health_score_distribution(self, client, mock_auth_admin, mock_db):
        """Test health score distribution endpoint."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.BillingAnalyticsService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_health_score_distribution.return_value = {
                "total_users": 100,
                "score_ranges": {
                    "excellent (90-100)": 20,
                    "good (70-89)": 50,
                    "average (50-69)": 25,
                    "poor (30-49)": 5,
                    "critical (0-29)": 0,
                },
                "avg_health_score": 75.5,
                "at_risk_users": 5,
                "power_users": 20,
            }

            response = client.get(
                "/api/v1/admin/billing-analytics/health-score-distribution"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total_users"] == 100
            assert "score_ranges" in data
            assert data["avg_health_score"] == 75.5
            assert data["at_risk_users"] == 5
            assert data["power_users"] == 20

    def test_unauthorized_access(self, client):
        """Test that endpoints require admin authentication."""
        # Mock no authentication
        response = client.get("/api/v1/admin/billing-analytics/overview")

        # Should return 401 or 403 depending on auth implementation
        assert response.status_code in [401, 403]

    def test_invalid_period_type_parameter(self, client, mock_auth_admin, mock_db):
        """Test validation of period_type parameter."""
        response = client.get(
            "/api/v1/admin/billing-analytics/overview?period_type=invalid"
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_invalid_uuid_parameter(self, client, mock_auth_admin, mock_db):
        """Test validation of UUID parameters."""
        response = client.get(
            "/api/v1/admin/billing-analytics/users/invalid-uuid/analytics"
        )

        # Should return 422 for validation error
        assert response.status_code == 422
