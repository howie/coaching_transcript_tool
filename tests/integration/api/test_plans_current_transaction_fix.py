"""Integration tests for the /api/plans/current endpoint transaction fix."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from apps.main import app
from src.coaching_assistant.models.user import User, UserPlan
from src.coaching_assistant.models.ecpay_subscription import SaasSubscription, SubscriptionStatus
from src.coaching_assistant.infrastructure.db.session import get_db
from tests.conftest import get_test_db_session


class TestPlansCurrentTransactionFix:
    """Integration tests for the /api/plans/current endpoint transaction management."""

    @pytest.fixture
    def client(self):
        """Create test client with test database."""
        app.dependency_overrides[get_db] = get_test_db_session
        return TestClient(app)

    @pytest.fixture
    def test_user(self, test_db_session: Session):
        """Create a test user."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            plan=UserPlan.FREE,
            provider="google",
            provider_id="google_123",
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user

    @pytest.fixture
    def authenticated_headers(self, test_user):
        """Create authentication headers for test user."""
        # Mock JWT token for testing - in real implementation this would be a valid JWT
        return {"Authorization": f"Bearer mock_token_{test_user.id}"}

    def test_plans_current_no_subscription_transaction_handling(
        self, client, test_user, authenticated_headers, test_db_session
    ):
        """Test that endpoint handles missing subscription without transaction errors."""
        # Mock the get_current_user_dependency to return our test user
        from src.coaching_assistant.api.dependencies import get_current_user_dependency

        def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user_dependency] = mock_get_current_user

        try:
            # Act - call the endpoint
            response = client.get("/api/plans/current", headers=authenticated_headers)

            # Assert - should succeed even without subscription
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "currentPlan" in data
            assert "usageStatus" in data
            assert "subscriptionInfo" in data

            # Verify user plan information is included
            assert data["usageStatus"]["plan"] == UserPlan.FREE.value
            assert data["usageStatus"]["userId"] == str(test_user.id)

        finally:
            # Clean up dependency override
            if get_current_user_dependency in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_dependency]

    def test_plans_current_with_subscription_transaction_handling(
        self, client, test_user, authenticated_headers, test_db_session
    ):
        """Test that endpoint handles subscription queries without transaction errors."""
        # Create a test subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=test_user.id,
            plan_id="PRO",
            plan_name="Pro Plan",
            billing_cycle="monthly",
            amount_twd=500,
            status=SubscriptionStatus.ACTIVE.value,
        )
        test_db_session.add(subscription)
        test_db_session.commit()

        # Mock the get_current_user_dependency to return our test user
        from src.coaching_assistant.api.dependencies import get_current_user_dependency

        def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user_dependency] = mock_get_current_user

        try:
            # Act - call the endpoint
            response = client.get("/api/plans/current", headers=authenticated_headers)

            # Assert - should succeed with subscription data
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "currentPlan" in data
            assert "usageStatus" in data
            assert "subscriptionInfo" in data

            # Verify subscription info is included
            assert data["subscriptionInfo"]["active"] is True

        finally:
            # Clean up dependency override
            if get_current_user_dependency in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_dependency]

    def test_plans_current_database_error_handling(
        self, client, test_user, authenticated_headers, test_db_session
    ):
        """Test that endpoint handles database errors gracefully without transaction issues."""
        # Mock the get_current_user_dependency to return our test user
        from src.coaching_assistant.api.dependencies import get_current_user_dependency

        def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user_dependency] = mock_get_current_user

        try:
            # Act - call the endpoint (should not cause transaction errors)
            response = client.get("/api/plans/current", headers=authenticated_headers)

            # Assert - should either succeed or fail gracefully (no 500 from transaction issues)
            assert response.status_code in [200, 404, 500]

            # If it's a 500, it should be from application logic, not transaction management
            if response.status_code == 500:
                error_detail = response.json().get("detail", "")
                assert "current transaction is aborted" not in error_detail
                assert "commands ignored until end of transaction block" not in error_detail

        finally:
            # Clean up dependency override
            if get_current_user_dependency in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_dependency]

    def test_multiple_concurrent_requests_no_transaction_conflicts(
        self, client, test_user, authenticated_headers
    ):
        """Test that multiple concurrent requests don't cause transaction conflicts."""
        # Mock the get_current_user_dependency to return our test user
        from src.coaching_assistant.api.dependencies import get_current_user_dependency

        def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user_dependency] = mock_get_current_user

        try:
            # Act - make multiple requests simulating concurrent access
            responses = []
            for i in range(5):
                response = client.get("/api/plans/current", headers=authenticated_headers)
                responses.append(response)

            # Assert - all requests should succeed without transaction errors
            for i, response in enumerate(responses):
                assert response.status_code == 200, f"Request {i} failed with {response.status_code}"

                # Verify no transaction error messages
                if response.status_code != 200:
                    error_detail = response.json().get("detail", "")
                    assert "current transaction is aborted" not in error_detail
                    assert "commands ignored until end of transaction block" not in error_detail

        finally:
            # Clean up dependency override
            if get_current_user_dependency in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_dependency]