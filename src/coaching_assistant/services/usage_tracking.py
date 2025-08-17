"""Usage tracking service for comprehensive usage analytics."""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_, func
import logging

from ..models.user import User, UserPlan
from ..models.session import Session as SessionModel
from ..models.usage_log import UsageLog, TranscriptionType
from ..models.usage_analytics import UsageAnalytics

logger = logging.getLogger(__name__)


class PlanLimits:
    """Plan limit configuration."""
    
    @staticmethod
    def get_limits(plan: UserPlan) -> dict:
        """Get plan limits as dictionary."""
        limits = {
            UserPlan.FREE: {
                "minutes_per_month": 120,  # 2 hours
                "sessions_per_month": 10,
                "max_file_size_mb": 50,
                "export_formats": ["json", "txt"],
                "features": ["basic_transcription"]
            },
            UserPlan.PRO: {
                "minutes_per_month": 1200,  # 20 hours
                "sessions_per_month": 100,
                "max_file_size_mb": 200,
                "export_formats": ["json", "txt", "vtt", "srt"],
                "features": ["basic_transcription", "speaker_diarization", "export_formats"]
            },
            UserPlan.ENTERPRISE: {
                "minutes_per_month": float("inf"),
                "sessions_per_month": float("inf"),
                "max_file_size_mb": 500,
                "export_formats": ["json", "txt", "vtt", "srt", "xlsx"],
                "features": ["basic_transcription", "speaker_diarization", "export_formats", "api_access", "priority_support"]
            }
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


class UsageTrackingService:
    """Comprehensive usage tracking and analytics service."""
    
    def __init__(self, db: DBSession):
        self.db = db
    
    def create_usage_log(
        self,
        session: SessionModel,
        transcription_type: TranscriptionType = TranscriptionType.ORIGINAL,
        cost_usd: Optional[float] = None,
        is_billable: bool = True,
        billing_reason: str = "transcription_completed"
    ) -> UsageLog:
        """Create comprehensive usage log entry."""
        
        logger.info(f"📊 Creating usage log for session {session.id}, type: {transcription_type.value}")
        
        user = self.db.query(User).filter(User.id == session.user_id).first()
        if not user:
            raise ValueError(f"User not found: {session.user_id}")
        
        # Find parent log for retries/re-transcriptions
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            parent_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).order_by(UsageLog.created_at.asc()).first()
        
        # Calculate cost if not provided
        if cost_usd is None and is_billable:
            # Basic cost calculation (can be enhanced later)
            # Google STT: ~$0.016 per minute, AssemblyAI: ~$0.01 per minute
            rate_per_minute = 0.016 if session.stt_provider == 'google' else 0.01
            cost_usd = (session.duration_seconds / 60.0) * rate_per_minute if session.duration_seconds else 0.0
        
        # Create usage log with comprehensive data
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, 'client_id', None),
            
            duration_minutes=int(session.duration_seconds / 60) if session.duration_seconds else 0,
            duration_seconds=session.duration_seconds or 0,
            cost_usd=Decimal(str(cost_usd)) if is_billable and cost_usd else Decimal('0'),
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
            
            provider_metadata=session.provider_metadata or {}
        )
        
        self.db.add(usage_log)
        self.db.flush()
        
        # Update user usage counters (only for billable)
        if is_billable:
            self._update_user_usage_counters(user, usage_log)
        
        # Update monthly analytics
        self._update_monthly_analytics(user.id, usage_log)
        
        self.db.commit()
        
        logger.info(f"✅ Usage log created: {usage_log.id}, billable: {is_billable}, cost: ${cost_usd:.4f}")
        
        return usage_log
    
    def _update_user_usage_counters(self, user: User, usage_log: UsageLog):
        """Update user's monthly usage counters with monthly reset logic."""
        
        logger.debug(f"📈 Updating usage counters for user {user.id}")
        
        # Check if we need to reset monthly usage
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not user.current_month_start or user.current_month_start.replace(tzinfo=timezone.utc) < current_month:
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
        user.total_minutes_processed = Decimal(str(user.total_minutes_processed or 0)) + Decimal(str(usage_log.duration_minutes))
        user.total_cost_usd = Decimal(str(user.total_cost_usd or 0)) + (usage_log.cost_usd or Decimal('0'))
        
        self.db.flush()
        
        logger.debug(f"✅ User counters updated: usage_minutes={user.usage_minutes}, total_transcriptions={user.total_transcriptions_generated}")
    
    def increment_session_count(self, user: User):
        """Increment session count with monthly reset check."""
        
        logger.debug(f"📈 Incrementing session count for user {user.id}")
        
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not user.current_month_start or user.current_month_start.replace(tzinfo=timezone.utc) < current_month:
            logger.info(f"🔄 Resetting monthly session count for user {user.id}")
            user.session_count = 0
            user.usage_minutes = 0
            user.transcription_count = 0
            user.current_month_start = current_month
        
        user.session_count += 1
        user.total_sessions_created += 1
        self.db.flush()
        
        logger.debug(f"✅ Session count updated: session_count={user.session_count}, total_sessions={user.total_sessions_created}")
    
    def _update_monthly_analytics(self, user_id: str, usage_log: UsageLog):
        """Update or create monthly analytics record."""
        
        month_year = usage_log.created_at.strftime('%Y-%m')
        logger.debug(f"📊 Updating monthly analytics for user {user_id}, month: {month_year}")
        
        analytics = self.db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.user_id == user_id,
                UsageAnalytics.month_year == month_year
            )
        ).first()
        
        if not analytics:
            # Create new monthly analytics record
            logger.info(f"📝 Creating new monthly analytics record for {month_year}")
            analytics = UsageAnalytics(
                user_id=user_id,
                month_year=month_year,
                primary_plan=usage_log.user_plan,
                period_start=usage_log.created_at.replace(day=1, hour=0, minute=0, second=0),
                period_end=self._get_month_end(usage_log.created_at)
            )
            self.db.add(analytics)
        
        # Update metrics based on transcription type
        if usage_log.transcription_type == TranscriptionType.ORIGINAL:
            analytics.original_transcriptions = (analytics.original_transcriptions or 0) + 1
        elif usage_log.transcription_type == TranscriptionType.RETRY_FAILED:
            analytics.free_retries = (analytics.free_retries or 0) + 1
        elif usage_log.transcription_type == TranscriptionType.RETRY_SUCCESS:
            analytics.paid_retranscriptions = (analytics.paid_retranscriptions or 0) + 1
        
        analytics.transcriptions_completed = (analytics.transcriptions_completed or 0) + 1
        analytics.total_minutes_processed = Decimal(str(analytics.total_minutes_processed or 0)) + Decimal(str(usage_log.duration_minutes))
        analytics.total_cost_usd = Decimal(str(analytics.total_cost_usd or 0)) + (usage_log.cost_usd or Decimal('0'))
        
        # Update provider breakdown
        if usage_log.stt_provider == 'google':
            analytics.google_stt_minutes = Decimal(str(analytics.google_stt_minutes or 0)) + Decimal(str(usage_log.duration_minutes))
        elif usage_log.stt_provider == 'assemblyai':
            analytics.assemblyai_minutes = Decimal(str(analytics.assemblyai_minutes or 0)) + Decimal(str(usage_log.duration_minutes))
        
        analytics.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        
        logger.debug(f"✅ Monthly analytics updated: transcriptions={analytics.transcriptions_completed}, minutes={analytics.total_minutes_processed}")
    
    def get_user_usage_summary(self, user_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get comprehensive usage summary for user."""
        
        logger.info(f"📊 Getting usage summary for user {user_id}")
        
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Get recent usage logs
        recent_logs = self.db.query(UsageLog).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            )
        ).order_by(UsageLog.created_at.desc()).limit(10).all()
        
        # Get monthly analytics
        monthly_analytics = self.db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.user_id == user_id,
                UsageAnalytics.period_start >= datetime.now(timezone.utc) - timedelta(days=365)
            )
        ).order_by(UsageAnalytics.period_start.desc()).all()
        
        return {
            "user_id": str(user.id),
            "plan": user.plan.value,
            "plan_limits": PlanLimits.get_limits(user.plan),
            "current_month": {
                "usage_minutes": user.usage_minutes,
                "session_count": user.session_count,
                "transcription_count": user.transcription_count,
                "month_start": user.current_month_start.isoformat() if user.current_month_start else None
            },
            "lifetime_totals": {
                "sessions_created": user.total_sessions_created,
                "transcriptions_generated": user.total_transcriptions_generated,
                "minutes_processed": float(user.total_minutes_processed),
                "cost_usd": float(user.total_cost_usd)
            },
            "recent_activity": [
                {
                    "id": str(log.id),
                    "session_id": str(log.session_id),
                    "transcription_type": log.transcription_type.value,
                    "duration_minutes": log.duration_minutes,
                    "cost_usd": float(log.cost_usd) if log.cost_usd else 0.0,
                    "is_billable": log.is_billable,
                    "stt_provider": log.stt_provider,
                    "created_at": log.created_at.isoformat()
                }
                for log in recent_logs
            ],
            "monthly_trends": [
                {
                    "month_year": analytics.month_year,
                    "transcriptions": analytics.transcriptions_completed,
                    "minutes": float(analytics.total_minutes_processed),
                    "cost": float(analytics.total_cost_usd),
                    "plan": analytics.primary_plan
                }
                for analytics in monthly_analytics
            ]
        }
    
    def get_admin_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        plan_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get system-wide analytics for admins."""
        
        logger.info(f"📊 Getting admin analytics from {start_date} to {end_date}")
        
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=90)  # Default 3 months
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Build query
        query = self.db.query(UsageLog).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        )
        
        if plan_filter:
            query = query.filter(UsageLog.user_plan == plan_filter)
        
        usage_logs = query.all()
        
        # Calculate aggregate metrics
        total_transcriptions = len(usage_logs)
        total_minutes = sum(log.duration_minutes for log in usage_logs)
        total_cost = sum(float(log.cost_usd) for log in usage_logs if log.cost_usd)
        billable_transcriptions = len([log for log in usage_logs if log.is_billable])
        
        # Plan distribution
        plan_stats = {}
        for log in usage_logs:
            plan = log.user_plan
            if plan not in plan_stats:
                plan_stats[plan] = {"count": 0, "minutes": 0, "cost": 0.0}
            plan_stats[plan]["count"] += 1
            plan_stats[plan]["minutes"] += log.duration_minutes
            plan_stats[plan]["cost"] += float(log.cost_usd) if log.cost_usd else 0.0
        
        # Provider breakdown
        provider_stats = {}
        for log in usage_logs:
            provider = log.stt_provider
            if provider not in provider_stats:
                provider_stats[provider] = {"count": 0, "minutes": 0, "cost": 0.0}
            provider_stats[provider]["count"] += 1
            provider_stats[provider]["minutes"] += log.duration_minutes
            provider_stats[provider]["cost"] += float(log.cost_usd) if log.cost_usd else 0.0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_transcriptions": total_transcriptions,
                "total_minutes": total_minutes,
                "total_cost_usd": total_cost,
                "billable_transcriptions": billable_transcriptions,
                "avg_duration_minutes": total_minutes / total_transcriptions if total_transcriptions > 0 else 0,
                "avg_cost_per_transcription": total_cost / billable_transcriptions if billable_transcriptions > 0 else 0
            },
            "plan_distribution": plan_stats,
            "provider_breakdown": provider_stats,
            "unique_users": len(set(log.user_id for log in usage_logs)),
            "unique_sessions": len(set(log.session_id for log in usage_logs))
        }
    
    def get_user_usage_history(
        self,
        user_id: Union[str, UUID],
        months: int = 3
    ) -> Dict[str, Any]:
        """Get detailed usage history for a user."""
        
        logger.info(f"📊 Getting {months} months of usage history for user {user_id}")
        
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        
        usage_logs = self.db.query(UsageLog).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= start_date
            )
        ).order_by(UsageLog.created_at.desc()).all()
        
        return {
            "user_id": str(user_id) if not isinstance(user_id, str) else user_id,
            "months_requested": months,
            "start_date": start_date.isoformat(),
            "total_logs": len(usage_logs),
            "usage_history": [
                {
                    "id": str(log.id),
                    "session_id": str(log.session_id),
                    "transcription_type": log.transcription_type.value,
                    "duration_minutes": log.duration_minutes,
                    "cost_usd": float(log.cost_usd) if log.cost_usd else 0.0,
                    "is_billable": log.is_billable,
                    "billing_reason": log.billing_reason,
                    "stt_provider": log.stt_provider,
                    "user_plan": log.user_plan,
                    "language": log.language,
                    "created_at": log.created_at.isoformat()
                }
                for log in usage_logs
            ]
        }
    
    def get_user_analytics(self, user_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get user's usage analytics and trends."""
        
        logger.info(f"📊 Getting analytics for user {user_id}")
        
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Get monthly analytics for past 12 months
        start_date = datetime.now(timezone.utc) - timedelta(days=365)
        
        monthly_analytics = self.db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.user_id == user_id,
                UsageAnalytics.period_start >= start_date
            )
        ).order_by(UsageAnalytics.period_start.desc()).all()
        
        return {
            "user_id": str(user_id) if not isinstance(user_id, str) else user_id,
            "plan": user.plan.value,
            "analytics_period": "12_months",
            "monthly_data": [
                {
                    "month_year": analytics.month_year,
                    "plan": analytics.primary_plan,
                    "sessions_created": analytics.sessions_created,
                    "transcriptions_completed": analytics.transcriptions_completed,
                    "minutes_processed": float(analytics.total_minutes_processed),
                    "cost_usd": float(analytics.total_cost_usd),
                    "billing_breakdown": {
                        "original": analytics.original_transcriptions,
                        "free_retries": analytics.free_retries,
                        "paid_retranscriptions": analytics.paid_retranscriptions
                    },
                    "provider_breakdown": {
                        "google_minutes": float(analytics.google_stt_minutes),
                        "assemblyai_minutes": float(analytics.assemblyai_minutes)
                    },
                    "avg_duration_minutes": analytics.avg_session_duration_minutes,
                    "avg_cost_per_transcription": analytics.avg_cost_per_transcription
                }
                for analytics in monthly_analytics
            ]
        }
    
    def _get_month_end(self, date: datetime) -> datetime:
        """Get end of month for given date."""
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            return date.replace(month=date.month + 1, day=1) - timedelta(days=1)