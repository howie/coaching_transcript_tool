"""
API tests for plan limits and usage validation endpoints.
Tests for /api/v1/plan/validate-action endpoint.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.user import User
from coaching_assistant.services.plan_limits import PlanName


class TestPlanValidationAPI:
    """Test suite for plan validation API endpoints."""

    @pytest.fixture
    def free_user(self, db_session: Session) -> User:
        """Create a user with FREE plan."""
        user = User(
            id="test-free-user",
            email="free@example.com",
            plan=PlanName.FREE,
            session_count=0,
            transcription_count=0,
            usage_minutes=0,
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def pro_user(self, db_session: Session) -> User:
        """Create a user with PRO plan."""
        user = User(
            id="test-pro-user",
            email="pro@example.com",
            plan=PlanName.PRO,
            session_count=50,
            transcription_count=100,
            usage_minutes=600,
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def maxed_free_user(self, db_session: Session) -> User:
        """Create a FREE user at their limits."""
        user = User(
            id="test-maxed-user",
            email="maxed@example.com",
            plan=PlanName.FREE,
            session_count=10,  # FREE limit
            transcription_count=20,  # FREE limit
            usage_minutes=120,  # FREE limit (2 hours)
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_validate_action_create_session_allowed(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation allows session creation when under limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["message"] is None
        assert data["limit_info"]["type"] == "sessions"
        assert data["limit_info"]["current"] == 0
        assert data["limit_info"]["limit"] == 10

    def test_validate_action_create_session_blocked(
        self, client: TestClient, maxed_free_user: User, auth_headers: dict
    ):
        """Test validation blocks session creation when at limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "reached your monthly session limit" in data["message"]
        assert data["limit_info"]["type"] == "sessions"
        assert data["limit_info"]["current"] == 10
        assert data["limit_info"]["limit"] == 10
        assert data["upgrade_suggestion"]["plan_id"] == "PRO"
        assert data["upgrade_suggestion"]["display_name"] == "Pro Plan"

    def test_validate_action_transcribe_allowed(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation allows transcription when under limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "transcribe", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["limit_info"]["type"] == "transcriptions"
        assert data["limit_info"]["current"] == 0
        assert data["limit_info"]["limit"] == 20

    def test_validate_action_transcribe_blocked(
        self, client: TestClient, maxed_free_user: User, auth_headers: dict
    ):
        """Test validation blocks transcription when at limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "transcribe", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "reached your monthly transcription limit" in data["message"]
        assert data["limit_info"]["type"] == "transcriptions"
        assert data["limit_info"]["current"] == 20
        assert data["limit_info"]["limit"] == 20

    def test_validate_action_check_minutes_allowed(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation allows minutes usage when under limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "check_minutes", "params": {"duration_min": 30}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["limit_info"]["type"] == "minutes"
        assert data["limit_info"]["current"] == 0
        assert data["limit_info"]["limit"] == 120

    def test_validate_action_check_minutes_blocked(
        self, client: TestClient, maxed_free_user: User, auth_headers: dict
    ):
        """Test validation blocks minutes usage when at limit."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "check_minutes", "params": {"duration_min": 10}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is False
        assert "reached your monthly audio minutes limit" in data["message"]
        assert data["limit_info"]["type"] == "minutes"
        assert data["limit_info"]["current"] == 120
        assert data["limit_info"]["limit"] == 120

    def test_validate_action_enterprise_unlimited(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """Test validation always allows for Enterprise users."""
        # Create enterprise user
        enterprise_user = User(
            id="test-enterprise-user",
            email="enterprise@example.com",
            plan=PlanName.ENTERPRISE,
            session_count=1000,  # High usage
            transcription_count=5000,
            usage_minutes=10000,
        )
        db_session.add(enterprise_user)
        db_session.commit()

        # Test all actions are allowed
        actions = ["create_session", "transcribe", "check_minutes"]
        for action in actions:
            response = client.post(
                "/api/v1/plan/validate-action",
                json={"action": action, "params": {}},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True
            assert data["limit_info"]["limit"] == -1  # Unlimited

    def test_validate_action_with_file_size(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation with file size parameter."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "upload_file", "params": {"file_size_mb": 50}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Assuming FREE plan has file size limit
        assert "file_size" in data.get("limit_info", {}).get("type", "")

    def test_validate_action_invalid_action(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation with invalid action type."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "invalid_action", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid action" in data["detail"]

    def test_validate_action_reset_date(
        self, client: TestClient, maxed_free_user: User, auth_headers: dict
    ):
        """Test validation includes reset date for monthly limits."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "reset_date" in data["limit_info"]

        # Parse and validate reset date
        reset_date = datetime.fromisoformat(data["limit_info"]["reset_date"])
        now = datetime.now()
        # Reset date should be first day of next month
        assert reset_date.day == 1
        assert reset_date > now

    def test_validate_action_pro_user_higher_limits(
        self, client: TestClient, pro_user: User, auth_headers: dict
    ):
        """Test PRO user has higher limits than FREE."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["limit_info"]["current"] == 50
        assert data["limit_info"]["limit"] == 100  # PRO limit

    def test_validate_action_concurrent_requests(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation handles concurrent requests correctly."""
        import concurrent.futures

        def make_request():
            return client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session", "params": {}},
                headers=auth_headers,
            )

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed with consistent data
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True
            assert data["limit_info"]["current"] == 0

    def test_validate_action_with_cache(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation uses cache for performance."""
        # First request - should hit database
        response1 = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        # Second request - should use cache
        response2 = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    @pytest.mark.parametrize(
        "action,params,expected_type",
        [
            ("create_session", {}, "sessions"),
            ("transcribe", {}, "transcriptions"),
            ("check_minutes", {"duration_min": 10}, "minutes"),
            ("upload_file", {"file_size_mb": 100}, "file_size"),
            ("export_transcript", {"format": "pdf"}, "exports"),
        ],
    )
    def test_validate_multiple_action_types(
        self,
        client: TestClient,
        free_user: User,
        auth_headers: dict,
        action: str,
        params: dict,
        expected_type: str,
    ):
        """Test validation for various action types."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": action, "params": params},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit_info"]["type"] == expected_type


class TestUsageTrackingIntegration:
    """Test usage tracking integration with validation."""

    def test_usage_increments_after_action(
        self,
        client: TestClient,
        free_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test usage counters increment after successful action."""
        # Initial validation
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )
        assert response.json()["limit_info"]["current"] == 0

        # Simulate session creation
        client.post(
            "/api/v1/sessions",
            json={
                "client_id": "test-client",
                "session_date": "2024-12-15",
                "duration_min": 60,
                "fee_amount": 1000,
                "fee_currency": "TWD",
            },
            headers=auth_headers,
        )

        # Check usage incremented
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )
        assert response.json()["limit_info"]["current"] == 1

    def test_monthly_reset(
        self,
        client: TestClient,
        maxed_free_user: User,
        auth_headers: dict,
        db_session: Session,
    ):
        """Test usage resets at month boundary."""
        # User is maxed out
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )
        assert response.json()["allowed"] is False

        # Simulate month change
        with patch(
            "coaching_assistant.services.usage_tracker.datetime"
        ) as mock_datetime:
            # Set to first day of next month
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            mock_datetime.now.return_value = next_month

            # Trigger monthly reset
            from coaching_assistant.tasks.usage_tasks import (
                reset_monthly_usage,
            )

            reset_monthly_usage()

            # Check usage is reset
            response = client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session", "params": {}},
                headers=auth_headers,
            )
            assert response.json()["allowed"] is True
            assert response.json()["limit_info"]["current"] == 0


class TestValidationPerformance:
    """Test performance characteristics of validation endpoint."""

    @pytest.mark.benchmark
    def test_validation_response_time(
        self,
        client: TestClient,
        free_user: User,
        auth_headers: dict,
        benchmark,
    ):
        """Test validation endpoint response time."""

        def validate():
            return client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session", "params": {}},
                headers=auth_headers,
            )

        result = benchmark(validate)
        assert result.status_code == 200
        # Response should be under 200ms
        assert benchmark.stats["mean"] < 0.2

    def test_validation_with_large_usage(
        self, client: TestClient, db_session: Session, auth_headers: dict
    ):
        """Test validation performance with high usage numbers."""
        # Create user with very high usage
        heavy_user = User(
            id="test-heavy-user",
            email="heavy@example.com",
            plan=PlanName.PRO,
            session_count=90,  # Near PRO limit
            transcription_count=180,
            usage_minutes=1100,
        )
        db_session.add(heavy_user)
        db_session.commit()

        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] is True
        assert data["limit_info"]["current"] == 90
        assert data["limit_info"]["limit"] == 100


class TestValidationErrorHandling:
    """Test error handling in validation endpoint."""

    def test_validation_without_auth(self, client: TestClient):
        """Test validation requires authentication."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"action": "create_session", "params": {}},
        )

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_validation_missing_action(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation with missing action field."""
        response = client.post(
            "/api/v1/plan/validate-action",
            json={"params": {}},
            headers=auth_headers,
        )

        assert response.status_code == 422
        assert "field required" in str(response.json()["detail"])

    def test_validation_database_error(
        self, client: TestClient, free_user: User, auth_headers: dict
    ):
        """Test validation handles database errors gracefully."""
        with patch(
            "coaching_assistant.services.usage_tracker.UsageTracker.get_current_usage"
        ) as mock_get:
            mock_get.side_effect = Exception("Database connection error")

            response = client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session", "params": {}},
                headers=auth_headers,
            )

            # Should fail open (allow action) on error
            assert response.status_code == 200
            data = response.json()
            assert data["allowed"] is True
            assert "temporarily unavailable" in data.get("message", "")
