"""Usage history domain model for Clean Architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class UsageHistory:
    """Domain model for historical usage tracking and analytics."""

    # Identifiers
    id: Optional[UUID] = None
    user_id: UUID = None

    # Time period information
    recorded_at: datetime = None
    period_type: str = None  # 'hourly', 'daily', 'monthly'
    period_start: datetime = None
    period_end: datetime = None

    # Core usage metrics
    sessions_created: int = 0
    audio_minutes_processed: Decimal = field(default_factory=lambda: Decimal("0"))
    transcriptions_completed: int = 0
    exports_generated: int = 0
    storage_used_mb: Decimal = field(default_factory=lambda: Decimal("0"))

    # Additional metrics
    unique_clients: int = 0
    api_calls_made: int = 0
    concurrent_sessions_peak: int = 0

    # Plan context (snapshot for historical accuracy)
    plan_name: str = "FREE"
    plan_limits: Dict[str, Any] = field(default_factory=dict)

    # Cost tracking
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal("0"))
    billable_transcriptions: int = 0
    free_retries: int = 0

    # Provider breakdown
    google_stt_minutes: Decimal = field(default_factory=lambda: Decimal("0"))
    assemblyai_minutes: Decimal = field(default_factory=lambda: Decimal("0"))

    # Export format breakdown
    exports_by_format: Dict[str, int] = field(default_factory=dict)

    # Performance metrics
    avg_processing_time_seconds: Decimal = field(default_factory=lambda: Decimal("0"))
    failed_transcriptions: int = 0

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def total_hours_processed(self) -> float:
        """Get total hours processed."""
        return float(self.audio_minutes_processed) / 60.0

    @property
    def avg_session_duration_minutes(self) -> float:
        """Calculate average session duration in minutes."""
        if self.transcriptions_completed > 0:
            return float(self.audio_minutes_processed) / self.transcriptions_completed
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate transcription success rate."""
        total_attempts = self.transcriptions_completed + self.failed_transcriptions
        if total_attempts > 0:
            return (self.transcriptions_completed / total_attempts) * 100
        return 0.0

    @property
    def cost_per_minute(self) -> float:
        """Calculate cost per minute of audio processed."""
        if self.audio_minutes_processed > 0:
            return float(self.total_cost_usd) / float(self.audio_minutes_processed)
        return 0.0

    @property
    def utilization_percentage(self) -> float:
        """Calculate plan utilization percentage."""
        if not self.plan_limits:
            return 0.0

        plan_minutes = self.plan_limits.get("minutes", 0)
        if plan_minutes > 0:
            return (float(self.audio_minutes_processed) / plan_minutes) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "recorded_at": (self.recorded_at.isoformat() if self.recorded_at else None),
            "period_type": self.period_type,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": (self.period_end.isoformat() if self.period_end else None),
            "usage_metrics": {
                "sessions_created": self.sessions_created,
                "audio_minutes_processed": float(self.audio_minutes_processed),
                "audio_hours_processed": self.total_hours_processed,
                "transcriptions_completed": self.transcriptions_completed,
                "exports_generated": self.exports_generated,
                "storage_used_mb": float(self.storage_used_mb),
                "unique_clients": self.unique_clients,
                "api_calls_made": self.api_calls_made,
                "concurrent_sessions_peak": self.concurrent_sessions_peak,
            },
            "plan_context": {
                "plan_name": self.plan_name,
                "plan_limits": self.plan_limits,
                "utilization_percentage": self.utilization_percentage,
            },
            "cost_metrics": {
                "total_cost_usd": float(self.total_cost_usd),
                "billable_transcriptions": self.billable_transcriptions,
                "free_retries": self.free_retries,
                "cost_per_minute": self.cost_per_minute,
            },
            "provider_breakdown": {
                "google_stt_minutes": float(self.google_stt_minutes),
                "assemblyai_minutes": float(self.assemblyai_minutes),
            },
            "export_activity": {
                "formats": self.exports_by_format,
                "total": self.exports_generated,
            },
            "performance_metrics": {
                "avg_processing_time_seconds": float(self.avg_processing_time_seconds),
                "failed_transcriptions": self.failed_transcriptions,
                "success_rate": self.success_rate,
                "avg_session_duration_minutes": (self.avg_session_duration_minutes),
            },
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }

    @classmethod
    def create_snapshot(
        cls,
        user_id: UUID,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        usage_data: Dict[str, Any],
    ) -> "UsageHistory":
        """Create a usage history snapshot from aggregated data."""
        return cls(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            recorded_at=datetime.utcnow(),
            sessions_created=usage_data.get("sessions_created", 0),
            audio_minutes_processed=Decimal(
                str(usage_data.get("audio_minutes_processed", 0))
            ),
            transcriptions_completed=usage_data.get("transcriptions_completed", 0),
            exports_generated=usage_data.get("exports_generated", 0),
            storage_used_mb=Decimal(str(usage_data.get("storage_used_mb", 0))),
            unique_clients=usage_data.get("unique_clients", 0),
            api_calls_made=usage_data.get("api_calls_made", 0),
            concurrent_sessions_peak=usage_data.get("concurrent_sessions_peak", 0),
            plan_name=usage_data.get("plan_name", "FREE"),
            plan_limits=usage_data.get("plan_limits", {}),
            total_cost_usd=Decimal(str(usage_data.get("total_cost_usd", 0))),
            billable_transcriptions=usage_data.get("billable_transcriptions", 0),
            free_retries=usage_data.get("free_retries", 0),
            google_stt_minutes=Decimal(str(usage_data.get("google_stt_minutes", 0))),
            assemblyai_minutes=Decimal(str(usage_data.get("assemblyai_minutes", 0))),
            exports_by_format=usage_data.get("exports_by_format", {}),
            avg_processing_time_seconds=Decimal(
                str(usage_data.get("avg_processing_time_seconds", 0))
            ),
            failed_transcriptions=usage_data.get("failed_transcriptions", 0),
        )
