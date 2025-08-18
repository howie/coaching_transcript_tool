"""
Integration tests for plan limits API that would catch the production AttributeError.
These tests actually call the FastAPI endpoints to ensure dependency injection works.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from coaching_assistant.main import app
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.core.database import get_db


class TestPlanLimitsAPIIntegration:
    """Integration tests for plan limits API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user with all required attributes."""
        user = Mock(spec=User)
        user.id = "test-user-123"
        user.email = "test@example.com"
        user.name = "Test User"
        user.plan = UserPlan.FREE
        user.session_count = 5
        user.transcription_count = 10
        user.usage_minutes = 120
        return user

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)

    def test_validate_action_endpoint_with_real_user_object(self, client, mock_user, mock_db_session):
        """Test /api/v1/plan/validate-action with actual User object (not UserResponse)."""
        
        # Mock the dependencies to return our test user
        with patch('coaching_assistant.api.plan_limits.get_current_user_dependency', return_value=mock_user), \
             patch('coaching_assistant.api.plan_limits.get_db', return_value=mock_db_session), \
             patch('coaching_assistant.api.plan_limits.UsageTracker'), \
             patch('coaching_assistant.api.plan_limits.PlanLimits.get_plan_limit') as mock_plan_limits:
            
            # Mock plan limits
            mock_plan_limits.return_value = Mock(max_sessions=10)
            
            # Make the API call
            response = client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session"},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            # Should NOT get AttributeError (500) - should get 200
            assert response.status_code != 500, f"Got 500 error: {response.text}"
            assert response.status_code == 200
            
            # Should have accessed user attributes without error
            data = response.json()
            assert "allowed" in data
            assert "limit_info" in data

    def test_get_current_usage_endpoint_with_real_user_object(self, client, mock_user, mock_db_session):
        """Test /api/v1/plan/current-usage with actual User object."""
        
        with patch('coaching_assistant.api.plan_limits.get_current_user_dependency', return_value=mock_user), \
             patch('coaching_assistant.api.plan_limits.get_db', return_value=mock_db_session), \
             patch('coaching_assistant.api.plan_limits.PlanLimits.get_plan_limit') as mock_plan_limits:
            
            # Mock plan limits  
            mock_plan_limits.return_value = Mock(
                max_sessions=10,
                max_transcriptions=50,
                max_minutes_per_month=300,
                max_file_size_mb=60
            )
            
            response = client.get(
                "/api/v1/plan/current-usage",
                headers={"Authorization": "Bearer fake-token"}
            )
            
            # Should NOT get AttributeError
            assert response.status_code != 500, f"Got 500 error: {response.text}"
            assert response.status_code == 200
            
            data = response.json()
            assert "usage" in data
            assert "sessions" in data["usage"]
            assert data["usage"]["sessions"]["current"] == 5  # From mock_user.session_count

    def test_increment_usage_endpoint_with_real_user_object(self, client, mock_user, mock_db_session):
        """Test /api/v1/plan/increment-usage with actual User object."""
        
        with patch('coaching_assistant.api.plan_limits.get_current_user_dependency', return_value=mock_user), \
             patch('coaching_assistant.api.plan_limits.get_db', return_value=mock_db_session), \
             patch('coaching_assistant.api.plan_limits.UsageTracker') as mock_tracker:
            
            # Mock the tracker
            mock_tracker.return_value.increment_usage.return_value = 6  # New value after increment
            
            response = client.post(
                "/api/v1/plan/increment-usage?metric=session_count&amount=1",
                headers={"Authorization": "Bearer fake-token"}
            )
            
            # Should NOT get AttributeError
            assert response.status_code != 500, f"Got 500 error: {response.text}"
            assert response.status_code == 200
            
            data = response.json()
            assert data["metric"] == "session_count"
            assert data["amount_added"] == 1

    def test_would_fail_with_user_response_object(self, client, mock_db_session):
        """Test that demonstrates the error would occur with UserResponse object."""
        from coaching_assistant.api.auth import UserResponse
        
        # Create UserResponse object (this is what was causing the error)
        user_response = UserResponse(
            id="test-user-123",
            email="test@example.com", 
            name="Test User",
            plan=UserPlan.FREE
        )
        
        # Mock the dependencies to return UserResponse (simulating the bug)
        with patch('coaching_assistant.api.plan_limits.get_current_user_dependency', return_value=user_response), \
             patch('coaching_assistant.api.plan_limits.get_db', return_value=mock_db_session), \
             patch('coaching_assistant.api.plan_limits.UsageTracker'), \
             patch('coaching_assistant.api.plan_limits.PlanLimits.get_plan_limit') as mock_plan_limits:
            
            mock_plan_limits.return_value = Mock(max_sessions=10)
            
            response = client.post(
                "/api/v1/plan/validate-action",
                json={"action": "create_session"},
                headers={"Authorization": "Bearer fake-token"}
            )
            
            # This SHOULD fail with 500 (AttributeError) if we're using UserResponse
            # But since we fixed it, it should work
            if hasattr(user_response, 'session_count'):
                # If UserResponse somehow has these attributes, test should pass
                assert response.status_code == 200
            else:
                # UserResponse doesn't have these attributes, so it should fail
                # But our fix means we're not using UserResponse anymore
                assert response.status_code == 500


class TestErrorDetection:
    """Tests specifically designed to detect the production error pattern."""

    def test_attribute_access_pattern_used_in_production(self):
        """Test the exact attribute access pattern that failed in production."""
        from coaching_assistant.models.user import User
        from coaching_assistant.api.auth import UserResponse
        
        # Create User object (correct)
        user = User()
        user.session_count = 5
        user.transcription_count = 10
        user.usage_minutes = 120
        
        # This should work (the fix)
        session_count = user.session_count or 0
        transcription_count = user.transcription_count or 0
        usage_minutes = user.usage_minutes or 0
        
        assert session_count == 5
        assert transcription_count == 10
        assert usage_minutes == 120
        
        # Create UserResponse object (would cause error)
        user_response = UserResponse(
            id="test-id",
            email="test@example.com",
            name="Test User", 
            plan=UserPlan.FREE
        )
        
        # This would cause AttributeError (demonstrating the bug)
        with pytest.raises(AttributeError):
            _ = user_response.session_count or 0
            
        with pytest.raises(AttributeError):
            _ = user_response.transcription_count or 0
            
        with pytest.raises(AttributeError):
            _ = user_response.usage_minutes or 0

    def test_fastapi_dependency_signature_correctness(self):
        """Test that FastAPI dependencies are correctly configured."""
        from coaching_assistant.api.plan_limits import validate_action, get_current_usage, increment_usage
        from coaching_assistant.api.auth import get_current_user_dependency
        import inspect
        
        # Check that all endpoints use the correct dependency
        endpoints = [validate_action, get_current_usage, increment_usage]
        
        for endpoint in endpoints:
            sig = inspect.signature(endpoint)
            current_user_param = sig.parameters.get('current_user')
            
            assert current_user_param is not None, f"{endpoint.__name__} missing current_user parameter"
            assert hasattr(current_user_param.default, 'dependency'), f"{endpoint.__name__} not using Depends()"
            assert current_user_param.default.dependency == get_current_user_dependency, \
                f"{endpoint.__name__} using wrong dependency"


class TestPreProductionValidation:
    """Tests that should be run before production deployment."""

    def test_all_plan_limits_endpoints_exist(self):
        """Test that all expected endpoints exist and are accessible."""
        client = TestClient(app)
        
        # Test that endpoints exist (will return 401 without auth, but not 404)
        endpoints = [
            "/api/v1/plan/validate-action",
            "/api/v1/plan/current-usage", 
            "/api/v1/plan/increment-usage"
        ]
        
        for endpoint in endpoints:
            if endpoint == "/api/v1/plan/validate-action":
                response = client.post(endpoint, json={"action": "create_session"})
            elif endpoint == "/api/v1/plan/increment-usage":
                response = client.post(f"{endpoint}?metric=session_count")
            else:
                response = client.get(endpoint)
                
            # Should not be 404 (endpoint exists)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
            # Should be 401 (unauthorized) or 422 (validation error), not 500 (server error)
            assert response.status_code in [401, 422], f"Unexpected error for {endpoint}: {response.status_code}"

    def test_user_model_compatibility_with_plan_limits(self):
        """Test that User model is fully compatible with plan limits expectations."""
        from coaching_assistant.models.user import User
        
        # Create user and test all attribute access patterns used in plan_limits.py
        user = User()
        
        # Test null coalescing (pattern used in production code)
        try:
            session_count = user.session_count or 0
            transcription_count = user.transcription_count or 0  
            usage_minutes = user.usage_minutes or 0
            
            # Test plan access
            plan = user.plan
            
            # If we get here, no AttributeError was raised
            assert isinstance(session_count, int)
            assert isinstance(transcription_count, int) 
            assert isinstance(usage_minutes, int)
            
        except AttributeError as e:
            pytest.fail(f"User model incompatible with plan limits: {e}")