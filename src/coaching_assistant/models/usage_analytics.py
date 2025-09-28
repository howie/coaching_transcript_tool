"""Usage analytics model for pre-aggregated monthly data."""

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class UsageAnalytics(BaseModel):
    """Monthly aggregated analytics for performance."""

    __tablename__ = "usage_analytics"

    # User reference
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    month_year = Column(String(7), nullable=False)  # 'YYYY-MM'

    # Plan information
    primary_plan = Column(String(20), nullable=False)
    plan_changed_during_month = Column(Boolean, default=False, nullable=False)

    # Aggregated metrics
    sessions_created = Column(Integer, default=0, nullable=False)
    transcriptions_completed = Column(Integer, default=0, nullable=False)
    total_minutes_processed = Column(DECIMAL(10, 2), default=0, nullable=False)
    total_cost_usd = Column(DECIMAL(12, 4), default=0, nullable=False)

    # Billing breakdown
    original_transcriptions = Column(Integer, default=0, nullable=False)
    free_retries = Column(Integer, default=0, nullable=False)
    paid_retranscriptions = Column(Integer, default=0, nullable=False)

    # Provider breakdown
    google_stt_minutes = Column(DECIMAL(10, 2), default=0, nullable=False)
    assemblyai_minutes = Column(DECIMAL(10, 2), default=0, nullable=False)

    # Export activity
    exports_by_format = Column(JSON, default={}, nullable=False)
    total_exports = Column(Integer, default=0, nullable=False)

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="usage_analytics")

    # Unique constraint on user_id and month_year
    __table_args__ = (UniqueConstraint("user_id", "month_year", name="uq_user_month"),)

    def __repr__(self):
        return (
            f"<UsageAnalytics(id={self.id}, user_id={self.user_id}, "
            f"month_year={self.month_year}, total_minutes={self.total_minutes_processed})>"
        )

    @property
    def total_hours_processed(self) -> float:
        """Get total hours processed."""
        return float(self.total_minutes_processed) / 60.0

    @property
    def avg_session_duration_minutes(self) -> float:
        """Calculate average session duration in minutes."""
        if self.transcriptions_completed > 0:
            return float(self.total_minutes_processed) / self.transcriptions_completed
        return 0.0

    @property
    def avg_cost_per_transcription(self) -> float:
        """Calculate average cost per transcription."""
        billable_transcriptions = (
            self.original_transcriptions + self.paid_retranscriptions
        )
        if billable_transcriptions > 0:
            return float(self.total_cost_usd) / billable_transcriptions
        return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "month_year": self.month_year,
            "primary_plan": self.primary_plan,
            "plan_changed_during_month": self.plan_changed_during_month,
            "sessions_created": self.sessions_created,
            "transcriptions_completed": self.transcriptions_completed,
            "total_minutes_processed": float(self.total_minutes_processed),
            "total_hours_processed": self.total_hours_processed,
            "total_cost_usd": float(self.total_cost_usd),
            "billing_breakdown": {
                "original": self.original_transcriptions,
                "free_retries": self.free_retries,
                "paid_retranscriptions": self.paid_retranscriptions,
            },
            "provider_breakdown": {
                "google_minutes": float(self.google_stt_minutes),
                "assemblyai_minutes": float(self.assemblyai_minutes),
            },
            "export_activity": {
                "formats": self.exports_by_format,
                "total": self.total_exports,
            },
            "period": {
                "start": (self.period_start.isoformat() if self.period_start else None),
                "end": (self.period_end.isoformat() if self.period_end else None),
            },
            "avg_session_duration_minutes": self.avg_session_duration_minutes,
            "avg_cost_per_transcription": self.avg_cost_per_transcription,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }
