"""Integration tests for Usage History Analytics API endpoints."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.usage_history import UsageHistory
from coaching_assistant.models.usage_log import UsageLog
from coaching_assistant.models.user import User, UserPlan


class TestUsageHistoryAPI:
    """Test suite for Usage History Analytics API endpoints."""

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user with auth token."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def auth_headers(self, test_user):
        """Create auth headers for API requests."""
        # Mock JWT token for testing
        # In real tests, you'd use your actual auth system
        return {"Authorization": f"Bearer mock_token_{test_user.id}"}

    @pytest.fixture
    def sample_usage_history(self, test_user, db_session):
        """Create sample usage history data."""
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        history_records = []

        for i in range(7):  # 7 days of data
            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=i),
                period_end=base_date - timedelta(days=i) + timedelta(days=1),
                sessions_created=i + 1,
                audio_minutes_processed=Decimal((i + 1) * 15),
                transcriptions_completed=i + 2,
                exports_generated=i,
                total_cost_usd=Decimal((i + 1) * 2.5),
                plan_name="FREE",
                plan_limits={"minutes": 60, "sessions": 10},
                google_stt_minutes=Decimal((i + 1) * 10),
                assemblyai_minutes=Decimal((i + 1) * 5),
                exports_by_format={"pdf": i, "docx": max(0, i - 1)},
            )
            db_session.add(history)
            history_records.append(history)

        db_session.commit()
        return history_records

    def test_usage_history_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns correct info."""
        response = client.get("/api/v1/usage/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Usage History Analytics API" in data["message"]

    def test_get_usage_history_success(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting usage history successfully."""
        # Mock the auth dependency
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/usage/history?period=7d&period_type=daily",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return list of usage history records
        assert isinstance(data, list)
        assert len(data) == 7  # 7 days of sample data

        # Check structure of first record
        first_record = data[0]
        assert "id" in first_record
        assert "user_id" in first_record
        assert "period_type" in first_record
        assert "usage_metrics" in first_record
        assert "plan_context" in first_record
        assert "cost_metrics" in first_record

        # Verify usage_metrics structure
        usage_metrics = first_record["usage_metrics"]
        assert "sessions_created" in usage_metrics
        assert "audio_minutes_processed" in usage_metrics
        assert "transcriptions_completed" in usage_metrics
        assert isinstance(usage_metrics["sessions_created"], int)
        assert isinstance(usage_metrics["audio_minutes_processed"], float)

    def test_get_usage_history_custom_period(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting usage history with custom date range."""
        mock_auth.return_value = test_user

        # Use custom date range
        start_date = "2024-08-01"
        end_date = "2024-08-07"

        response = client.get(
            f"/api/v1/usage/history?period=custom&from_date={start_date}&to_date={end_date}&period_type=daily",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_usage_trends_success(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting usage trends successfully."""
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/usage/trends?period=7d&group_by=day", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return list of trend data
        assert isinstance(data, list)

        if data:  # If we have data
            first_trend = data[0]
            assert "date" in first_trend
            assert "sessions" in first_trend
            assert "minutes" in first_trend
            assert "hours" in first_trend
            assert "transcriptions" in first_trend
            assert "exports" in first_trend
            assert "cost" in first_trend
            assert "utilization" in first_trend
            assert "success_rate" in first_trend
            assert "avg_duration" in first_trend

            # Verify data types
            assert isinstance(first_trend["sessions"], int)
            assert isinstance(first_trend["minutes"], float)
            assert isinstance(first_trend["hours"], float)
            assert isinstance(first_trend["cost"], float)

    def test_get_usage_predictions_success(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting usage predictions successfully."""
        mock_auth.return_value = test_user

        response = client.get("/api/v1/usage/predictions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check prediction structure
        assert "predicted_sessions" in data
        assert "predicted_minutes" in data
        assert "estimated_limit_date" in data
        assert "confidence" in data
        assert "recommendation" in data
        assert "growth_rate" in data
        assert "current_trend" in data

        # Verify data types
        assert isinstance(data["predicted_sessions"], int)
        assert isinstance(data["predicted_minutes"], int)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["recommendation"], str)
        assert isinstance(data["growth_rate"], float)
        assert data["current_trend"] in ["growing", "stable", "declining"]

    def test_get_usage_insights_success(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting usage insights successfully."""
        mock_auth.return_value = test_user

        response = client.get("/api/v1/usage/insights", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should return list of insights
        assert isinstance(data, list)

        if data:  # If we have insights
            first_insight = data[0]
            assert "type" in first_insight
            assert "title" in first_insight
            assert "message" in first_insight
            assert "suggestion" in first_insight
            assert "priority" in first_insight
            assert "action" in first_insight

            # Verify valid types and priorities
            assert first_insight["type"] in [
                "pattern",
                "optimization",
                "warning",
                "trend",
                "cost",
            ]
            assert first_insight["priority"] in ["low", "medium", "high"]
            if first_insight["action"]:
                assert first_insight["action"] in [
                    "upgrade",
                    "downgrade",
                    "review",
                ]

    def test_get_comprehensive_analytics_success(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test getting comprehensive analytics successfully."""
        mock_auth.return_value = test_user

        response = client.get("/api/v1/usage/analytics?period=7d", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check comprehensive analytics structure
        assert "current_period" in data
        assert "trends" in data
        assert "predictions" in data
        assert "insights" in data
        assert "summary" in data

        # Check current_period structure
        current_period = data["current_period"]
        assert "total_sessions" in current_period
        assert "total_minutes" in current_period
        assert "total_transcriptions" in current_period
        assert "avg_daily_usage" in current_period

        # Check trends is list
        assert isinstance(data["trends"], list)

        # Check predictions structure
        predictions = data["predictions"]
        assert "predicted_sessions" in predictions
        assert "confidence" in predictions

        # Check insights is list
        assert isinstance(data["insights"], list)

        # Check summary structure
        summary = data["summary"]
        assert "data_points" in summary
        assert "total_cost" in summary
        assert "insights_count" in summary

    def test_create_usage_snapshot_success(
        self,
        client: TestClient,
        test_user,
        auth_headers,
        mock_auth,
        db_session,
    ):
        """Test creating a usage snapshot manually."""
        mock_auth.return_value = test_user

        # Create some usage data first
        session = Session(
            user_id=test_user.id,
            title="Test Session",
            audio_filename="test_audio.mp3",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(session)
        db_session.commit()

        usage_log = UsageLog(
            user_id=test_user.id,
            session_id=session.id,
            duration_minutes=30,
            duration_seconds=1800,
            stt_provider="google",
            user_plan="FREE",
        )
        db_session.add(usage_log)
        db_session.commit()

        response = client.post(
            "/api/v1/usage/snapshot?period_type=daily", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should return the created snapshot
        assert "id" in data
        assert "user_id" in data
        assert data["period_type"] == "daily"
        assert "usage_metrics" in data

    def test_export_usage_data_json(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test exporting usage data in JSON format."""
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/usage/export?format=json&period=7d", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "format" in data
        assert data["format"] == "json"
        assert "period" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_export_usage_data_csv_not_implemented(
        self, client: TestClient, test_user, auth_headers, mock_auth
    ):
        """Test that CSV export returns not implemented message."""
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/usage/export?format=csv&period=7d", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "not yet implemented" in data["message"]

    def test_export_usage_data_invalid_format(
        self, client: TestClient, test_user, auth_headers, mock_auth
    ):
        """Test that invalid export format returns error."""
        mock_auth.return_value = test_user

        response = client.get(
            "/api/v1/usage/export?format=invalid&period=7d",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unsupported export format" in data["detail"]

    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        # Test without auth headers
        endpoints = [
            "/api/v1/usage/history",
            "/api/v1/usage/trends",
            "/api/v1/usage/predictions",
            "/api/v1/usage/insights",
            "/api/v1/usage/analytics",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should return 401 or 403 (depending on auth implementation)
            assert response.status_code in [
                401,
                403,
                422,
            ]  # 422 for missing dependency

    def test_usage_history_with_no_data(
        self, client: TestClient, test_user, auth_headers, mock_auth
    ):
        """Test endpoints when user has no usage data."""
        mock_auth.return_value = test_user

        # Test history endpoint with no data
        response = client.get("/api/v1/usage/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

        # Test trends endpoint with no data
        response = client.get("/api/v1/usage/trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test predictions with no data
        response = client.get("/api/v1/usage/predictions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == 0.0
        assert "Insufficient" in data["recommendation"]

        # Test insights with no data
        response = client.get("/api/v1/usage/insights", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_trends_with_different_group_by(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test trends endpoint with different grouping options."""
        mock_auth.return_value = test_user

        # Test daily grouping
        response = client.get("/api/v1/usage/trends?group_by=day", headers=auth_headers)
        assert response.status_code == 200

        # Test weekly grouping
        response = client.get(
            "/api/v1/usage/trends?group_by=week", headers=auth_headers
        )
        assert response.status_code == 200

        # Test monthly grouping
        response = client.get(
            "/api/v1/usage/trends?group_by=month", headers=auth_headers
        )
        assert response.status_code == 200

    def test_analytics_different_periods(
        self,
        client: TestClient,
        test_user,
        sample_usage_history,
        auth_headers,
        mock_auth,
    ):
        """Test analytics endpoint with different time periods."""
        mock_auth.return_value = test_user

        periods = ["7d", "30d", "3m"]

        for period in periods:
            response = client.get(
                f"/api/v1/usage/analytics?period={period}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Should have consistent structure regardless of period
            assert "current_period" in data
            assert "trends" in data
            assert "predictions" in data
            assert "insights" in data
            assert "summary" in data

    def test_error_handling(
        self,
        client: TestClient,
        test_user,
        auth_headers,
        mock_auth,
        db_session,
    ):
        """Test API error handling."""
        mock_auth.return_value = test_user

        # Test with invalid period format for custom period
        response = client.get(
            "/api/v1/usage/history?period=custom&from_date=invalid&to_date=2024-08-07",
            headers=auth_headers,
        )
        # Should handle invalid date format gracefully
        assert response.status_code in [400, 500]  # Depending on validation

    def test_snapshot_different_period_types(
        self, client: TestClient, test_user, auth_headers, mock_auth
    ):
        """Test creating snapshots with different period types."""
        mock_auth.return_value = test_user

        period_types = ["hourly", "daily", "monthly"]

        for period_type in period_types:
            response = client.post(
                f"/api/v1/usage/snapshot?period_type={period_type}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["period_type"] == period_type
