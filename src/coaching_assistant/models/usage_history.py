"""Usage history model for tracking historical usage patterns over time."""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DECIMAL,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from .base import BaseModel


class UsageHistory(BaseModel):
    """Historical usage tracking for analytics and trend analysis."""

    __tablename__ = "usage_history"

    # User reference
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Time period information
    recorded_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    period_type = Column(
        String(20), nullable=False
    )  # 'hourly', 'daily', 'monthly'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Core usage metrics
    sessions_created = Column(Integer, default=0, nullable=False)
    audio_minutes_processed = Column(DECIMAL(10, 2), default=0, nullable=False)
    transcriptions_completed = Column(Integer, default=0, nullable=False)
    exports_generated = Column(Integer, default=0, nullable=False)
    storage_used_mb = Column(DECIMAL(10, 2), default=0, nullable=False)

    # Additional metrics
    unique_clients = Column(Integer, default=0, nullable=False)
    api_calls_made = Column(Integer, default=0, nullable=False)
    concurrent_sessions_peak = Column(Integer, default=0, nullable=False)

    # Plan context (snapshot for historical accuracy)
    plan_name = Column(String(20), nullable=False)
    plan_limits = Column(JSON, default={}, nullable=False)

    # Cost tracking
    total_cost_usd = Column(DECIMAL(12, 4), default=0, nullable=False)
    billable_transcriptions = Column(Integer, default=0, nullable=False)
    free_retries = Column(Integer, default=0, nullable=False)

    # Provider breakdown
    google_stt_minutes = Column(DECIMAL(10, 2), default=0, nullable=False)
    assemblyai_minutes = Column(DECIMAL(10, 2), default=0, nullable=False)

    # Export format breakdown
    exports_by_format = Column(JSON, default={}, nullable=False)

    # Performance metrics
    avg_processing_time_seconds = Column(
        DECIMAL(8, 2), default=0, nullable=False
    )
    failed_transcriptions = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="usage_history")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "period_type",
            "period_start",
            name="uq_user_period_start",
        ),
        Index("idx_usage_history_user_period", "user_id", "period_start"),
        Index("idx_usage_history_recorded", "recorded_at"),
        Index("idx_usage_history_period_type", "period_type"),
    )

    def __repr__(self):
        return (
            f"<UsageHistory(id={self.id}, user_id={self.user_id}, "
            f"period_type={self.period_type}, period_start={self.period_start}, "
            f"sessions={self.sessions_created})>"
        )

    @property
    def total_hours_processed(self) -> float:
        """Get total hours processed."""
        return float(self.audio_minutes_processed) / 60.0

    @property
    def avg_session_duration_minutes(self) -> float:
        """Calculate average session duration in minutes."""
        if self.transcriptions_completed > 0:
            return (
                float(self.audio_minutes_processed)
                / self.transcriptions_completed
            )
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate transcription success rate."""
        total_attempts = (
            self.transcriptions_completed + self.failed_transcriptions
        )
        if total_attempts > 0:
            return (self.transcriptions_completed / total_attempts) * 100
        return 0.0

    @property
    def cost_per_minute(self) -> float:
        """Calculate cost per minute of audio processed."""
        if self.audio_minutes_processed > 0:
            return float(self.total_cost_usd) / float(
                self.audio_minutes_processed
            )
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
            "id": str(self.id),
            "user_id": str(self.user_id),
            "recorded_at": (
                self.recorded_at.isoformat() if self.recorded_at else None
            ),
            "period_type": self.period_type,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": (
                self.period_end.isoformat() if self.period_end else None
            ),
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
                "avg_processing_time_seconds": float(
                    self.avg_processing_time_seconds
                ),
                "failed_transcriptions": self.failed_transcriptions,
                "success_rate": self.success_rate,
                "avg_session_duration_minutes": self.avg_session_duration_minutes,
            },
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }

    @classmethod
    def create_snapshot(
        cls,
        user_id,  # Can be UUID or str
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
            audio_minutes_processed=usage_data.get(
                "audio_minutes_processed", 0
            ),
            transcriptions_completed=usage_data.get(
                "transcriptions_completed", 0
            ),
            exports_generated=usage_data.get("exports_generated", 0),
            storage_used_mb=usage_data.get("storage_used_mb", 0),
            unique_clients=usage_data.get("unique_clients", 0),
            api_calls_made=usage_data.get("api_calls_made", 0),
            concurrent_sessions_peak=usage_data.get(
                "concurrent_sessions_peak", 0
            ),
            plan_name=usage_data.get("plan_name", "FREE"),
            plan_limits=usage_data.get("plan_limits", {}),
            total_cost_usd=usage_data.get("total_cost_usd", 0),
            billable_transcriptions=usage_data.get(
                "billable_transcriptions", 0
            ),
            free_retries=usage_data.get("free_retries", 0),
            google_stt_minutes=usage_data.get("google_stt_minutes", 0),
            assemblyai_minutes=usage_data.get("assemblyai_minutes", 0),
            exports_by_format=usage_data.get("exports_by_format", {}),
            avg_processing_time_seconds=usage_data.get(
                "avg_processing_time_seconds", 0
            ),
            failed_transcriptions=usage_data.get("failed_transcriptions", 0),
        )
