"""Usage tracking use case following Clean Architecture principles.

This module contains the business logic for usage tracking without
any infrastructure dependencies. It operates only through repository
ports and domain models.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
import logging

from ..repositories.ports import (
    UserRepoPort,
    UsageLogRepoPort,
    SessionRepoPort,
    UsageAnalyticsRepoPort,
)
from ..models.user import User, UserPlan
from ..models.session import Session as SessionModel, SessionStatus
from ..models.usage_log import UsageLog, TranscriptionType

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
                int(session.duration_seconds / 60)
                if session.duration_seconds
                else 0
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
        self, session: SessionModel, cost_usd: Optional[float], is_billable: bool
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
        next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
        
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
        usage_analytics_repo: 'UsageAnalyticsRepoPort',
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
        usage_analytics_repo: 'UsageAnalyticsRepoPort',
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