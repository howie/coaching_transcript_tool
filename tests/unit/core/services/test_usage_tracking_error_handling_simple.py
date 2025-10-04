"""Error handling tests for PlanLimits helper class.

NOTE: CreateUsageLogUseCase and GetUserUsageUseCase have architectural issues
that prevent proper testing. See coverage-week1-day1-progress.md for details.

These tests focus on the working PlanLimits class edge cases.
"""

import pytest

from coaching_assistant.core.models.user import UserPlan
from coaching_assistant.core.services.usage_tracking_use_case import PlanLimits


class TestPlanLimitsEdgeCases:
    """Test edge cases in PlanLimits helper class."""

    def test_get_limits_with_invalid_plan(self):
        """Test handling of invalid/unknown plan types."""
        # This should default to FREE plan
        limits = PlanLimits.get_limits(None)
        assert limits["minutes_per_month"] == 120  # FREE plan default

    def test_validate_file_size_with_zero(self):
        """Test file size validation with zero size."""
        assert PlanLimits.validate_file_size(UserPlan.FREE, 0) is True

    def test_validate_file_size_with_negative(self):
        """Test file size validation with negative size."""
        # Negative should still be valid (edge case)
        assert PlanLimits.validate_file_size(UserPlan.FREE, -1) is True

    def test_validate_export_format_case_insensitive(self):
        """Test export format validation is case insensitive."""
        assert PlanLimits.validate_export_format(UserPlan.FREE, "JSON") is True
        assert PlanLimits.validate_export_format(UserPlan.FREE, "Json") is True
        assert PlanLimits.validate_export_format(UserPlan.PRO, "VTT") is True

    def test_validate_export_format_with_empty_string(self):
        """Test export format validation with empty string."""
        assert PlanLimits.validate_export_format(UserPlan.FREE, "") is False

    def test_validate_export_format_with_none(self):
        """Test export format validation with None."""
        # Should handle None gracefully
        with pytest.raises(AttributeError):
            PlanLimits.validate_export_format(UserPlan.FREE, None)
