"""Plan management use cases for Clean Architecture.

This module contains business logic for plan configuration, validation, and limits
operations. All external dependencies are injected through repository ports.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...exceptions import DomainException
from ..models.plan_configuration import PlanConfiguration
from ..models.user import UserPlan
from ..repositories.ports import (
    PlanConfigurationRepoPort,
    SessionRepoPort,
    SubscriptionRepoPort,
    UsageLogRepoPort,
    UserRepoPort,
)


def _get_plan_value(plan):
    """Safely get the string value from a plan field, handling both enum and string types."""
    return plan.value if hasattr(plan, "value") else plan


class PlanRetrievalUseCase:
    """Use case for retrieving plan information and configurations."""

    def __init__(
        self,
        plan_config_repo: PlanConfigurationRepoPort,
        user_repo: UserRepoPort,
        subscription_repo: SubscriptionRepoPort,
    ):
        self.plan_config_repo = plan_config_repo
        self.user_repo = user_repo
        self.subscription_repo = subscription_repo

    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all available plans with their configurations.

        Returns:
            List of plan configuration dictionaries
        """
        plan_configs = self.plan_config_repo.get_all_active_plans()

        return [self._format_plan_config(config) for config in plan_configs]

    def get_user_current_plan(self, user_id: UUID) -> Dict[str, Any]:
        """Get current plan for a user with detailed information.

        Args:
            user_id: User ID

        Returns:
            Dictionary with current plan information

        Raises:
            DomainException: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise DomainException(f"User not found: {user_id}")

        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if not plan_config:
            # Return fallback plan info if config not found
            return self._get_fallback_plan_info(user.plan)

        # Note: subscription details fetched separately by subscription use case
        # to avoid duplicate queries within same transaction

        plan_info = self._format_plan_config(plan_config)
        plan_info.update(
            {
                "user_plan": _get_plan_value(user.plan),
                "subscription": None,  # Set separately by caller if needed
                "is_current_plan": True,
            }
        )

        return plan_info

    def compare_plans(
        self, plan_types: Optional[List[UserPlan]] = None
    ) -> Dict[str, Any]:
        """Get plan comparison data.

        Args:
            plan_types: Optional list of specific plans to compare

        Returns:
            Dictionary with plan comparison data
        """
        if plan_types:
            plan_configs = [
                self.plan_config_repo.get_by_plan_type(plan_type)
                for plan_type in plan_types
            ]
            plan_configs = [config for config in plan_configs if config]
        else:
            plan_configs = self.plan_config_repo.get_all_active_plans()

        formatted_plans = [self._format_plan_config(config) for config in plan_configs]

        # Sort by sort_order or plan hierarchy
        formatted_plans.sort(key=lambda x: x.get("sort_order", 999))

        return {
            "plans": formatted_plans,
            "comparison_features": self._get_comparison_features(),
            "total_plans": len(formatted_plans),
        }

    def _format_plan_config(self, config: PlanConfiguration) -> Dict[str, Any]:
        """Format plan configuration for API response."""
        limits = config.limits

        # Format limits for frontend display (accessing dataclass fields
        # directly)
        formatted_limits = {
            "maxSessions": self._format_limit_value(limits.max_sessions),
            "maxTotalMinutes": self._format_limit_value(limits.max_total_minutes),
            "maxTranscriptionCount": self._format_limit_value(
                limits.max_transcription_count
            ),
            "maxFileSizeMb": limits.max_file_size_mb,
            "exportFormats": limits.export_formats,
            "concurrentProcessing": limits.concurrent_processing,
            "retentionDays": self._format_retention_days(limits.retention_days),
        }

        return {
            "id": _get_plan_value(config.plan_type),
            "name": config.plan_name,
            "display_name": config.display_name,
            "description": config.description,
            "tagline": config.tagline,
            "limits": formatted_limits,
            "features": config.features or {},
            "pricing": self._get_pricing_dict(config),
            "is_active": config.is_active,
            "sort_order": config.sort_order,
        }

    def _get_pricing_dict(self, config) -> Dict[str, Any]:
        """Build pricing dictionary from PlanConfiguration pricing dataclass."""
        pricing = config.pricing
        return {
            "monthly_usd": pricing.monthly_price_cents / 100,
            "annual_usd": pricing.annual_price_cents / 100,
            "monthly_twd": pricing.monthly_price_twd_cents / 100,
            "annual_twd": pricing.annual_price_twd_cents / 100,
            "currency": pricing.currency,
        }

    def _format_limit_value(self, value: int) -> str | int:
        """Format limit value for display."""
        return "unlimited" if value == -1 else value

    def _format_retention_days(self, value: int) -> str | int:
        """Format retention days for display."""
        return "permanent" if value == -1 else value

    def _format_subscription_info(self, subscription) -> Dict[str, Any]:
        """Format subscription information."""
        return {
            "id": str(subscription.id),
            "status": _get_plan_value(subscription.status),
            "plan_id": subscription.plan_id,
            "billing_cycle": subscription.billing_cycle,
            "created_at": subscription.created_at.isoformat(),
            "next_billing_date": (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end
                else None
            ),
        }

    def _get_fallback_plan_info(self, plan_type: UserPlan) -> Dict[str, Any]:
        """Get fallback plan information when config not found in database."""
        fallback_configs = {
            UserPlan.FREE: {
                "id": "FREE",
                "name": "Free Plan",
                "display_name": "Free",
                "description": "Basic transcription features",
                "limits": {
                    "maxSessions": "unlimited",
                    "maxTotalMinutes": 120,
                    "maxFileSizeMb": 60,
                    "exportFormats": ["json", "txt"],
                    "concurrentProcessing": 1,
                    "retentionDays": 30,
                },
            },
            UserPlan.PRO: {
                "id": "PRO",
                "name": "Pro Plan",
                "display_name": "Pro",
                "description": "Advanced features for professionals",
                "limits": {
                    "maxSessions": "unlimited",
                    "maxTotalMinutes": 1000,
                    "maxFileSizeMb": 200,
                    "exportFormats": ["json", "txt", "excel"],
                    "concurrentProcessing": 3,
                    "retentionDays": 90,
                },
            },
            UserPlan.ENTERPRISE: {
                "id": "ENTERPRISE",
                "name": "Enterprise Plan",
                "display_name": "Enterprise",
                "description": "Full featured plan for teams",
                "limits": {
                    "maxSessions": "unlimited",
                    "maxTotalMinutes": "unlimited",
                    "maxFileSizeMb": 500,
                    "exportFormats": ["json", "txt", "excel"],
                    "concurrentProcessing": 10,
                    "retentionDays": "permanent",
                },
            },
        }

        return fallback_configs.get(plan_type, fallback_configs[UserPlan.FREE])

    def _get_comparison_features(self) -> List[str]:
        """Get list of features for plan comparison."""
        return [
            "maxTotalMinutes",
            "maxFileSizeMb",
            "exportFormats",
            "concurrentProcessing",
            "retentionDays",
            "advancedAnalytics",
            "prioritySupport",
        ]


class PlanValidationUseCase:
    """Use case for validating plan limits and usage."""

    def __init__(
        self,
        plan_config_repo: PlanConfigurationRepoPort,
        user_repo: UserRepoPort,
        session_repo: SessionRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        self.plan_config_repo = plan_config_repo
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.usage_log_repo = usage_log_repo

    def validate_user_limits(self, user_id: UUID) -> Dict[str, Any]:
        """Validate user's current usage against plan limits.

        Args:
            user_id: User ID to validate

        Returns:
            Dictionary with validation results and usage information

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise DomainException(f"User not found: {user_id}")

        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if not plan_config:
            # Fallback with default structure when no plan config found
            current_usage = self._get_current_usage(user_id)
            return {
                "valid": True,
                "message": "No plan limits configured",
                "limits": {},
                "current_usage": current_usage,
                "violations": [],
                "warnings": [],
            }

        limits = plan_config.limits
        current_usage = self._get_current_usage(user_id)

        # Convert PlanLimits dataclass to dictionary for API compatibility
        limits_dict = {
            "maxSessions": limits.max_sessions,
            "maxMinutes": limits.max_total_minutes,
            "maxTranscriptions": limits.max_transcription_count,
            "maxFileSize": limits.max_file_size_mb,
            "exportFormats": limits.export_formats,
            "concurrentJobs": limits.concurrent_processing,
            "retentionDays": limits.retention_days,
        }

        validation_results = {
            "valid": True,
            "limits": limits_dict,
            "current_usage": current_usage,
            "violations": [],
            "warnings": [],
        }

        # Check session count limit
        max_sessions = limits.max_sessions
        if max_sessions > 0 and current_usage["session_count"] >= max_sessions:
            validation_results["valid"] = False
            validation_results["violations"].append(
                {
                    "type": "session_count",
                    "limit": max_sessions,
                    "current": current_usage["session_count"],
                    "message": (
                        f"Session limit exceeded: {current_usage['session_count']}/{max_sessions}"
                    ),
                }
            )

        # Check total minutes limit
        max_minutes = limits.max_total_minutes
        if max_minutes > 0 and current_usage["total_minutes"] >= max_minutes:
            validation_results["valid"] = False
            validation_results["violations"].append(
                {
                    "type": "total_minutes",
                    "limit": max_minutes,
                    "current": current_usage["total_minutes"],
                    "message": (
                        f"Total minutes limit exceeded: {current_usage['total_minutes']}/{max_minutes}"
                    ),
                }
            )

        # Add warnings for approaching limits
        if max_sessions > 0:
            usage_percentage = (current_usage["session_count"] / max_sessions) * 100
            if usage_percentage >= 80:
                validation_results["warnings"].append(
                    {
                        "type": "session_count_warning",
                        "message": (
                            f"Approaching session limit: {usage_percentage:.1f}% used"
                        ),
                    }
                )

        if max_minutes > 0:
            usage_percentage = (current_usage["total_minutes"] / max_minutes) * 100
            if usage_percentage >= 80:
                validation_results["warnings"].append(
                    {
                        "type": "minutes_warning",
                        "message": (
                            f"Approaching minutes limit: {usage_percentage:.1f}% used"
                        ),
                    }
                )

        return validation_results

    def validate_file_size(self, user_id: UUID, file_size_mb: float) -> Dict[str, Any]:
        """Validate if file size is within plan limits.

        Args:
            user_id: User ID
            file_size_mb: File size in megabytes

        Returns:
            Dictionary with validation result
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise DomainException(f"User not found: {user_id}")

        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if not plan_config:
            return {"valid": True, "message": "No file size limits configured"}

        max_file_size = (
            plan_config.limits.max_file_size_mb
        )  # Access dataclass field directly

        if file_size_mb > max_file_size:
            return {
                "valid": False,
                "limit": max_file_size,
                "actual": file_size_mb,
                "message": (
                    f"File size {file_size_mb:.1f}MB exceeds plan limit of {max_file_size}MB"
                ),
            }

        return {
            "valid": True,
            "limit": max_file_size,
            "actual": file_size_mb,
            "message": "File size within limits",
        }

    def _get_current_usage(self, user_id: UUID) -> Dict[str, Any]:
        """Get current usage statistics for user."""
        # Get current period usage (can be configured)
        now = datetime.now(UTC)
        period_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )  # Start of month

        try:
            # Try to get usage from repositories (Clean Architecture approach)
            session_count = self.session_repo.count_user_sessions(
                user_id, since=period_start
            )
            total_minutes = self.session_repo.get_total_duration_minutes(
                user_id, since=period_start
            )

            # Get usage logs for cost calculation
            usage_logs = self.usage_log_repo.get_by_user_id(user_id, period_start, now)
            total_cost = sum(log.cost_usd for log in usage_logs)
        except (AttributeError, Exception):
            # Fallback to user model data during Clean Architecture migration
            user = self.user_repo.get_by_id(user_id)
            session_count = getattr(user, "session_count", 0)
            total_minutes = getattr(user, "usage_minutes", 0)
            total_cost = 0.0  # Default for cost tracking

        return {
            "session_count": session_count,
            "total_minutes": total_minutes,
            "total_cost_usd": float(total_cost),
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),
        }
