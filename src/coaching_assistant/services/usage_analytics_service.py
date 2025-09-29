"""Usage Analytics Service for processing and generating usage insights."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..models.session import Session as TranscriptionSession
from ..models.usage_history import UsageHistory
from ..models.usage_log import TranscriptionType, UsageLog
from ..models.user import User
from ..services.plan_limits import get_global_plan_limits

logger = logging.getLogger(__name__)


class UsageAnalyticsService:
    """Service for usage history aggregation and analytics."""

    def __init__(self, db: Session):
        self.db = db
        self.plan_limits = get_global_plan_limits()

    def record_usage_snapshot(
        self, user_id: UUID, period_type: str = "hourly"
    ) -> UsageHistory:
        """Record current usage snapshot for a user."""
        logger.info(f"📊 Recording {period_type} usage snapshot for user {user_id}")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Calculate period boundaries
        now = datetime.now(UTC)
        period_start, period_end = self._calculate_period_boundaries(now, period_type)

        # Aggregate current usage data
        usage_data = self._aggregate_usage_data(user_id, period_start, period_end)

        # Check if snapshot already exists
        existing = (
            self.db.query(UsageHistory)
            .filter(
                and_(
                    UsageHistory.user_id == user_id,
                    UsageHistory.period_type == period_type,
                    UsageHistory.period_start == period_start,
                )
            )
            .first()
        )

        if existing:
            # Update existing snapshot
            for key, value in usage_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.recorded_at = now
            self.db.commit()
            logger.info(
                f"✅ Updated existing {period_type} snapshot for user {user_id}"
            )
            return existing
        else:
            # Create new snapshot
            snapshot = UsageHistory.create_snapshot(
                user_id=user_id,  # Pass UUID directly, not as string
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                usage_data=usage_data,
            )
            self.db.add(snapshot)
            self.db.commit()
            logger.info(f"✅ Created new {period_type} snapshot for user {user_id}")
            return snapshot

    def get_usage_trends(
        self, user_id: UUID, period: str = "30d", group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """Get usage trends for specified period."""
        logger.info(
            f"📈 Getting usage trends for user {user_id}, period: {period}, group_by: {group_by}"
        )

        start_date = self._parse_period_to_date(period)
        end_date = datetime.now(UTC)

        # Query usage history based on group_by preference
        if group_by == "day":
            period_type_filter = "daily"
        elif group_by == "week":
            period_type_filter = "daily"  # We'll aggregate daily data into weeks
        elif group_by == "month":
            period_type_filter = "monthly"
        else:
            period_type_filter = "daily"

        # Get data from usage_history table
        history_data = (
            self.db.query(UsageHistory)
            .filter(
                and_(
                    UsageHistory.user_id == user_id,
                    UsageHistory.period_type == period_type_filter,
                    UsageHistory.period_start >= start_date,
                    UsageHistory.period_start <= end_date,
                )
            )
            .order_by(UsageHistory.period_start)
            .all()
        )

        # If no history data, fall back to usage_log aggregation
        if not history_data:
            return self._aggregate_usage_logs_for_trends(
                user_id, start_date, end_date, group_by
            )

        # Format trend data
        trends = []
        for record in history_data:
            trends.append(
                {
                    "date": record.period_start.strftime("%Y-%m-%d"),
                    "sessions": record.sessions_created,
                    "minutes": float(record.audio_minutes_processed),
                    "hours": record.total_hours_processed,
                    "transcriptions": record.transcriptions_completed,
                    "exports": record.exports_generated,
                    "cost": float(record.total_cost_usd),
                    "utilization": record.utilization_percentage,
                    "success_rate": record.success_rate,
                    "avg_duration": record.avg_session_duration_minutes,
                }
            )

        logger.info(f"✅ Retrieved {len(trends)} trend data points for user {user_id}")
        return trends

    def predict_usage(self, user_id: UUID) -> Dict[str, Any]:
        """Predict future usage based on historical patterns."""
        logger.info(f"🔮 Generating usage predictions for user {user_id}")

        # Get last 90 days of data for better prediction accuracy
        historical_data = self.get_usage_trends(user_id, "90d", "day")

        if len(historical_data) < 7:
            logger.warning(f"⚠️ Insufficient data for predictions for user {user_id}")
            return {
                "predicted_sessions": 0,
                "predicted_minutes": 0,
                "estimated_limit_date": None,
                "confidence": 0.0,
                "recommendation": ("Insufficient historical data for predictions"),
            }

        # Simple trend analysis (can be enhanced with ML later)
        recent_days = historical_data[-14:]  # Last 2 weeks
        avg_daily_sessions = sum(d["sessions"] for d in recent_days) / len(recent_days)
        avg_daily_minutes = sum(d["minutes"] for d in recent_days) / len(recent_days)

        # Calculate growth rate
        early_period = historical_data[: len(historical_data) // 2]
        late_period = historical_data[len(historical_data) // 2 :]

        early_avg = (
            sum(d["sessions"] for d in early_period) / len(early_period)
            if early_period
            else 0
        )
        late_avg = (
            sum(d["sessions"] for d in late_period) / len(late_period)
            if late_period
            else 0
        )

        growth_rate = ((late_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0

        # Predict next 30 days
        days_in_month = 30
        predicted_sessions = avg_daily_sessions * days_in_month
        predicted_minutes = avg_daily_minutes * days_in_month

        # Get user's current plan limits
        user = self.db.query(User).filter(User.id == user_id).first()
        plan_config = self.plan_limits.get_plan_limit(user.plan.value)

        # Estimate when limits will be reached
        limit_date = None
        if avg_daily_minutes > 0:
            days_to_limit = plan_config.max_minutes / avg_daily_minutes
            if days_to_limit <= 30:  # Within next month
                limit_date = (
                    datetime.now(UTC) + timedelta(days=days_to_limit)
                ).isoformat()

        # Generate recommendation
        recommendation = self._generate_plan_recommendation(
            predicted_sessions, predicted_minutes, user.plan.value, growth_rate
        )

        # Calculate confidence based on data consistency
        confidence = min(len(historical_data) / 30, 1.0) * 0.8  # Max 80% confidence

        prediction = {
            "predicted_sessions": int(predicted_sessions),
            "predicted_minutes": int(predicted_minutes),
            "estimated_limit_date": limit_date,
            "confidence": confidence,
            "recommendation": recommendation,
            "growth_rate": growth_rate,
            "current_trend": (
                "growing"
                if growth_rate > 5
                else "stable"
                if growth_rate > -5
                else "declining"
            ),
        }

        logger.info(
            f"✅ Generated predictions for user {user_id}: {predicted_sessions} sessions, {predicted_minutes} minutes"
        )
        return prediction

    def generate_insights(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Generate personalized usage insights and recommendations."""
        logger.info(f"💡 Generating usage insights for user {user_id}")

        insights = []

        # Get recent usage data
        usage_data = self.get_usage_trends(user_id, "30d", "day")
        user = self.db.query(User).filter(User.id == user_id).first()

        if not usage_data or not user:
            return insights

        # Analyze patterns
        patterns = self._analyze_usage_patterns(usage_data, user)

        # Peak usage analysis
        if patterns.get("peak_day"):
            insights.append(
                {
                    "type": "pattern",
                    "title": "Peak Usage Day",
                    "message": (
                        f"You use the platform most on {patterns['peak_day']}s"
                    ),
                    "suggestion": (
                        "Consider scheduling heavy transcription tasks on this day"
                    ),
                    "priority": "medium",
                    "action": None,
                }
            )

        # Plan utilization analysis
        utilization = patterns.get("utilization", 0)
        if utilization < 30:
            insights.append(
                {
                    "type": "optimization",
                    "title": "Low Plan Utilization",
                    "message": (
                        f"You're using only {utilization:.1f}% of your {user.plan.value.upper()} plan"
                    ),
                    "suggestion": "Consider downgrading to save costs",
                    "priority": "low",
                    "action": "downgrade",
                }
            )
        elif utilization > 85:
            insights.append(
                {
                    "type": "warning",
                    "title": "High Plan Utilization",
                    "message": (
                        f"You're using {utilization:.1f}% of your plan capacity"
                    ),
                    "suggestion": "Consider upgrading to avoid hitting limits",
                    "priority": "high",
                    "action": "upgrade",
                }
            )

        # Growth trend analysis
        growth_rate = patterns.get("growth_rate", 0)
        if growth_rate > 20:
            insights.append(
                {
                    "type": "trend",
                    "title": "Rapid Usage Growth",
                    "message": (f"Your usage has grown {growth_rate:.1f}% this month"),
                    "suggestion": "You may need to upgrade your plan soon",
                    "priority": "high",
                    "action": "upgrade",
                }
            )
        elif growth_rate < -20:
            insights.append(
                {
                    "type": "trend",
                    "title": "Declining Usage",
                    "message": (
                        f"Your usage has decreased {abs(growth_rate):.1f}% this month"
                    ),
                    "suggestion": ("Consider if your current plan is still optimal"),
                    "priority": "low",
                    "action": "review",
                }
            )

        # Cost efficiency analysis
        if patterns.get("avg_cost_per_minute", 0) > 0:
            cost_per_minute = patterns["avg_cost_per_minute"]
            insights.append(
                {
                    "type": "cost",
                    "title": "Cost Analysis",
                    "message": (
                        f"Your average cost is ${cost_per_minute:.3f} per minute"
                    ),
                    "suggestion": "Track your most efficient usage patterns",
                    "priority": "low",
                    "action": None,
                }
            )

        logger.info(f"✅ Generated {len(insights)} insights for user {user_id}")
        return insights

    def _calculate_period_boundaries(
        self, timestamp: datetime, period_type: str
    ) -> Tuple[datetime, datetime]:
        """Calculate period start and end boundaries."""
        if period_type == "hourly":
            start = timestamp.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period_type == "daily":
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period_type == "monthly":
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:
            raise ValueError(f"Unsupported period type: {period_type}")

        return start, end

    def _aggregate_usage_data(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Aggregate usage data for a specific time period."""
        # Get usage logs for the period
        usage_logs = (
            self.db.query(UsageLog)
            .filter(
                and_(
                    UsageLog.user_id == user_id,
                    UsageLog.created_at >= start_date,
                    UsageLog.created_at < end_date,
                )
            )
            .all()
        )

        # Get sessions for the period
        sessions = (
            self.db.query(TranscriptionSession)
            .filter(
                and_(
                    TranscriptionSession.user_id == user_id,
                    TranscriptionSession.created_at >= start_date,
                    TranscriptionSession.created_at < end_date,
                )
            )
            .all()
        )

        # Calculate aggregated metrics
        total_minutes = sum(log.duration_minutes for log in usage_logs)
        total_cost = sum(float(log.cost_usd or 0) for log in usage_logs)
        billable_transcriptions = len([log for log in usage_logs if log.is_billable])
        free_retries = len(
            [
                log
                for log in usage_logs
                if log.transcription_type == TranscriptionType.RETRY_FAILED
            ]
        )

        # Provider breakdown
        google_minutes = sum(
            log.duration_minutes for log in usage_logs if log.stt_provider == "google"
        )
        assemblyai_minutes = sum(
            log.duration_minutes
            for log in usage_logs
            if log.stt_provider == "assemblyai"
        )

        # Calculate performance metrics
        completed_logs = [log for log in usage_logs if log.transcription_completed_at]
        avg_processing_time = 0
        if completed_logs:
            processing_times = [
                (
                    log.transcription_completed_at - log.transcription_started_at
                ).total_seconds()
                for log in completed_logs
                if log.transcription_started_at and log.transcription_completed_at
            ]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)

        # Get user's current plan info
        user = self.db.query(User).filter(User.id == user_id).first()
        plan_config = self.plan_limits.get_plan_limit(user.plan.value)

        # Convert PlanLimit to dict for usage data
        plan_limits_dict = {
            "sessions": plan_config.max_sessions,
            "transcriptions": plan_config.max_transcriptions,
            "minutes": plan_config.max_minutes,
            "file_size_mb": plan_config.max_file_size_mb,
            "export_formats": plan_config.export_formats,
        }

        # Calculate storage usage from session file sizes
        storage_used_mb = sum(
            getattr(session, "audio_file_size_mb", 0) or 0 for session in sessions
        )

        # Track exports by format from usage logs
        export_logs = [
            log
            for log in usage_logs
            if log.transcription_type and log.transcription_type.value == "export"
        ]
        exports_by_format = {}
        for log in export_logs:
            # Extract format from metadata if available, otherwise default to "unknown"
            format_type = "unknown"
            if log.metadata and "export_format" in log.metadata:
                format_type = log.metadata["export_format"].lower()
            current_count = exports_by_format.get(format_type, 0)
            exports_by_format[format_type] = current_count + 1

        # Track failed transcriptions from usage logs
        failed_transcriptions = len(
            [
                log
                for log in usage_logs
                if log.error_occurred
            ]
        )

        # Calculate API calls from total usage log entries
        api_calls_made = len(usage_logs)

        # Calculate concurrent sessions peak
        concurrent_peak = self._calculate_concurrent_sessions_peak(sessions)

        return {
            "sessions_created": len(sessions),
            "audio_minutes_processed": total_minutes,
            "transcriptions_completed": len(usage_logs),
            "exports_generated": len(export_logs),
            "storage_used_mb": storage_used_mb,
            "unique_clients": len(
                set(log.metadata.get("client_id") for log in usage_logs
                    if log.metadata and "client_id" in log.metadata)
            ),
            "api_calls_made": api_calls_made,
            "concurrent_sessions_peak": concurrent_peak,
            "plan_name": user.plan.value,
            "plan_limits": plan_limits_dict,
            "total_cost_usd": total_cost,
            "billable_transcriptions": billable_transcriptions,
            "free_retries": free_retries,
            "google_stt_minutes": google_minutes,
            "assemblyai_minutes": assemblyai_minutes,
            "exports_by_format": exports_by_format,
            "avg_processing_time_seconds": avg_processing_time,
            "failed_transcriptions": failed_transcriptions,
        }

    def _calculate_concurrent_sessions_peak(self, sessions) -> int:
        """Calculate the peak number of concurrent sessions."""
        if not sessions:
            return 0

        # Create timeline events for session start/end
        events = []
        for session in sessions:
            if hasattr(session, "created_at") and session.created_at:
                events.append((session.created_at, "start"))

                # Use updated_at as end time if available, otherwise assume 1
                # hour duration
                end_time = getattr(session, "updated_at", None)
                if not end_time:
                    from datetime import timedelta

                    end_time = session.created_at + timedelta(hours=1)
                events.append((end_time, "end"))

        # Sort events by timestamp
        events.sort(key=lambda x: x[0])

        # Calculate peak concurrent sessions
        current_concurrent = 0
        peak_concurrent = 0

        for timestamp, event_type in events:
            if event_type == "start":
                current_concurrent += 1
                peak_concurrent = max(peak_concurrent, current_concurrent)
            else:  # end
                current_concurrent -= 1

        return peak_concurrent

    def _parse_period_to_date(self, period: str) -> datetime:
        """Parse period string to start date."""
        now = datetime.now(UTC)

        if period == "7d":
            return now - timedelta(days=7)
        elif period == "30d":
            return now - timedelta(days=30)
        elif period == "3m":
            return now - timedelta(days=90)
        elif period == "12m":
            return now - timedelta(days=365)
        else:
            # Default to 30 days
            return now - timedelta(days=30)

    def _aggregate_usage_logs_for_trends(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
    ) -> List[Dict[str, Any]]:
        """Aggregate usage logs when no history data is available."""
        logger.info(f"📊 Falling back to usage log aggregation for user {user_id}")

        # This is a simplified version - should be enhanced for production
        usage_logs = (
            self.db.query(UsageLog)
            .filter(
                and_(
                    UsageLog.user_id == user_id,
                    UsageLog.created_at >= start_date,
                    UsageLog.created_at <= end_date,
                )
            )
            .all()
        )

        # Group by date
        daily_data = {}
        for log in usage_logs:
            date_key = log.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "sessions": 0,
                    "minutes": 0,
                    "transcriptions": 0,
                    "cost": 0,
                }
            daily_data[date_key]["transcriptions"] += 1
            daily_data[date_key]["minutes"] += log.duration_minutes
            daily_data[date_key]["cost"] += float(log.cost_cents or 0) / 100  # Convert cents to dollars

        # Convert to list format
        trends = []
        for date_str, data in sorted(daily_data.items()):
            trends.append(
                {
                    "date": date_str,
                    "sessions": data["sessions"],
                    "minutes": data["minutes"],
                    "hours": data["minutes"] / 60.0,
                    "transcriptions": data["transcriptions"],
                    "exports": 0,
                    "cost": data["cost"],
                    "utilization": 0,
                    "success_rate": 100,  # Assume success if in logs
                    "avg_duration": (data["minutes"] / max(data["transcriptions"], 1)),
                }
            )

        return trends

    def _analyze_usage_patterns(
        self, usage_data: List[Dict[str, Any]], user: User
    ) -> Dict[str, Any]:
        """Analyze usage patterns from historical data."""
        if not usage_data:
            return {}

        # Calculate overall metrics
        total_sessions = sum(d["sessions"] for d in usage_data)
        total_minutes = sum(d["minutes"] for d in usage_data)
        avg_daily_sessions = total_sessions / len(usage_data)

        # Get current plan limits
        plan_config = self.plan_limits.get_plan_limit(user.plan.value)
        utilization = (
            (total_minutes / plan_config.max_minutes) * 100
            if plan_config.max_minutes > 0
            else 0
        )

        # Calculate growth rate (comparing first half to second half)
        mid_point = len(usage_data) // 2
        if mid_point > 0:
            early_avg = sum(d["sessions"] for d in usage_data[:mid_point]) / mid_point
            late_avg = sum(d["sessions"] for d in usage_data[mid_point:]) / (
                len(usage_data) - mid_point
            )
            growth_rate = (
                ((late_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
            )
        else:
            growth_rate = 0

        # Find peak usage day (simplified - could be enhanced)
        peak_day = "Monday"  # Placeholder - would need actual day-of-week analysis

        # Calculate average cost per minute
        total_cost = sum(d.get("cost", 0) for d in usage_data)
        avg_cost_per_minute = total_cost / total_minutes if total_minutes > 0 else 0

        return {
            "utilization": utilization,
            "growth_rate": growth_rate,
            "peak_day": peak_day,
            "avg_daily_sessions": avg_daily_sessions,
            "avg_cost_per_minute": avg_cost_per_minute,
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
        }

    def _generate_plan_recommendation(
        self,
        predicted_sessions: float,
        predicted_minutes: float,
        current_plan: str,
        growth_rate: float,
    ) -> str:
        """Generate plan recommendation based on predictions."""
        current_limits = self.plan_limits.get_plan_limit(current_plan.lower())

        # Check if predicted usage exceeds current plan
        if predicted_minutes > current_limits.max_minutes * 0.8:  # 80% threshold
            if current_plan.lower() == "free":
                return "Consider upgrading to PRO plan to handle your growing usage"
            elif current_plan.lower() == "pro":
                return "Consider upgrading to ENTERPRISE plan for unlimited usage"
            else:
                return "Your usage is well within your ENTERPRISE plan limits"
        elif predicted_minutes < current_limits.max_minutes * 0.3:  # 30% threshold
            if current_plan.lower() == "enterprise":
                return "You may be over-paying - consider PRO plan for your usage level"
            elif current_plan.lower() == "pro":
                return "Consider if FREE plan might meet your needs"
            else:
                return "Your FREE plan seems appropriate for your usage"
        else:
            return f"Your {current_plan.upper()} plan is well-suited for your usage patterns"
