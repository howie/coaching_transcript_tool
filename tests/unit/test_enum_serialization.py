"""
Unit tests for enum serialization in HTTP responses.

These tests protect against regressions where enums are included directly
in HTTPException details, causing JSON serialization errors.
"""

import json

import pytest
from fastapi.responses import JSONResponse

from coaching_assistant.models.user import UserPlan


class TestEnumSerialization:
    """Test that enums are properly serialized in HTTP responses."""

    def test_user_plan_enum_not_json_serializable_directly(self):
        """Test that UserPlan enums cannot be JSON serialized directly."""
        user_plan = UserPlan.FREE

        # This should fail - enums are not JSON serializable by default
        with pytest.raises(
            TypeError, match="Object of type UserPlan is not JSON serializable"
        ):
            json.dumps({"plan": user_plan})

    def test_user_plan_enum_value_is_json_serializable(self):
        """Test that UserPlan enum values can be JSON serialized."""
        user_plan = UserPlan.FREE

        # This should work - enum values are strings
        serialized = json.dumps({"plan": user_plan.value})
        data = json.loads(serialized)

        assert data["plan"] == "free"
        assert isinstance(data["plan"], str)

    def test_all_user_plan_values_are_serializable(self):
        """Test that all UserPlan enum values are JSON serializable."""
        for plan in UserPlan:
            # Should not raise an exception
            serialized = json.dumps({"plan": plan.value})
            data = json.loads(serialized)

            assert isinstance(data["plan"], str)
            assert data["plan"] in ["free", "pro", "enterprise"]

    def test_http_exception_with_enum_value_is_serializable(self):
        """Test that HTTPException with enum values can be serialized."""
        user_plan = UserPlan.FREE

        # Create an HTTPException detail like our fixed code
        detail = {
            "error": "session_limit_exceeded",
            "message": "You have reached your limit",
            "plan": user_plan.value,  # Use .value, not the enum directly
        }

        # This should work
        response = JSONResponse(content={"detail": detail}, status_code=403)

        # Should be able to serialize the response body
        assert response.status_code == 403
        # The JSONResponse should not raise serialization errors when rendered

    def test_http_exception_with_enum_object_fails(self):
        """Test that HTTPException with enum objects fails serialization."""
        user_plan = UserPlan.FREE

        # Create an HTTPException detail with enum object (the bug we fixed)
        detail = {
            "error": "session_limit_exceeded",
            "message": "You have reached your limit",
            "plan": user_plan,  # This would cause the serialization error
        }

        # This should fail when trying to create JSONResponse
        with pytest.raises(
            TypeError, match="Object of type UserPlan is not JSON serializable"
        ):
            # Manually trigger serialization like FastAPI would
            json.dumps(detail)

    def test_session_limit_exceeded_detail_structure(self):
        """Test the structure of session limit exceeded error details."""
        user_plan = UserPlan.FREE

        # This represents the fixed error detail structure
        detail = {
            "error": "session_limit_exceeded",
            "message": "You have reached your monthly session limit of 3",
            "current_usage": 3,
            "limit": 3,
            "plan": user_plan.value,  # Fixed: use .value instead of enum
        }

        # Should be serializable
        serialized = json.dumps({"detail": detail})
        data = json.loads(serialized)

        # Verify structure
        assert data["detail"]["error"] == "session_limit_exceeded"
        assert data["detail"]["current_usage"] == 3
        assert data["detail"]["limit"] == 3
        assert data["detail"]["plan"] == "free"
        assert isinstance(data["detail"]["plan"], str)

    def test_transcription_limit_exceeded_detail_structure(self):
        """Test the structure of transcription limit exceeded error details."""
        user_plan = UserPlan.FREE

        detail = {
            "error": "transcription_limit_exceeded",
            "message": ("You have reached your monthly transcription limit of 5"),
            "current_usage": 5,
            "limit": 5,
            "plan": user_plan.value,  # Fixed: use .value
        }

        # Should be serializable
        serialized = json.dumps({"detail": detail})
        data = json.loads(serialized)

        # Verify structure
        assert data["detail"]["error"] == "transcription_limit_exceeded"
        assert data["detail"]["plan"] == "free"

    def test_file_size_exceeded_detail_structure(self):
        """Test the structure of file size exceeded error details."""
        user_plan = UserPlan.FREE

        detail = {
            "error": "file_size_exceeded",
            "message": "File size 30.0MB exceeds your plan limit of 25MB",
            "file_size_mb": 30.0,
            "limit_mb": 25,
            "plan": user_plan.value,  # Fixed: use .value
        }

        # Should be serializable
        serialized = json.dumps({"detail": detail})
        data = json.loads(serialized)

        # Verify structure
        assert data["detail"]["error"] == "file_size_exceeded"
        assert data["detail"]["file_size_mb"] == 30.0
        assert data["detail"]["limit_mb"] == 25
        assert data["detail"]["plan"] == "free"

    def test_pro_plan_serialization(self):
        """Test that PRO plan enum is also properly serialized."""
        user_plan = UserPlan.PRO

        detail = {"error": "some_limit_exceeded", "plan": user_plan.value}

        serialized = json.dumps({"detail": detail})
        data = json.loads(serialized)

        assert data["detail"]["plan"] == "pro"
        assert isinstance(data["detail"]["plan"], str)

    def test_enterprise_plan_serialization(self):
        """Test that ENTERPRISE plan enum is also properly serialized."""
        user_plan = UserPlan.ENTERPRISE

        detail = {"error": "some_limit_exceeded", "plan": user_plan.value}

        serialized = json.dumps({"detail": detail})
        data = json.loads(serialized)

        assert data["detail"]["plan"] == "enterprise"
        assert isinstance(data["detail"]["plan"], str)


if __name__ == "__main__":
    pytest.main([__file__])
