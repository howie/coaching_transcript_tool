"""Usage analytics domain model for Clean Architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class UsageAnalytics:
    """Domain model for monthly aggregated analytics."""

    # Identifiers
    id: Optional[UUID] = None
    user_id: UUID = None
    month_year: str = None  # 'YYYY-MM'

    # Plan information
    primary_plan: str = "FREE"
    plan_changed_during_month: bool = False

    # Aggregated metrics
    sessions_created: int = 0
    transcriptions_completed: int = 0
    total_minutes_processed: Decimal = field(default_factory=lambda: Decimal("0"))
    total_cost_usd: Decimal = field(default_factory=lambda: Decimal("0"))

    # Billing breakdown
    original_transcriptions: int = 0
    free_retries: int = 0
    paid_retranscriptions: int = 0

    # Provider breakdown
    google_stt_minutes: Decimal = field(default_factory=lambda: Decimal("0"))
    assemblyai_minutes: Decimal = field(default_factory=lambda: Decimal("0"))

    # Export activity
    exports_by_format: Dict[str, int] = field(default_factory=dict)
    total_exports: int = 0

    # Time period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
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
