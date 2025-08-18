"""
Contract tests between User model and plan limits functionality.
These tests ensure the User model always provides the interface expected by plan limits.
"""

import pytest
from datetime import datetime
from typing import Optional, Union

from coaching_assistant.models.user import User, UserPlan


class TestUserModelPlanLimitsContract:
    """Test the contract between User model and plan limits expectations."""

    def test_user_has_required_usage_tracking_attributes(self):
        """Test that User model has all attributes required for usage tracking."""
        user = User()
        
        # These attributes are required by plan_limits.py
        required_attributes = [
            'session_count',
            'transcription_count', 
            'usage_minutes',
            'plan'
        ]
        
        for attr in required_attributes:
            assert hasattr(user, attr), f"User model missing required attribute: {attr}"

    def test_usage_attributes_are_nullable_integers(self):
        """Test that usage attributes are nullable integers (database schema)."""
        user = User()
        
        # These should be None initially or integers when set
        usage_attrs = ['session_count', 'transcription_count', 'usage_minutes']
        
        for attr in usage_attrs:
            value = getattr(user, attr)
            assert value is None or isinstance(value, int), \
                f"{attr} should be None or int, got {type(value)}"

    def test_usage_attributes_support_null_coalescing_pattern(self):
        """Test that usage attributes work with 'or 0' pattern used in plan_limits.py."""
        user = User()
        
        # This is the exact pattern used in plan_limits.py lines 93, 106, 118, etc.
        session_count = user.session_count or 0
        transcription_count = user.transcription_count or 0
        usage_minutes = user.usage_minutes or 0
        
        # Should all be integers after null coalescing
        assert isinstance(session_count, int)
        assert isinstance(transcription_count, int) 
        assert isinstance(usage_minutes, int)
        
        # Should all be 0 when user attributes are None
        assert session_count == 0
        assert transcription_count == 0
        assert usage_minutes == 0

    def test_usage_attributes_with_actual_values(self):
        """Test usage attributes when they have actual values."""
        user = User()
        user.session_count = 5
        user.transcription_count = 10
        user.usage_minutes = 120
        
        # Null coalescing should return the actual values
        session_count = user.session_count or 0
        transcription_count = user.transcription_count or 0
        usage_minutes = user.usage_minutes or 0
        
        assert session_count == 5
        assert transcription_count == 10
        assert usage_minutes == 120

    def test_plan_attribute_compatibility(self):
        """Test that plan attribute works as expected by plan_limits.py."""
        user = User()
        
        # Plan can be None initially
        assert user.plan is None or isinstance(user.plan, UserPlan)
        
        # When set, should be UserPlan enum
        user.plan = UserPlan.FREE
        assert user.plan == UserPlan.FREE
        assert user.plan.value == "free"
        
        # Test enum conversion pattern used in plan_limits.py
        if user.plan:
            plan_value = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
            assert plan_value == "free"

    def test_user_model_attribute_types(self):
        """Test that all usage attributes have correct types when set."""
        user = User()
        
        # Set attributes to various values
        user.session_count = 5
        user.transcription_count = 10
        user.usage_minutes = 120
        user.plan = UserPlan.PRO
        
        # Verify types
        assert isinstance(user.session_count, int)
        assert isinstance(user.transcription_count, int)
        assert isinstance(user.usage_minutes, int)
        assert isinstance(user.plan, UserPlan)

    def test_user_model_defaults_match_plan_limits_expectations(self):
        """Test that User model defaults work with plan limits logic."""
        user = User()
        
        # Plan limits uses these default patterns
        session_count = user.session_count or 0
        transcription_count = user.transcription_count or 0
        usage_minutes = user.usage_minutes or 0
        
        # All should be valid integers for arithmetic operations
        assert session_count >= 0
        assert transcription_count >= 0
        assert usage_minutes >= 0
        
        # Should support comparison operations used in plan_limits.py
        assert session_count < 1000  # Example limit check
        assert transcription_count < 1000
        assert usage_minutes < 10000


class TestPlanLimitsAttributeAccess:
    """Test specific attribute access patterns used in plan_limits.py."""

    def test_validate_action_create_session_pattern(self):
        """Test attribute access pattern from validate_action for create_session."""
        user = User()
        user.session_count = 5
        
        # This is the exact pattern from plan_limits.py line 93
        current_usage = user.session_count or 0
        limit = 10  # Example limit
        allowed = limit == -1 or current_usage < limit
        
        assert current_usage == 5
        assert allowed is True

    def test_validate_action_transcribe_pattern(self):
        """Test attribute access pattern from validate_action for transcribe."""
        user = User()
        user.transcription_count = 15
        
        # This is the exact pattern from plan_limits.py line 106
        current_usage = user.transcription_count or 0
        limit = 20
        allowed = limit == -1 or current_usage < limit
        
        assert current_usage == 15
        assert allowed is True

    def test_validate_action_check_minutes_pattern(self):
        """Test attribute access pattern from validate_action for check_minutes."""
        user = User()
        user.usage_minutes = 100
        
        # This is the exact pattern from plan_limits.py line 118-124
        current_usage = user.usage_minutes or 0
        requested_minutes = 50
        projected_usage = current_usage + requested_minutes
        limit = 200
        allowed = limit == -1 or projected_usage <= limit
        
        assert current_usage == 100
        assert projected_usage == 150
        assert allowed is True

    def test_get_current_usage_pattern(self):
        """Test attribute access patterns from get_current_usage endpoint."""
        user = User()
        user.session_count = 3
        user.transcription_count = 7
        user.usage_minutes = 45
        user.plan = UserPlan.PRO
        
        # These are the exact patterns from plan_limits.py lines 246, 254, 262
        sessions_current = user.session_count or 0
        transcriptions_current = user.transcription_count or 0
        minutes_current = user.usage_minutes or 0
        
        assert sessions_current == 3
        assert transcriptions_current == 7
        assert minutes_current == 45
        
        # Test plan access pattern
        if user.plan:
            plan_value = user.plan.value if hasattr(user.plan, 'value') else str(user.plan)
            assert plan_value == "pro"


class TestUserModelRobustness:
    """Test that User model is robust against edge cases."""

    def test_user_with_zero_values(self):
        """Test User model with zero usage values."""
        user = User()
        user.session_count = 0
        user.transcription_count = 0
        user.usage_minutes = 0
        
        # Null coalescing should still work
        assert (user.session_count or 0) == 0
        assert (user.transcription_count or 0) == 0
        assert (user.usage_minutes or 0) == 0

    def test_user_with_negative_values(self):
        """Test User model with negative values (edge case)."""
        user = User()
        user.session_count = -1
        user.transcription_count = -5
        user.usage_minutes = -10
        
        # Should still work with plan limits logic
        assert (user.session_count or 0) == -1
        assert (user.transcription_count or 0) == -5
        assert (user.usage_minutes or 0) == -10

    def test_user_with_large_values(self):
        """Test User model with large usage values."""
        user = User()
        user.session_count = 999999
        user.transcription_count = 888888
        user.usage_minutes = 777777
        
        # Should handle large integers
        assert (user.session_count or 0) == 999999
        assert (user.transcription_count or 0) == 888888
        assert (user.usage_minutes or 0) == 777777


class TestContractViolationDetection:
    """Tests to detect if the contract is ever violated."""

    def test_user_response_contract_violation(self):
        """Test that UserResponse does NOT satisfy the contract (by design)."""
        from coaching_assistant.api.auth import UserResponse
        
        user_response = UserResponse(
            id="test-id",
            email="test@example.com",
            name="Test User",
            plan=UserPlan.FREE
        )
        
        # UserResponse should NOT have usage attributes
        usage_attrs = ['session_count', 'transcription_count', 'usage_minutes']
        
        for attr in usage_attrs:
            assert not hasattr(user_response, attr), \
                f"UserResponse should NOT have {attr} - this would mask the contract violation"

    def test_function_signature_enforcement(self):
        """Test that plan limits functions have correct type annotations."""
        from coaching_assistant.api.plan_limits import validate_action, get_current_usage, increment_usage
        from coaching_assistant.models.user import User
        import inspect
        
        functions = [validate_action, get_current_usage, increment_usage]
        
        for func in functions:
            sig = inspect.signature(func)
            current_user_param = sig.parameters.get('current_user')
            
            assert current_user_param is not None, f"{func.__name__} missing current_user parameter"
            
            # Check type annotation if present
            if current_user_param.annotation != inspect.Parameter.empty:
                assert current_user_param.annotation == User, \
                    f"{func.__name__} should annotate current_user as User, not {current_user_param.annotation}"

    def test_model_import_correctness(self):
        """Test that plan_limits.py imports User model, not UserResponse."""
        import coaching_assistant.api.plan_limits as plan_limits_module
        
        # Should import User model
        assert hasattr(plan_limits_module, 'User'), "plan_limits.py should import User model"
        
        # Should NOT import UserResponse
        assert not hasattr(plan_limits_module, 'UserResponse'), \
            "plan_limits.py should NOT import UserResponse"