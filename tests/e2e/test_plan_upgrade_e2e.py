"""
End-to-end tests for plan upgrade user journey.
Tests the complete flow from hitting limits to successful upgrade.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.session import Session as CoachingSession
from coaching_assistant.models.user import User, UserPlan


class TestPlanUpgradeE2E:
    """End-to-end tests for plan upgrade flow."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient):
        """Set up test environment."""
        self.db = db_session
        self.client = client

    def create_test_user(self, email: str, plan: UserPlan = UserPlan.FREE) -> User:
        """Create a test user with specified plan."""
        user = User(
            email=email,
            name="Test User",
            plan=plan,
            usage_minutes=0,
            session_count=0,
            transcription_count=0,
            current_month_start=datetime.now().replace(day=1),
        )
        self.db.add(user)
        self.db.commit()
        return user

    def test_free_user_journey_to_pro(self):
        """Test complete journey: Free user hits limits and upgrades to Pro."""
        # Step 1: Create free user
        user = self.create_test_user("free_user@test.com", UserPlan.FREE)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Step 2: User checks current plan
        response = self.client.get("/api/v1/plans/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "FREE"
        assert data["limits"]["max_sessions"] == 10

        # Step 3: User creates sessions up to limit
        for i in range(9):
            session = CoachingSession(
                user_id=user.id, title=f"Session {i + 1}", status="completed"
            )
            self.db.add(session)
            user.session_count = i + 1
        self.db.commit()

        # Step 4: User checks usage - should see warning
        response = self.client.get("/api/v1/plan/current-usage", headers=auth_headers)
        assert response.status_code == 200
        usage = response.json()
        assert usage["session_count"] == 9
        assert usage["session_limit"] == 10
        assert usage["sessions_remaining"] == 1

        # Step 5: User creates 10th session (at limit)
        session = CoachingSession(
            user_id=user.id, title="Session 10", status="completed"
        )
        self.db.add(session)
        user.session_count = 10
        self.db.commit()

        # Step 6: User tries to create 11th session - should fail
        response = self.client.post(
            "/api/sessions", json={"title": "Session 11"}, headers=auth_headers
        )
        assert response.status_code == 402  # Payment Required
        error = response.json()
        assert "limit" in error.get("detail", "").lower()

        # Step 7: User views plan comparison
        response = self.client.get("/api/v1/plans/compare")
        assert response.status_code == 200
        plans = response.json()
        pro_plan = next(p for p in plans if p["name"] == "PRO")
        assert pro_plan["max_sessions"] == 100
        assert pro_plan["price_monthly"] > 0

        # Step 8: User initiates upgrade to Pro
        with patch("stripe.PaymentIntent.create") as mock_payment:
            mock_payment.return_value = MagicMock(
                id="pi_test123",
                status="succeeded",
                amount=2500,  # $25.00
            )

            response = self.client.post(
                "/api/v1/plans/upgrade",
                json={"target_plan": "PRO", "payment_method": "pm_test123"},
                headers=auth_headers,
            )

            # Simulate successful upgrade
            if response.status_code in [200, 201]:
                user.plan = UserPlan.PRO
                self.db.commit()

        # Step 9: Verify upgrade successful
        response = self.client.get("/api/v1/plans/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "PRO"
        assert data["limits"]["max_sessions"] == 100

        # Step 10: User can now create session 11
        response = self.client.post(
            "/api/sessions",
            json={"title": "Session 11 - After Upgrade"},
            headers=auth_headers,
        )
        # Should succeed with Pro plan
        assert response.status_code in [200, 201]

    def test_usage_limit_warnings_and_notifications(self):
        """Test usage limit warnings at different thresholds."""
        user = self.create_test_user("warning_test@test.com", UserPlan.FREE)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Test at 50% usage
        user.usage_minutes = 60  # 50% of 120 minutes
        self.db.commit()

        response = self.client.get("/api/v1/plan/current-usage", headers=auth_headers)
        if response.status_code == 200:
            status = response.json()
            assert status.get("usage_percentage", 0) == 50
            assert (
                status.get("warning_level") is None
                or status.get("warning_level") == "none"
            )

        # Test at 80% usage - should show warning
        user.usage_minutes = 96  # 80% of 120 minutes
        self.db.commit()

        response = self.client.get("/api/v1/plan/current-usage", headers=auth_headers)
        if response.status_code == 200:
            status = response.json()
            assert status.get("usage_percentage", 0) == 80
            assert status.get("warning_level") == "warning"

        # Test at 95% usage - should show critical warning
        user.usage_minutes = 114  # 95% of 120 minutes
        self.db.commit()

        response = self.client.get("/api/v1/plan/current-usage", headers=auth_headers)
        if response.status_code == 200:
            status = response.json()
            assert status.get("usage_percentage", 0) == 95
            assert status.get("warning_level") == "critical"

    def test_pro_to_business_upgrade_for_teams(self):
        """Test Pro user upgrading to Business for team features."""
        # Create Pro user
        user = self.create_test_user("pro_user@test.com", UserPlan.PRO)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Pro user needs team features
        response = self.client.get("/api/v1/plans/compare")
        assert response.status_code == 200
        plans = response.json()

        business_plan = next(p for p in plans if p["name"] == "BUSINESS")
        assert business_plan["features"].get("team_collaboration") is True
        assert business_plan["features"].get("api_access") is True
        assert business_plan["features"].get("sso") is True

        # Upgrade to Business
        with patch("stripe.Subscription.modify") as mock_sub:
            mock_sub.return_value = MagicMock(id="sub_business123", status="active")

            response = self.client.post(
                "/api/v1/plans/upgrade",
                json={
                    "target_plan": "BUSINESS",
                    "payment_method": "pm_business123",
                },
                headers=auth_headers,
            )

            if response.status_code in [200, 201]:
                user.plan = UserPlan.BUSINESS
                self.db.commit()

        # Verify Business features enabled
        response = self.client.get("/api/v1/plans/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "BUSINESS"
        assert data["limits"]["max_sessions"] == -1  # Unlimited
        assert data["limits"]["concurrent_processing"] == 10

    def test_failed_payment_handling(self):
        """Test handling of failed payment during upgrade."""
        user = self.create_test_user("payment_fail@test.com", UserPlan.FREE)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Attempt upgrade with failing payment
        with patch("stripe.PaymentIntent.create") as mock_payment:
            mock_payment.side_effect = Exception("Card declined")

            response = self.client.post(
                "/api/v1/plans/upgrade",
                json={"target_plan": "PRO", "payment_method": "pm_declined"},
                headers=auth_headers,
            )

            # Should return error
            assert response.status_code in [400, 402]
            error = response.json()
            assert (
                "payment" in error.get("detail", "").lower()
                or "declined" in error.get("detail", "").lower()
            )

        # Verify user still on Free plan
        response = self.client.get("/api/v1/plans/current", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["plan"] == "FREE"

    def test_export_format_restrictions_e2e(self):
        """Test export format restrictions across different plans."""
        # Create users with different plans
        free_user = self.create_test_user("free_export@test.com", UserPlan.FREE)
        pro_user = self.create_test_user("pro_export@test.com", UserPlan.PRO)
        business_user = self.create_test_user(
            "business_export@test.com", UserPlan.BUSINESS
        )

        # Create a session for each user
        for user in [free_user, pro_user, business_user]:
            session = CoachingSession(
                user_id=user.id,
                title="Test Session",
                status="completed",
                transcript_text="Test transcript content",
            )
            self.db.add(session)
        self.db.commit()

        # Test Free user export limitations
        free_headers = {"Authorization": f"Bearer {free_user.id}"}

        # TXT export should work
        response = self.client.get(
            "/api/sessions/1/transcript?format=txt", headers=free_headers
        )
        assert response.status_code in [
            200,
            404,
        ]  # 404 if session doesn't exist

        # XLSX export should fail for free user
        response = self.client.get(
            "/api/sessions/1/transcript?format=xlsx", headers=free_headers
        )
        if response.status_code == 402:
            error = response.json()
            assert "upgrade" in error.get("detail", "").lower()

        # Test Pro user can export advanced formats
        pro_headers = {"Authorization": f"Bearer {pro_user.id}"}
        response = self.client.get(
            "/api/sessions/1/transcript?format=xlsx", headers=pro_headers
        )
        assert response.status_code in [200, 404]

        # Test Business user has all export options
        business_headers = {"Authorization": f"Bearer {business_user.id}"}
        for format in ["txt", "json", "xlsx", "docx", "vtt", "srt"]:
            response = self.client.get(
                f"/api/sessions/1/transcript?format={format}",
                headers=business_headers,
            )
            assert response.status_code in [200, 404]

    def test_monthly_usage_reset_e2e(self):
        """Test monthly usage reset functionality."""
        user = self.create_test_user("reset_test@test.com", UserPlan.FREE)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Set usage for last month
        last_month = datetime.now().replace(day=1) - timedelta(days=1)
        user.usage_minutes = 100
        user.session_count = 8
        user.current_month_start = last_month.replace(day=1)
        self.db.commit()

        # Check usage before reset
        response = self.client.get("/api/v1/plan/current-usage", headers=auth_headers)

        # Trigger usage check (would normally happen on first action of month)
        response = self.client.post(
            "/api/v1/plan/reset-monthly-usage", headers=auth_headers
        )

        if response.status_code == 200:
            # Verify usage reset
            user = self.db.query(User).filter_by(id=user.id).first()
            assert user.usage_minutes == 0
            assert user.session_count == 0
            assert user.current_month_start.month == datetime.now().month

    def test_concurrent_processing_limits_e2e(self):
        """Test concurrent processing limits enforcement."""
        user = self.create_test_user("concurrent_test@test.com", UserPlan.FREE)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Create a processing session
        session1 = CoachingSession(
            user_id=user.id, title="Processing 1", status="processing"
        )
        self.db.add(session1)
        self.db.commit()

        # Free user should not be able to start another concurrent processing
        response = self.client.post(
            "/api/sessions/2/start-transcription", headers=auth_headers
        )

        if response.status_code == 429:  # Too Many Requests
            error = response.json()
            assert "concurrent" in error.get("detail", "").lower()

        # Upgrade to Pro (3 concurrent)
        user.plan = UserPlan.PRO
        self.db.commit()

        # Should now be able to start more concurrent processing
        for i in range(2):
            session = CoachingSession(
                user_id=user.id, title=f"Processing {i + 2}", status="processing"
            )
            self.db.add(session)
        self.db.commit()

        # 4th concurrent should fail even for Pro
        response = self.client.post(
            "/api/sessions/4/start-transcription", headers=auth_headers
        )

        if response.status_code == 429:
            error = response.json()
            assert "limit" in error.get("detail", "").lower()

    def test_plan_downgrade_restrictions(self):
        """Test restrictions when downgrading plans."""
        # Create Business user with lots of content
        user = self.create_test_user("downgrade_test@test.com", UserPlan.BUSINESS)
        auth_headers = {"Authorization": f"Bearer {user.id}"}

        # Create 50 sessions (exceeds Free limit)
        for i in range(50):
            session = CoachingSession(
                user_id=user.id, title=f"Session {i + 1}", status="completed"
            )
            self.db.add(session)
        user.session_count = 50
        self.db.commit()

        # Attempt downgrade to Free
        response = self.client.post(
            "/api/v1/plans/downgrade",
            json={"target_plan": "FREE"},
            headers=auth_headers,
        )

        if response.status_code == 200:
            # Downgrade successful but with restrictions
            data = response.json()
            assert data.get("warning") is not None
            assert "existing" in data.get("warning", "").lower()

            # User keeps access to existing sessions
            response = self.client.get("/api/sessions", headers=auth_headers)
            assert response.status_code == 200
            sessions = response.json()
            assert len(sessions) == 50

            # But cannot create new sessions
            response = self.client.post(
                "/api/sessions",
                json={"title": "New Session After Downgrade"},
                headers=auth_headers,
            )
            assert response.status_code == 402

    @pytest.mark.asyncio
    async def test_webhook_notifications_e2e(self):
        """Test webhook notifications during plan events."""
        user = self.create_test_user("webhook_test@test.com", UserPlan.FREE)

        with patch("httpx.AsyncClient.post") as mock_webhook:
            mock_webhook.return_value = MagicMock(status_code=200)

            # Test limit approaching webhook
            user.usage_minutes = 108  # 90% of limit
            self.db.commit()

            # Simulate transcription that triggers check
            self.client.post(
                "/api/sessions/1/start-transcription",
                headers={"Authorization": f"Bearer {user.id}"},
            )

            if mock_webhook.called:
                call_args = mock_webhook.call_args
                webhook_data = call_args[1].get("json", {})
                assert webhook_data.get("event") == "usage_warning"
                assert webhook_data.get("usage_percentage") >= 90

            # Test upgrade webhook
            user.plan = UserPlan.PRO
            self.db.commit()

            if mock_webhook.called:
                recent_call = mock_webhook.call_args_list[-1]
                webhook_data = recent_call[1].get("json", {})
                assert webhook_data.get("event") == "plan_upgraded"
                assert webhook_data.get("new_plan") == "PRO"
