"""Integration tests for subscription endpoint Pydantic validation.

This test suite validates the full request-response cycle including Pydantic
schema validation, specifically for edge cases that mocked tests miss.

Critical: These tests catch Pydantic v2 type validation issues that unit tests
with mocks cannot detect.
"""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from coaching_assistant.api.v1.subscriptions import CurrentSubscriptionResponse, router
from coaching_assistant.core.models.user import User, UserPlan, UserRole
from coaching_assistant.core.services.subscription_management_use_case import (
    SubscriptionRetrievalUseCase,
)
from coaching_assistant.infrastructure.db.repositories.subscription_repository import (
    SubscriptionRepository,
)
from coaching_assistant.infrastructure.db.repositories.user_repository import (
    UserRepository,
)


class TestSubscriptionEndpointPydanticValidation:
    """Integration tests that validate Pydantic response models with real data."""

    def test_get_current_subscription_no_subscription_validates_response(
        self, db_session
    ):
        """Test response with None subscription/payment validates correctly.

        This is a critical integration test that validates the full stack:
        - Real database (no subscription exists)
        - Real service layer returns None values
        - Real Pydantic validation on response

        This test catches Pydantic v2 type validation bugs that mocks hide.

        Bug Context:
        - Pydantic v2 requires `Optional[Dict]` not just `Dict = None`
        - Mocked unit tests bypass Pydantic instantiation
        - Production users without subscriptions triggered 500 errors
        - This test ensures the schema handles None values correctly
        """
        # Arrange: Create user without subscription
        user_repo = UserRepository(db_session)
        subscription_repo = SubscriptionRepository(db_session)

        test_user = User(
            id=uuid4(),
            email=f"test-no-sub-{uuid4()}@example.com",
            role=UserRole.USER,
            plan=UserPlan.FREE,
            created_at=datetime.now(UTC),
        )
        user_repo.create(test_user)
        db_session.commit()

        # Create use case with real repositories
        use_case = SubscriptionRetrievalUseCase(
            user_repo=user_repo, subscription_repo=subscription_repo
        )

        # Act: Get subscription (should return None values)
        result = use_case.get_current_subscription(test_user.id)

        # Assert: Service layer returns expected structure
        assert result["status"] == "no_subscription"
        assert result["subscription"] is None
        assert result["payment_method"] is None

        # Critical: Validate Pydantic schema accepts None values
        # This is where the bug was - Pydantic v2 rejected None for Dict type
        response = CurrentSubscriptionResponse(
            subscription=result["subscription"],
            payment_method=result["payment_method"],
            status=result["status"],
        )

        assert response.subscription is None
        assert response.payment_method is None
        assert response.status == "no_subscription"

    def test_get_current_subscription_endpoint_full_integration(self, db_session):
        """Test full endpoint integration with no subscription.

        This validates the entire request→response→Pydantic validation cycle
        through the FastAPI endpoint.
        """

        # Arrange: Create user without subscription
        user_repo = UserRepository(db_session)
        subscription_repo = SubscriptionRepository(db_session)

        test_user = User(
            id=uuid4(),
            email=f"test-endpoint-{uuid4()}@example.com",
            role=UserRole.USER,
            plan=UserPlan.FREE,
            created_at=datetime.now(UTC),
        )
        user_repo.create(test_user)
        db_session.commit()

        # Setup FastAPI app
        app = FastAPI()
        app.include_router(router, prefix="/v1/subscriptions")
        client = TestClient(app)

        # Mock auth to return our test user
        def get_test_user():
            return test_user

        # Mock use case factory to return real use case
        def get_real_use_case():
            return SubscriptionRetrievalUseCase(
                user_repo=user_repo, subscription_repo=subscription_repo
            )

        # Override dependencies
        from coaching_assistant.api.v1.subscriptions import (
            get_current_user_dependency,
            get_subscription_retrieval_use_case,
        )

        app.dependency_overrides[get_current_user_dependency] = get_test_user
        app.dependency_overrides[get_subscription_retrieval_use_case] = (
            get_real_use_case
        )

        # Act: Call endpoint
        response = client.get("/v1/subscriptions/current")

        # Assert: Should return 200 with valid response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_subscription"
        assert data["subscription"] is None
        assert data["payment_method"] is None

        # Cleanup
        app.dependency_overrides.clear()


class TestPydanticSchemaValidation:
    """Direct Pydantic schema validation tests."""

    def test_current_subscription_response_accepts_none_subscription(self):
        """Verify schema accepts None for subscription field."""
        response = CurrentSubscriptionResponse(
            subscription=None, payment_method={"auth_id": "123"}, status="active"
        )
        assert response.subscription is None
        assert response.payment_method is not None

    def test_current_subscription_response_accepts_none_payment_method(self):
        """Verify schema accepts None for payment_method field."""
        response = CurrentSubscriptionResponse(
            subscription={"id": "sub_123"}, payment_method=None, status="active"
        )
        assert response.subscription is not None
        assert response.payment_method is None

    def test_current_subscription_response_accepts_all_none_values(self):
        """Verify schema accepts None for all optional fields.

        This is the critical test case that production hit.
        User with no subscription should return all None values.
        """
        response = CurrentSubscriptionResponse(
            subscription=None, payment_method=None, status="no_subscription"
        )
        assert response.subscription is None
        assert response.payment_method is None
        assert response.status == "no_subscription"

    def test_current_subscription_response_with_valid_data(self):
        """Verify schema accepts valid subscription data."""
        response = CurrentSubscriptionResponse(
            subscription={
                "id": "sub_123",
                "plan_id": "pro",
                "status": "active",
                "amount_cents": 29900,
            },
            payment_method={"auth_id": "AUTH_123", "auth_status": "active"},
            status="active",
        )
        assert response.subscription["id"] == "sub_123"
        assert response.payment_method["auth_id"] == "AUTH_123"
        assert response.status == "active"
