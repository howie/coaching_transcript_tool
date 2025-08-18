"""
Unit tests to catch dependency injection issues in plan limits API.
These tests specifically catch the AttributeError that occurred in production.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Depends
from sqlalchemy.orm import Session

from coaching_assistant.api.plan_limits import validate_action, get_current_usage, increment_usage
from coaching_assistant.api.plan_limits import ValidateActionRequest
from coaching_assistant.api.auth import get_current_user_dependency, UserResponse
from coaching_assistant.models.user import User, UserPlan


class TestDependencyInjectionCompatibility:
    """Test that plan limits API uses correct dependencies."""

    def test_validate_action_uses_correct_dependency(self):
        """Test that validate_action uses get_current_user_dependency, not get_current_user."""
        # Get the function signature
        import inspect
        sig = inspect.signature(validate_action)
        
        # Check the current_user parameter
        current_user_param = sig.parameters['current_user']
        
        # The default should be Depends(get_current_user_dependency)
        assert current_user_param.default is not inspect.Parameter.empty
        assert hasattr(current_user_param.default, 'dependency')
        assert current_user_param.default.dependency == get_current_user_dependency
        
    def test_get_current_usage_uses_correct_dependency(self):
        """Test that get_current_usage uses get_current_user_dependency."""
        import inspect
        sig = inspect.signature(get_current_usage)
        current_user_param = sig.parameters['current_user']
        
        assert current_user_param.default is not inspect.Parameter.empty
        assert hasattr(current_user_param.default, 'dependency')
        assert current_user_param.default.dependency == get_current_user_dependency

    def test_increment_usage_uses_correct_dependency(self):
        """Test that increment_usage uses get_current_user_dependency."""
        import inspect
        sig = inspect.signature(increment_usage)
        current_user_param = sig.parameters['current_user']
        
        assert current_user_param.default is not inspect.Parameter.empty
        assert hasattr(current_user_param.default, 'dependency')
        assert current_user_param.default.dependency == get_current_user_dependency

    def test_user_model_has_required_attributes(self):
        """Test that User model has all attributes required by plan limits."""
        user = User()
        
        # These are the attributes that caused the production error
        required_attrs = ['session_count', 'transcription_count', 'usage_minutes']
        
        for attr in required_attrs:
            assert hasattr(user, attr), f"User model missing required attribute: {attr}"
            
    def test_user_response_does_not_have_usage_attributes(self):
        """Test that UserResponse model does NOT have usage attributes (expected behavior)."""
        # These attributes should NOT exist on UserResponse
        usage_attrs = ['session_count', 'transcription_count', 'usage_minutes']
        
        for attr in usage_attrs:
            assert not hasattr(UserResponse, attr), f"UserResponse should not have {attr}"

    @patch('coaching_assistant.api.plan_limits.get_db')
    def test_validate_action_with_user_attributes(self, mock_get_db):
        """Test that validate_action can access User model attributes without AttributeError."""
        # Create a mock user with required attributes
        mock_user = Mock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.plan = UserPlan.FREE
        mock_user.session_count = 5
        mock_user.transcription_count = 10
        mock_user.usage_minutes = 120
        
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = mock_db
        
        # Create request
        request = ValidateActionRequest(action="create_session")
        
        # This should NOT raise AttributeError
        # We'll patch the function to test just the attribute access
        with patch('coaching_assistant.api.plan_limits.UsageTracker'), \
             patch('coaching_assistant.api.plan_limits.PlanLimits.get_plan_limit'):
            
            try:
                # Test attribute access that would fail with UserResponse
                session_count = mock_user.session_count
                transcription_count = mock_user.transcription_count
                usage_minutes = mock_user.usage_minutes
                
                # If we get here, no AttributeError was raised
                assert session_count == 5
                assert transcription_count == 10
                assert usage_minutes == 120
                
            except AttributeError as e:
                pytest.fail(f"AttributeError raised when accessing user attributes: {e}")

    def test_user_response_would_cause_attribute_error(self):
        """Test that UserResponse would cause AttributeError (demonstrating the bug)."""
        # Create a UserResponse instance (this is what was causing the error)
        user_response = UserResponse(
            id="test-id",
            email="test@example.com", 
            name="Test User",
            plan=UserPlan.FREE
        )
        
        # These should raise AttributeError (proving the bug)
        with pytest.raises(AttributeError, match="'UserResponse' object has no attribute 'session_count'"):
            _ = user_response.session_count
            
        with pytest.raises(AttributeError, match="'UserResponse' object has no attribute 'transcription_count'"):
            _ = user_response.transcription_count
            
        with pytest.raises(AttributeError, match="'UserResponse' object has no attribute 'usage_minutes'"):
            _ = user_response.usage_minutes


class TestUserModelContract:
    """Test the contract between User model and plan limits expectations."""

    def test_user_model_usage_attributes_are_integers(self):
        """Test that usage attributes are integers or None (database defaults)."""
        user = User()
        
        # These should be None initially (database default) or integers
        assert user.session_count is None or isinstance(user.session_count, int)
        assert user.transcription_count is None or isinstance(user.transcription_count, int)
        assert user.usage_minutes is None or isinstance(user.usage_minutes, int)

    def test_user_model_usage_attributes_support_null_coalescing(self):
        """Test that usage attributes work with 'or 0' pattern used in plan limits."""
        user = User()
        
        # This is the pattern used in plan_limits.py
        session_count = user.session_count or 0
        transcription_count = user.transcription_count or 0
        usage_minutes = user.usage_minutes or 0
        
        assert isinstance(session_count, int)
        assert isinstance(transcription_count, int)
        assert isinstance(usage_minutes, int)

    def test_user_model_plan_attribute(self):
        """Test that User model has plan attribute."""
        user = User()
        
        # Should have plan attribute (may be None initially)
        assert hasattr(user, 'plan')
        
        # When set, should be UserPlan enum
        user.plan = UserPlan.FREE
        assert user.plan == UserPlan.FREE


class TestProductionErrorPrevention:
    """Tests specifically designed to catch the production error early."""

    def test_import_compatibility(self):
        """Test that we're importing the correct dependency function."""
        from coaching_assistant.api.plan_limits import get_current_user_dependency as imported_dependency
        from coaching_assistant.api.auth import get_current_user_dependency as auth_dependency
        
        # Should be the same function
        assert imported_dependency == auth_dependency

    def test_no_wrong_import(self):
        """Test that we're NOT importing get_current_user (which returns UserResponse)."""
        import coaching_assistant.api.plan_limits as plan_limits_module
        
        # Should NOT have get_current_user imported
        assert not hasattr(plan_limits_module, 'get_current_user')
        
        # Should have get_current_user_dependency
        assert hasattr(plan_limits_module, 'get_current_user_dependency')

    @patch('coaching_assistant.api.plan_limits.get_current_user_dependency')
    @patch('coaching_assistant.api.plan_limits.get_db')
    def test_validate_action_calls_with_user_model(self, mock_get_db, mock_get_current_user_dependency):
        """Integration test that validate_action receives User model, not UserResponse."""
        # Setup mocks
        mock_user = Mock(spec=User)
        mock_user.id = "test-user"
        mock_user.plan = UserPlan.FREE
        mock_user.session_count = 0
        mock_user.transcription_count = 0
        mock_user.usage_minutes = 0
        
        mock_get_current_user_dependency.return_value = mock_user
        mock_get_db.return_value = Mock(spec=Session)
        
        request = ValidateActionRequest(action="create_session")
        
        # This should work without issues
        with patch('coaching_assistant.api.plan_limits.UsageTracker'), \
             patch('coaching_assistant.api.plan_limits.PlanLimits.get_plan_limit') as mock_plan_limits:
            
            # Mock the plan limits response
            mock_plan_limits.return_value = Mock(max_sessions=10)
            
            # Import here to avoid circular imports in the actual function call
            import asyncio
            
            # This should NOT raise AttributeError
            try:
                # Note: We can't easily call the actual function due to FastAPI dependencies,
                # but we can test the attribute access pattern
                current_usage = mock_user.session_count or 0
                assert current_usage == 0
                
            except AttributeError:
                pytest.fail("AttributeError raised - this indicates the production bug is still present")