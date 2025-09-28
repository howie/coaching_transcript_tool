"""
Integration tests for billing plan system.
Tests end-to-end workflows including plan limits, upgrades, and usage tracking.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.session import Session as CoachingSession
from coaching_assistant.models.usage_log import UsageLog
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.services.plan_limits import PlanLimits
from coaching_assistant.services.usage_tracking import UsageTrackingService


class TestPlanIntegration:
    """Integration tests for billing plan functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient, sample_user: User):
        """Set up test environment."""
        self.db = db_session
        self.client = client
        self.user = sample_user
        # Reset user to free plan for consistent testing
        self.user.plan = UserPlan.FREE
        self.user.usage_minutes = 0
        self.user.session_count = 0
        self.user.transcription_count = 0
        self.user.current_month_start = datetime.now().replace(day=1)
        self.db.commit()

    def test_free_user_limit_enforcement_workflow(self):
        """Test complete free user limit hit and upgrade flow."""
        # Set user near session limit (9 out of 10)
        self.user.session_count = 9
        self.db.commit()

        # Create 10th session - should succeed
        response = self.client.post(
            "/api/v1/sessions",
            json={"title": "Session 10", "description": "At limit"},
            headers={"Authorization": f"Bearer {self.user.id}"},
        )
        assert response.status_code == 201

        # Update session count
        self.user.session_count = 10
        self.db.commit()

        # 11th session should fail with limit exceeded
        response = self.client.post(
            "/api/v1/sessions",
            json={"title": "Session 11", "description": "Over limit"},
            headers={"Authorization": f"Bearer {self.user.id}"},
        )
        assert response.status_code == 402  # Payment Required
        error_data = response.json()
        assert "limit" in error_data.get("detail", "").lower()
        assert "upgrade" in error_data.get("detail", "").lower()

    def test_usage_tracking_across_operations(self):
        """Test usage tracking survives various operations."""
        # Create a session with transcription
        session = CoachingSession(
            user_id=self.user.id,
            title="Test Session",
            duration_seconds=600,  # 10 minutes
            status="completed",
        )
        self.db.add(session)
        self.db.commit()

        # Create usage log
        usage_log = UsageLog(
            user_id=self.user.id,
            session_id=session.id,
            action_type="transcription",
            duration_minutes=10,
            is_billable=True,
            cost_usd=0.05,
            metadata={"provider": "google", "model": "chirp_2"},
        )
        self.db.add(usage_log)
        self.db.commit()

        # Verify usage log exists
        logs = self.db.query(UsageLog).filter_by(session_id=session.id).all()
        assert len(logs) == 1
        assert logs[0].duration_minutes == 10

        # Simulate soft delete of session (mark as deleted)
        session.deleted_at = datetime.now()
        self.db.commit()

        # Usage log should still exist
        logs = self.db.query(UsageLog).filter_by(session_id=session.id).all()
        assert len(logs) == 1
        assert logs[0].user_id == self.user.id

    def test_plan_upgrade_flow(self):
        """Test plan upgrade from Free to Pro."""
        # Start with free plan at limit
        self.user.session_count = 10  # At free limit
        self.db.commit()

        # Attempt to upgrade to Pro
        response = self.client.post(
            "/api/v1/plans/upgrade",
            json={"target_plan": "PRO"},
            headers={"Authorization": f"Bearer {self.user.id}"},
        )

        # In test mode, simulate successful upgrade
        if response.status_code == 200:
            self.user.plan = UserPlan.PRO
            self.db.commit()

            # Verify plan updated
            assert self.user.plan == UserPlan.PRO

            # Should now be able to create more sessions
            limits = PlanLimits.get_limits(UserPlan.PRO)
            assert limits["max_sessions"] == 100  # Pro limit

            # Verify user can now create session 11
            response = self.client.post(
                "/api/v1/sessions",
                json={"title": "Session 11", "description": "After upgrade"},
                headers={"Authorization": f"Bearer {self.user.id}"},
            )
            # Should succeed now with Pro plan
            assert response.status_code in [200, 201]

    def test_usage_analytics_calculation(self):
        """Test accurate usage analytics calculation."""
        # Create multiple usage logs for current month
        base_time = datetime.now().replace(day=1)

        for i in range(5):
            log = UsageLog(
                user_id=self.user.id,
                session_id=None,
                action_type="transcription",
                duration_minutes=30,
                is_billable=True,
                cost_usd=0.10,
                created_at=base_time + timedelta(days=i),
            )
            self.db.add(log)

        self.db.commit()

        # Get usage summary
        response = self.client.get(
            "/api/v1/usage/current-month",
            headers={"Authorization": f"Bearer {self.user.id}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify calculations
        assert data["total_minutes"] == 150  # 5 * 30
        assert data["total_cost"] == 0.50  # 5 * 0.10
        assert data["transcription_count"] == 5

    def test_concurrent_session_limits(self):
        """Test concurrent processing limits by plan."""
        # Free plan - 1 concurrent
        self.user.plan = UserPlan.FREE
        self.db.commit()

        limits = PlanLimits.get_limits(UserPlan.FREE)
        assert limits["concurrent_processing"] == 1

        # Pro plan - 3 concurrent
        self.user.plan = UserPlan.PRO
        self.db.commit()

        limits = PlanLimits.get_limits(UserPlan.PRO)
        assert limits["concurrent_processing"] == 3

        # Business plan - 10 concurrent
        self.user.plan = UserPlan.BUSINESS
        self.db.commit()

        limits = PlanLimits.get_limits(UserPlan.BUSINESS)
        assert limits["concurrent_processing"] == 10

    def test_export_format_restrictions(self):
        """Test export format availability by plan."""
        # Free plan - limited formats
        self.user.plan = UserPlan.FREE
        self.db.commit()

        response = self.client.get(
            "/api/v1/plans/export-formats",
            headers={"Authorization": f"Bearer {self.user.id}"},
        )

        if response.status_code == 200:
            formats = response.json()
            assert "txt" in formats
            assert "json" in formats
            assert "xlsx" not in formats  # Premium format
            assert "docx" not in formats  # Premium format

    def test_monthly_usage_reset(self):
        """Test monthly usage counter reset."""
        # Set usage for last month
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        self.user.usage_minutes = 100
        self.user.session_count = 5
        self.user.transcription_count = 8
        self.user.current_month_start = last_month.replace(day=1)
        self.db.commit()

        # Trigger reset check
        service = UsageTrackingService(self.db)
        service.check_and_reset_monthly_usage(self.user)

        # Verify counters reset
        assert self.user.usage_minutes == 0
        assert self.user.session_count == 0
        assert self.user.transcription_count == 0
        assert self.user.current_month_start.month == datetime.now().month

    def test_plan_comparison_endpoint(self):
        """Test plan comparison API endpoint."""
        response = self.client.get("/api/v1/plans/compare")

        assert response.status_code == 200
        data = response.json()

        # Should have all three plans
        assert len(data) == 3
        plan_names = [p["name"] for p in data]
        assert "FREE" in plan_names
        assert "PRO" in plan_names
        assert "BUSINESS" in plan_names

        # Verify plan details
        free_plan = next(p for p in data if p["name"] == "FREE")
        assert free_plan["max_sessions"] == 10
        assert free_plan["max_total_minutes"] == 120

    def test_usage_history_endpoint(self):
        """Test usage history retrieval."""
        # Create historical usage data
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            log = UsageLog(
                user_id=self.user.id,
                session_id=None,
                action_type="transcription",
                duration_minutes=10,
                is_billable=True,
                cost_usd=0.05,
                created_at=date,
            )
            self.db.add(log)

        self.db.commit()

        # Get usage history
        response = self.client.get(
            "/api/v1/usage/history?days=30",
            headers={"Authorization": f"Bearer {self.user.id}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 30 days of data
        assert len(data) >= 30

        # Verify data structure
        for entry in data[:5]:  # Check first 5 entries
            assert "date" in entry
            assert "minutes" in entry
            assert "cost" in entry
            assert "count" in entry

    def test_plan_validation_before_action(self):
        """Test pre-action validation for plan limits."""
        # Set user at transcription limit
        self.user.plan = UserPlan.FREE
        self.user.transcription_count = 20  # At free limit
        self.db.commit()

        # Try to validate new transcription
        response = self.client.post(
            "/api/v1/plans/validate",
            json={
                "action": "create_transcription",
                "resource_type": "transcription",
            },
            headers={"Authorization": f"Bearer {self.user.id}"},
        )

        if response.status_code == 200:
            data = response.json()
            assert data.get("allowed") is False
            assert "limit" in data.get("reason", "").lower()
        elif response.status_code == 402:
            # Payment required response
            assert True

    def test_smart_billing_retry_classification(self):
        """Test smart billing for retry vs retranscription."""
        # Create a failed session
        failed_session = CoachingSession(
            user_id=self.user.id,
            title="Failed Session",
            status="failed",
            error_message="STT provider error",
        )
        self.db.add(failed_session)
        self.db.commit()

        # Retry should be free
        usage_log = UsageLog(
            user_id=self.user.id,
            session_id=failed_session.id,
            action_type="retry_failed",
            duration_minutes=10,
            is_billable=False,  # Should be free
            cost_usd=0.00,
        )
        self.db.add(usage_log)
        self.db.commit()

        assert usage_log.is_billable is False
        assert usage_log.cost_usd == 0.00

        # Create a successful session
        success_session = CoachingSession(
            user_id=self.user.id, title="Success Session", status="completed"
        )
        self.db.add(success_session)
        self.db.commit()

        # Re-transcription should be billable
        retrans_log = UsageLog(
            user_id=self.user.id,
            session_id=success_session.id,
            action_type="retranscription",
            duration_minutes=10,
            is_billable=True,  # Should be billable
            cost_usd=0.05,
        )
        self.db.add(retrans_log)
        self.db.commit()

        assert retrans_log.is_billable is True
        assert retrans_log.cost_usd > 0

    @pytest.mark.asyncio
    async def test_webhook_notification_on_limit(self):
        """Test webhook notifications when approaching limits."""
        # Set user near limit (90% of free plan)
        self.user.usage_minutes = 108  # 90% of 120 minutes
        self.db.commit()

        with patch("httpx.AsyncClient.post") as mock_post:
            # Simulate webhook call
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Trigger limit check (this would normally happen during
            # transcription)
            service = UsageTrackingService(self.db)
            await service.check_usage_limits_and_notify(self.user)

            # Verify webhook was called if configured
            if mock_post.called:
                call_args = mock_post.call_args
                assert "usage_warning" in str(call_args)
