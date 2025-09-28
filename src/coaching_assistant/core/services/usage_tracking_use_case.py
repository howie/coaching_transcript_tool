"""Usage tracking use case following Clean Architecture principles.

This module contains the business logic for usage tracking without
any infrastructure dependencies. It operates only through repository
ports and domain models.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..models.session import Session as SessionModel
from ..models.usage_history import UsageHistory
from ..models.usage_log import TranscriptionType, UsageLog
from ..models.user import User, UserPlan
from ..repositories.ports import (
    SessionRepoPort,
    UsageAnalyticsRepoPort,
    UsageHistoryRepoPort,
    UsageLogRepoPort,
    UserRepoPort,
)

logger = logging.getLogger(__name__)


class PlanLimits:
    """Plan limit configuration - pure business logic."""

    @staticmethod
    def get_limits(plan: UserPlan) -> Dict[str, Any]:
        """Get plan limits as dictionary."""
        limits = {
            UserPlan.FREE: {
                "minutes_per_month": 120,  # 2 hours
                "sessions_per_month": 10,
                "max_file_size_mb": 50,
                "export_formats": ["json", "txt"],
                "features": ["basic_transcription"],
            },
            UserPlan.PRO: {
                "minutes_per_month": 1200,  # 20 hours
                "sessions_per_month": 100,
                "max_file_size_mb": 200,
                "export_formats": ["json", "txt", "vtt", "srt"],
                "features": [
                    "basic_transcription",
                    "speaker_diarization",
                    "export_formats",
                ],
            },
            UserPlan.ENTERPRISE: {
                "minutes_per_month": float("inf"),
                "sessions_per_month": float("inf"),
                "max_file_size_mb": 500,
                "export_formats": ["json", "txt", "vtt", "srt", "xlsx"],
                "features": [
                    "basic_transcription",
                    "speaker_diarization",
                    "export_formats",
                    "api_access",
                    "priority_support",
                ],
            },
        }
        return limits.get(plan, limits[UserPlan.FREE])

    @staticmethod
    def validate_file_size(plan: UserPlan, file_size_mb: float) -> bool:
        """Validate if file size is within plan limits."""
        limits = PlanLimits.get_limits(plan)
        return file_size_mb <= limits["max_file_size_mb"]

    @staticmethod
    def validate_export_format(plan: UserPlan, format: str) -> bool:
        """Validate if export format is available for plan."""
        limits = PlanLimits.get_limits(plan)
        return format.lower() in limits.get("export_formats", [])


class CreateUsageLogUseCase:
    """Use case for creating usage log entries."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
        session_repo: SessionRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            user_repo: User repository port
            usage_log_repo: Usage log repository port
            session_repo: Session repository port
        """
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo
        self.session_repo = session_repo

    def execute(
        self,
        session: SessionModel,
        transcription_type: TranscriptionType = TranscriptionType.ORIGINAL,
        cost_usd: Optional[float] = None,
        is_billable: bool = True,
        billing_reason: str = "transcription_completed",
    ) -> UsageLog:
        """Create comprehensive usage log entry.

        Args:
            session: Session entity
            transcription_type: Type of transcription operation
            cost_usd: Optional explicit cost
            is_billable: Whether this usage should be billed
            billing_reason: Reason for billing

        Returns:
            Created usage log entity

        Raises:
            ValueError: If user not found or invalid session
            RuntimeError: If repository operations fail
        """
        logger.info(
            f"📊 Creating usage log for session {session.id}, type: {transcription_type.value}"
        )

        # Get user - this is a business rule, user must exist
        user = self.user_repo.get_by_id(session.user_id)
        if not user:
            raise ValueError(f"User not found: {session.user_id}")

        # Find parent log for retries/re-transcriptions
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            existing_logs = self.usage_log_repo.get_by_session_id(session.id)
            if existing_logs:
                # Get the first (original) log as parent
                parent_log = min(existing_logs, key=lambda log: log.created_at)

        # Calculate cost if not provided - this is business logic
        calculated_cost = self._calculate_cost(session, cost_usd, is_billable)

        # Create usage log with comprehensive data
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, "client_id", None),
            duration_minutes=(
                int(session.duration_seconds / 60) if session.duration_seconds else 0
            ),
            duration_seconds=session.duration_seconds or 0,
            cost_usd=calculated_cost,
            stt_provider=session.stt_provider,
            transcription_type=transcription_type,
            is_billable=is_billable,
            billing_reason=billing_reason,
            parent_log_id=parent_log.id if parent_log else None,
            user_plan=user.plan.value,
            plan_limits=PlanLimits.get_limits(user.plan),
            language=session.language,
            enable_diarization=True,  # Default from session config
            original_filename=session.audio_filename,
            transcription_started_at=session.updated_at,
            transcription_completed_at=datetime.now(timezone.utc),
            provider_metadata=session.provider_metadata or {},
        )

        # Save usage log
        saved_log = self.usage_log_repo.save(usage_log)

        # Update user usage counters (only for billable)
        if is_billable:
            self._update_user_usage_counters(user, saved_log)

        logger.info(
            f"✅ Usage log created: {saved_log.id}, billable: {is_billable}, cost: ${calculated_cost:.4f}"
        )

        return saved_log

    def _calculate_cost(
        self,
        session: SessionModel,
        cost_usd: Optional[float],
        is_billable: bool,
    ) -> Decimal:
        """Calculate cost for the session - pure business logic.

        Args:
            session: Session entity
            cost_usd: Explicit cost override
            is_billable: Whether this should be billed

        Returns:
            Calculated cost as Decimal
        """
        if not is_billable:
            return Decimal("0")

        if cost_usd is not None:
            return Decimal(str(cost_usd))

        if not session.duration_seconds:
            return Decimal("0")

        # Basic cost calculation - this is business logic
        # Google STT: ~$0.016 per minute, AssemblyAI: ~$0.01 per minute
        rate_per_minute = 0.016 if session.stt_provider == "google" else 0.01
        duration_minutes = session.duration_seconds / 60.0
        calculated_cost = duration_minutes * rate_per_minute

        return Decimal(str(calculated_cost))

    def _update_user_usage_counters(self, user: User, usage_log: UsageLog) -> None:
        """Update user's monthly usage counters with monthly reset logic.

        Args:
            user: User entity to update
            usage_log: Usage log with billing information
        """
        logger.debug(f"📈 Updating usage counters for user {user.id}")

        # Check if we need to reset monthly usage - business rule
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if (
            not user.current_month_start
            or user.current_month_start.replace(tzinfo=timezone.utc) < current_month
        ):
            logger.info(f"🔄 Resetting monthly usage for user {user.id}")
            user.usage_minutes = 0
            user.session_count = 0
            user.transcription_count = 0
            user.current_month_start = current_month

        # Update current month counters
        user.usage_minutes += usage_log.duration_minutes
        user.transcription_count += 1

        # Update cumulative counters
        user.total_transcriptions_generated += 1
        user.total_minutes_processed = Decimal(
            str(user.total_minutes_processed or 0)
        ) + Decimal(str(usage_log.duration_minutes))
        user.total_cost_usd = Decimal(str(user.total_cost_usd or 0)) + (
            usage_log.cost_usd or Decimal("0")
        )

        # Save updated user
        self.user_repo.save(user)


class GetUserUsageUseCase:
    """Use case for retrieving user usage information."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            user_repo: User repository port
            usage_log_repo: Usage log repository port
        """
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo

    def get_current_month_usage(self, user_id: UUID) -> Dict[str, Any]:
        """Get current month usage summary for user.

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary containing current month usage data

        Raises:
            ValueError: If user not found
            RuntimeError: If repository operations fail
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Calculate current month boundaries
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (
            month_start.replace(month=month_start.month + 1)
            if month_start.month < 12
            else month_start.replace(year=month_start.year + 1, month=1)
        )

        # Get usage summary from repository
        usage_summary = self.usage_log_repo.get_usage_summary(
            user_id, month_start, next_month
        )

        # Get plan limits
        plan_limits = PlanLimits.get_limits(user.plan)

        return {
            "user_id": str(user_id),
            "plan": user.plan.value,
            "current_month_start": month_start.isoformat(),
            "usage_summary": usage_summary,
            "plan_limits": plan_limits,
            "user_counters": {
                "usage_minutes": user.usage_minutes,
                "transcription_count": user.transcription_count,
                "session_count": user.session_count,
            },
            "totals": {
                "total_transcriptions": user.total_transcriptions_generated,
                "total_minutes": float(user.total_minutes_processed or 0),
                "total_cost_usd": float(user.total_cost_usd or 0),
            },
        }


class GetUsageHistoryUseCase:
    """Use case for retrieving user usage history across multiple months."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            user_repo: User repository port
            usage_log_repo: Usage log repository port
        """
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo

    def execute(self, user_id: UUID, months: int = 3) -> Dict[str, Any]:
        """Get usage history for specified number of months.

        Args:
            user_id: UUID of the user
            months: Number of months to retrieve (1-12)

        Returns:
            Dictionary containing usage history data

        Raises:
            ValueError: If user not found or invalid months parameter
        """
        if months < 1 or months > 12:
            raise ValueError("Months must be between 1 and 12")

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Get usage history from repository
        usage_history = self.usage_log_repo.get_user_usage_history(user_id, months)

        return {
            "user_id": str(user_id),
            "plan": user.plan.value,
            "months_requested": months,
            "usage_history": usage_history,
            "plan_limits": PlanLimits.get_limits(user.plan),
        }


class GetUserAnalyticsUseCase:
    """Use case for retrieving comprehensive user analytics."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
        usage_analytics_repo: "UsageAnalyticsRepoPort",
    ):
        """Initialize use case with repository dependencies.

        Args:
            user_repo: User repository port
            usage_log_repo: Usage log repository port
            usage_analytics_repo: Usage analytics repository port
        """
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo
        self.usage_analytics_repo = usage_analytics_repo

    def execute(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive analytics for user.

        Args:
            user_id: UUID of the user

        Returns:
            Dictionary containing user analytics data

        Raises:
            ValueError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Get analytics data from repository
        analytics_data = self.usage_analytics_repo.get_by_user(user_id)

        return {
            "user_id": str(user_id),
            "plan": user.plan.value,
            "analytics": analytics_data,
        }


class GetAdminAnalyticsUseCase:
    """Use case for retrieving admin analytics across all users."""

    def __init__(
        self,
        usage_analytics_repo: "UsageAnalyticsRepoPort",
    ):
        """Initialize use case with repository dependencies.

        Args:
            usage_analytics_repo: Usage analytics repository port
        """
        self.usage_analytics_repo = usage_analytics_repo

    def execute(self) -> Dict[str, Any]:
        """Get system-wide analytics for admin users.

        Returns:
            Dictionary containing admin analytics data
        """
        # Get admin analytics from repository
        admin_analytics = self.usage_analytics_repo.get_admin_analytics()

        return admin_analytics


class GetSpecificUserUsageUseCase:
    """Use case for retrieving usage summary for any specific user (Admin only)."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            user_repo: User repository port
            usage_log_repo: Usage log repository port
        """
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo

    def execute(self, user_id: UUID) -> Dict[str, Any]:
        """Get usage summary for any specific user (Admin access).

        Args:
            user_id: UUID of the user to get usage for

        Returns:
            Dictionary containing user usage summary data

        Raises:
            ValueError: If user not found
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Calculate current month boundaries
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (
            month_start.replace(month=month_start.month + 1)
            if month_start.month < 12
            else month_start.replace(year=month_start.year + 1, month=1)
        )

        # Get usage summary from repository - same logic as regular user
        usage_summary = self.usage_log_repo.get_usage_summary(
            user_id, month_start, next_month
        )

        # Get plan limits
        plan_limits = PlanLimits.get_limits(user.plan)

        return {
            "user_id": str(user_id),
            "user_email": getattr(user, "email", None),  # Include email for admin view
            "plan": user.plan.value,
            "current_month_start": month_start.isoformat(),
            "usage_summary": usage_summary,
            "plan_limits": plan_limits,
            "user_counters": {
                "usage_minutes": user.usage_minutes,
                "transcription_count": user.transcription_count,
                "session_count": user.session_count,
            },
            "totals": {
                "total_transcriptions": user.total_transcriptions_generated,
                "total_minutes": float(user.total_minutes_processed or 0),
                "total_cost_usd": float(user.total_cost_usd or 0),
            },
        }


class GetMonthlyUsageReportUseCase:
    """Use case for retrieving detailed monthly usage reports (Admin only)."""

    def __init__(
        self,
        usage_analytics_repo: "UsageAnalyticsRepoPort",
    ):
        """Initialize use case with repository dependencies.

        Args:
            usage_analytics_repo: Usage analytics repository port
        """
        self.usage_analytics_repo = usage_analytics_repo

    def execute(self, month_year: str) -> Dict[str, Any]:
        """Get detailed monthly usage report for all users.

        Args:
            month_year: Month in YYYY-MM format

        Returns:
            Dictionary containing monthly report data

        Raises:
            ValueError: If month format is invalid
        """
        # Validate month format
        try:
            datetime.strptime(month_year, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid month format. Use YYYY-MM")

        # Get all analytics for the month
        monthly_analytics = self.usage_analytics_repo.get_by_month_year(month_year)

        if not monthly_analytics:
            return {
                "month_year": month_year,
                "message": "No data available for this month",
                "total_users": 0,
                "summary": {},
            }

        # Aggregate data
        total_users = len(monthly_analytics)
        total_transcriptions = sum(
            analytics.transcriptions_completed for analytics in monthly_analytics
        )
        total_minutes = sum(
            float(analytics.total_minutes_processed) for analytics in monthly_analytics
        )
        total_cost = sum(
            float(analytics.total_cost_usd) for analytics in monthly_analytics
        )

        # Plan breakdown
        plan_breakdown = {}
        for analytics in monthly_analytics:
            plan = analytics.primary_plan
            if plan not in plan_breakdown:
                plan_breakdown[plan] = {
                    "users": 0,
                    "transcriptions": 0,
                    "minutes": 0.0,
                    "cost": 0.0,
                }
            plan_breakdown[plan]["users"] += 1
            plan_breakdown[plan]["transcriptions"] += analytics.transcriptions_completed
            plan_breakdown[plan]["minutes"] += float(analytics.total_minutes_processed)
            plan_breakdown[plan]["cost"] += float(analytics.total_cost_usd)

        # Provider breakdown
        total_google_minutes = sum(
            float(analytics.google_stt_minutes) for analytics in monthly_analytics
        )
        total_assemblyai_minutes = sum(
            float(analytics.assemblyai_minutes) for analytics in monthly_analytics
        )

        return {
            "month_year": month_year,
            "total_users": total_users,
            "summary": {
                "total_transcriptions": total_transcriptions,
                "total_minutes": total_minutes,
                "total_hours": total_minutes / 60,
                "total_cost_usd": total_cost,
                "avg_minutes_per_user": (
                    total_minutes / total_users if total_users > 0 else 0
                ),
                "avg_cost_per_user": (
                    total_cost / total_users if total_users > 0 else 0
                ),
            },
            "plan_breakdown": plan_breakdown,
            "provider_breakdown": {
                "google": {
                    "minutes": total_google_minutes,
                    "percentage": (
                        (total_google_minutes / total_minutes * 100)
                        if total_minutes > 0
                        else 0
                    ),
                },
                "assemblyai": {
                    "minutes": total_assemblyai_minutes,
                    "percentage": (
                        (total_assemblyai_minutes / total_minutes * 100)
                        if total_minutes > 0
                        else 0
                    ),
                },
            },
            "period": {
                "start": f"{month_year}-01",
                "end": (
                    monthly_analytics[0].period_end.isoformat()
                    if monthly_analytics[0].period_end
                    else None
                ),
            },
        }


class GetUsageTrendsUseCase:
    """Use case for getting usage trends and patterns over time."""

    def __init__(
        self,
        usage_analytics_repo: UsageAnalyticsRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        self.usage_analytics_repo = usage_analytics_repo
        self.usage_log_repo = usage_log_repo

    def execute(
        self, user_id: UUID, period: str, group_by: str
    ) -> List[Dict[str, Any]]:
        """
        Get usage trends data for visualization.

        Args:
            user_id: User identifier
            period: Time period (7d, 30d, 3m, 12m)
            group_by: Grouping level (day, week, month)
        """
        logger.info(f"Getting usage trends for user {user_id}, period: {period}")

        # Calculate date range based on period
        end_date = datetime.now(timezone.utc)
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "3m":
            start_date = end_date - timedelta(days=90)
        elif period == "12m":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        # Generate trend data points
        trends = []
        current_date = start_date

        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            # Get usage logs for this date
            daily_logs = self.usage_log_repo.get_by_user_and_date_range(
                user_id, current_date, next_date
            )

            daily_sessions = len(set(log.session_id for log in daily_logs))
            daily_minutes = sum(log.duration_minutes or 0 for log in daily_logs)
            daily_transcriptions = len(
                [log for log in daily_logs if log.transcription_type]
            )
            daily_exports = len(
                [log for log in daily_logs if "export" in str(log.action).lower()]
            )
            daily_cost = sum(log.cost_usd or Decimal("0") for log in daily_logs)

            trends.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sessions": daily_sessions,
                    "minutes": float(daily_minutes),
                    "hours": float(daily_minutes / 60),
                    "transcriptions": daily_transcriptions,
                    "exports": daily_exports,
                    "cost": float(daily_cost),
                    "utilization": min(float(daily_minutes / 60), 100.0),
                    "success_rate": 100.0 if daily_sessions > 0 else 0.0,
                    "avg_duration": (
                        float(daily_minutes / daily_sessions)
                        if daily_sessions > 0
                        else 0.0
                    ),
                }
            )

            current_date = next_date

        logger.info(f"Generated {len(trends)} trend data points for user {user_id}")
        return trends


class GetUsagePredictionsUseCase:
    """Use case for generating usage predictions based on historical patterns."""

    def __init__(
        self,
        usage_analytics_repo: UsageAnalyticsRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        self.usage_analytics_repo = usage_analytics_repo
        self.usage_log_repo = usage_log_repo

    def execute(self, user_id: UUID) -> Dict[str, Any]:
        """
        Generate usage predictions for the next period.

        Args:
            user_id: User identifier
        """
        logger.info(f"Generating usage predictions for user {user_id}")

        # Get historical data for the last 30 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        historical_logs = self.usage_log_repo.get_by_user_and_date_range(
            user_id, start_date, end_date
        )

        if not historical_logs:
            return {
                "predicted_sessions": 0,
                "predicted_minutes": 0,
                "estimated_limit_date": None,
                "confidence": 0.0,
                "recommendation": ("No historical data available for predictions"),
                "growth_rate": 0.0,
                "current_trend": "unknown",
            }

        # Calculate daily averages
        total_sessions = len(set(log.session_id for log in historical_logs))
        total_minutes = sum(log.duration_minutes or 0 for log in historical_logs)

        avg_sessions_per_day = total_sessions / 30
        avg_minutes_per_day = total_minutes / 30

        # Simple linear projection for next 30 days
        predicted_sessions = int(avg_sessions_per_day * 30)
        predicted_minutes = int(avg_minutes_per_day * 30)

        # Calculate growth rate (comparing first 15 days vs last 15 days)
        mid_date = start_date + timedelta(days=15)
        first_half = [log for log in historical_logs if log.created_at < mid_date]
        second_half = [log for log in historical_logs if log.created_at >= mid_date]

        first_half_minutes = sum(log.duration_minutes or 0 for log in first_half)
        second_half_minutes = sum(log.duration_minutes or 0 for log in second_half)

        growth_rate = 0.0
        if first_half_minutes > 0:
            growth_rate = (
                (second_half_minutes - first_half_minutes) / first_half_minutes
            ) * 100

        # Determine trend
        if growth_rate > 10:
            current_trend = "increasing"
            confidence = 0.75
        elif growth_rate < -10:
            current_trend = "decreasing"
            confidence = 0.75
        else:
            current_trend = "stable"
            confidence = 0.6

        # Generate recommendation
        if predicted_minutes > 1000:  # > ~16 hours
            recommendation = "Consider upgrading to Pro plan for better limits"
        elif predicted_minutes < 60:  # < 1 hour
            recommendation = "Current usage is low, Free plan should be sufficient"
        else:
            recommendation = "Current usage pattern looks sustainable"

        # Estimate when limits might be reached (assuming Free plan limit of
        # 120 minutes)
        estimated_limit_date = None
        if avg_minutes_per_day > 0:
            days_to_limit = 120 / avg_minutes_per_day
            if days_to_limit <= 30:
                estimated_limit_date = (
                    datetime.now() + timedelta(days=int(days_to_limit))
                ).strftime("%Y-%m-%d")

        return {
            "predicted_sessions": predicted_sessions,
            "predicted_minutes": predicted_minutes,
            "estimated_limit_date": estimated_limit_date,
            "confidence": confidence,
            "recommendation": recommendation,
            "growth_rate": growth_rate,
            "current_trend": current_trend,
        }


class GetUsageInsightsUseCase:
    """Use case for generating personalized usage insights and recommendations."""

    def __init__(
        self,
        usage_analytics_repo: UsageAnalyticsRepoPort,
        usage_log_repo: UsageLogRepoPort,
        user_repo: UserRepoPort,
    ):
        self.usage_analytics_repo = usage_analytics_repo
        self.usage_log_repo = usage_log_repo
        self.user_repo = user_repo

    def execute(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Generate personalized usage insights.

        Args:
            user_id: User identifier
        """
        logger.info(f"Generating usage insights for user {user_id}")

        insights = []

        # Get user and recent usage data
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return insights

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        recent_logs = self.usage_log_repo.get_by_user_and_date_range(
            user_id, start_date, end_date
        )

        if not recent_logs:
            insights.append(
                {
                    "type": "pattern",
                    "title": "Getting Started",
                    "message": "No recent usage detected",
                    "suggestion": (
                        "Try uploading your first coaching session recording"
                    ),
                    "priority": "medium",
                    "action": None,
                }
            )
            return insights

        # Analyze usage patterns
        total_minutes = sum(log.duration_minutes or 0 for log in recent_logs)
        total_sessions = len(set(log.session_id for log in recent_logs))

        # Plan usage insight
        plan_limits = PlanLimits.get_limits(user.plan)
        monthly_limit = plan_limits["minutes_per_month"]
        utilization = (total_minutes / monthly_limit) * 100 if monthly_limit > 0 else 0

        if utilization > 90:
            insights.append(
                {
                    "type": "warning",
                    "title": "Plan Limit Approaching",
                    "message": (
                        f"You've used {utilization:.1f}% of your monthly limit"
                    ),
                    "suggestion": ("Consider upgrading to Pro plan for higher limits"),
                    "priority": "high",
                    "action": "upgrade",
                }
            )
        elif utilization < 10:
            insights.append(
                {
                    "type": "optimization",
                    "title": "Low Usage Detected",
                    "message": (
                        f"You've only used {utilization:.1f}% of your plan limits"
                    ),
                    "suggestion": "You might be able to use a lower plan tier",
                    "priority": "low",
                    "action": "downgrade",
                }
            )

        # Usage efficiency insight
        if total_sessions > 0:
            avg_duration = total_minutes / total_sessions
            if avg_duration > 120:  # > 2 hours per session
                insights.append(
                    {
                        "type": "optimization",
                        "title": "Long Session Duration",
                        "message": (
                            f"Average session duration: {avg_duration:.1f} minutes"
                        ),
                        "suggestion": (
                            "Consider breaking longer sessions into smaller chunks for better processing"
                        ),
                        "priority": "medium",
                        "action": None,
                    }
                )
            elif avg_duration < 15:  # < 15 minutes per session
                insights.append(
                    {
                        "type": "pattern",
                        "title": "Short Sessions",
                        "message": (
                            f"Average session duration: {avg_duration:.1f} minutes"
                        ),
                        "suggestion": ("Short sessions are processed efficiently"),
                        "priority": "low",
                        "action": None,
                    }
                )

        # Cost analysis insight
        total_cost = sum(log.cost_usd or Decimal("0") for log in recent_logs)
        if total_cost > 0:
            cost_per_minute = (
                float(total_cost / total_minutes) if total_minutes > 0 else 0
            )
            insights.append(
                {
                    "type": "cost",
                    "title": "Cost Efficiency",
                    "message": (f"Current cost: ${cost_per_minute:.4f} per minute"),
                    "suggestion": ("Cost tracking is active for your transcriptions"),
                    "priority": "low",
                    "action": None,
                }
            )

        # Activity pattern insight
        # Group by day of week to find patterns
        weekday_usage = {}
        for log in recent_logs:
            weekday = log.created_at.strftime("%A")
            weekday_usage[weekday] = weekday_usage.get(weekday, 0) + (
                log.duration_minutes or 0
            )

        if weekday_usage:
            most_active_day = max(weekday_usage, key=weekday_usage.get)
            insights.append(
                {
                    "type": "pattern",
                    "title": "Usage Pattern",
                    "message": f"Most active day: {most_active_day}",
                    "suggestion": ("Consistent usage patterns help with planning"),
                    "priority": "low",
                    "action": None,
                }
            )

        logger.info(f"Generated {len(insights)} insights for user {user_id}")
        return insights


class CreateUsageSnapshotUseCase:
    """Use case for creating manual usage snapshots."""

    def __init__(
        self,
        usage_log_repo: UsageLogRepoPort,
        usage_history_repo: "UsageHistoryRepoPort",
    ):
        self.usage_log_repo = usage_log_repo
        self.usage_history_repo = usage_history_repo

    def execute(self, user_id: UUID, period_type: str) -> "UsageHistory":
        """
        Create a usage snapshot for the specified period.

        Args:
            user_id: User identifier
            period_type: Type of period (hourly, daily, monthly)
        """
        logger.info(
            f"Creating usage snapshot for user {user_id}, period: {period_type}"
        )

        # Calculate period boundaries
        now = datetime.now(timezone.utc)

        if period_type == "hourly":
            period_start = now.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)
        elif period_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                period_end = period_start.replace(year=now.year + 1, month=1)
            else:
                period_end = period_start.replace(month=now.month + 1)
        else:
            raise ValueError(f"Invalid period_type: {period_type}")

        # Get usage data for the period
        usage_logs = self.usage_log_repo.get_by_user_and_date_range(
            user_id, period_start, period_end
        )

        # Aggregate metrics
        total_sessions = len(set(log.session_id for log in usage_logs))
        total_minutes = sum(log.duration_minutes or 0 for log in usage_logs)
        total_transcriptions = len(
            [log for log in usage_logs if log.transcription_type]
        )
        total_exports = len(
            [log for log in usage_logs if "export" in str(log.action).lower()]
        )
        total_cost = sum(log.cost_usd or Decimal("0") for log in usage_logs)

        # Create snapshot data
        usage_metrics = {
            "sessions": total_sessions,
            "minutes": float(total_minutes),
            "transcriptions": total_transcriptions,
            "exports": total_exports,
        }

        plan_context = {
            "plan_type": "free",  # TODO: Get actual plan from user
            "limits": {"monthly_minutes": 120, "monthly_sessions": 10},
        }

        cost_metrics = {
            "total_cost": float(total_cost),
            "cost_per_minute": (
                float(total_cost / total_minutes) if total_minutes > 0 else 0
            ),
        }

        provider_breakdown = {
            "google": {"minutes": float(total_minutes * 0.6)},  # Estimate
            "assemblyai": {"minutes": float(total_minutes * 0.4)},  # Estimate
        }

        export_activity = {
            "total_exports": total_exports,
            "formats_used": ["json", "txt"],  # Default formats
        }

        performance_metrics = {
            "avg_processing_time": 30.0,  # Estimate
            "success_rate": 100.0,
        }

        # Create UsageHistory domain object
        from ..models.usage_history import UsageHistory

        usage_history = UsageHistory(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            usage_metrics=usage_metrics,
            plan_context=plan_context,
            cost_metrics=cost_metrics,
            provider_breakdown=provider_breakdown,
            export_activity=export_activity,
            performance_metrics=performance_metrics,
        )

        # Save and return
        saved_history = self.usage_history_repo.save(usage_history)
        logger.info(f"Created usage snapshot {saved_history.id} for user {user_id}")

        return saved_history


class ExportUsageDataUseCase:
    """Use case for exporting usage data in various formats."""

    def __init__(
        self,
        usage_analytics_repo: UsageAnalyticsRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        self.usage_analytics_repo = usage_analytics_repo
        self.usage_log_repo = usage_log_repo

    def execute(self, user_id: UUID, format: str, period: str) -> Dict[str, Any]:
        """
        Export usage data in the specified format.

        Args:
            user_id: User identifier
            format: Export format (json, xlsx, txt)
            period: Time period to export
        """
        logger.info(
            f"Exporting usage data for user {user_id}, format: {format}, period: {period}"
        )

        # Get trends data (reuse logic from trends use case)
        trends_use_case = GetUsageTrendsUseCase(
            self.usage_analytics_repo, self.usage_log_repo
        )

        trends_data = trends_use_case.execute(user_id, period, "day")

        filename_base = f"usage_history_{period}_{user_id}"

        if format.lower() == "json":
            return {
                "format": "json",
                "period": period,
                "data": trends_data,
                "filename": f"{filename_base}.json",
            }
        elif format.lower() == "xlsx":
            # Return Excel export structure (actual Excel generation handled in
            # API layer)
            return {
                "format": "xlsx",
                "period": period,
                "data": trends_data,
                "filename": f"{filename_base}.xlsx",
            }
        elif format.lower() == "txt":
            # Generate text format
            lines = []
            lines.append(f"Usage History Report - Period: {period}")
            lines.append("=" * 50)
            lines.append("")

            for item in trends_data:
                lines.append(f"Date: {item.get('date', 'N/A')}")
                lines.append(f"Sessions: {item.get('sessions', 0)}")
                lines.append(f"Minutes Processed: {item.get('minutes', 0):.1f}")
                lines.append(f"Transcriptions: {item.get('transcriptions', 0)}")
                lines.append(f"Exports Generated: {item.get('exports', 0)}")
                lines.append(f"Cost (USD): ${item.get('cost', 0.0):.2f}")
                lines.append("-" * 30)

            txt_data = "\n".join(lines)

            return {
                "format": "txt",
                "period": period,
                "data": txt_data,
                "filename": f"{filename_base}.txt",
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Generated export data for user {user_id} in {format} format")
