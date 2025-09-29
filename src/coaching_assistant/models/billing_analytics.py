"""Billing Analytics model for enhanced admin reporting and revenue analysis."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class BillingAnalytics(BaseModel):
    """Enhanced billing analytics for admin reporting and revenue analysis."""

    __tablename__ = "billing_analytics"

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
    )  # 'daily', 'weekly', 'monthly', 'quarterly'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Plan information
    plan_name = Column(String(20), nullable=False)
    plan_changed_during_period = Column(Boolean, default=False, nullable=False)
    previous_plan = Column(String(20), nullable=True)
    plan_change_date = Column(DateTime(timezone=True), nullable=True)

    # Revenue metrics
    total_revenue_usd = Column(DECIMAL(12, 4), default=0, nullable=False)
    subscription_revenue_usd = Column(DECIMAL(12, 4), default=0, nullable=False)
    usage_overage_usd = Column(DECIMAL(12, 4), default=0, nullable=False)
    one_time_fees_usd = Column(DECIMAL(12, 4), default=0, nullable=False)

    # Usage metrics
    sessions_created = Column(Integer, default=0, nullable=False)
    transcriptions_completed = Column(Integer, default=0, nullable=False)
    total_minutes_processed = Column(DECIMAL(10, 2), default=0, nullable=False)
    unique_active_days = Column(Integer, default=0, nullable=False)

    # Billing breakdown
    original_transcriptions = Column(Integer, default=0, nullable=False)
    free_retries = Column(Integer, default=0, nullable=False)
    paid_retranscriptions = Column(Integer, default=0, nullable=False)
    overage_minutes = Column(DECIMAL(10, 2), default=0, nullable=False)

    # Provider cost breakdown
    google_stt_cost_usd = Column(DECIMAL(10, 4), default=0, nullable=False)
    assemblyai_cost_usd = Column(DECIMAL(10, 4), default=0, nullable=False)
    total_provider_cost_usd = Column(DECIMAL(10, 4), default=0, nullable=False)

    # Customer health metrics
    plan_utilization_percentage = Column(DECIMAL(5, 2), default=0, nullable=False)
    days_active_in_period = Column(Integer, default=0, nullable=False)
    avg_sessions_per_active_day = Column(DECIMAL(8, 2), default=0, nullable=False)
    churn_risk_score = Column(DECIMAL(3, 2), default=0, nullable=False)  # 0.0-1.0

    # Export and feature usage
    exports_by_format = Column(JSON, default={}, nullable=False)
    total_exports = Column(Integer, default=0, nullable=False)
    features_used = Column(JSON, default=[], nullable=False)  # List of feature names
    api_calls_made = Column(Integer, default=0, nullable=False)

    # Cohort and segmentation
    user_signup_date = Column(DateTime(timezone=True), nullable=True)
    user_tenure_days = Column(Integer, default=0, nullable=False)
    user_segment = Column(
        String(20), nullable=True
    )  # 'new', 'growing', 'power', 'enterprise'

    # Performance and quality metrics
    avg_processing_time_seconds = Column(DECIMAL(8, 2), default=0, nullable=False)
    success_rate_percentage = Column(DECIMAL(5, 2), default=100, nullable=False)
    support_tickets_count = Column(Integer, default=0, nullable=False)

    # Geographic and demographic
    user_timezone = Column(String(50), nullable=True)
    user_country = Column(String(2), nullable=True)  # ISO country code
    user_language = Column(String(10), nullable=True)

    # Predictive metrics
    predicted_next_month_usage = Column(DECIMAL(10, 2), default=0, nullable=False)
    upgrade_probability = Column(DECIMAL(3, 2), default=0, nullable=False)  # 0.0-1.0
    lifetime_value_estimate = Column(DECIMAL(12, 4), default=0, nullable=False)

    # Notes and flags
    anomaly_flags = Column(JSON, default=[], nullable=False)
    billing_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="billing_analytics")

    # Constraints and indexes for performance
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "period_type",
            "period_start",
            name="uq_billing_analytics_period",
        ),
        Index("idx_billing_analytics_user_period", "user_id", "period_start"),
        Index("idx_billing_analytics_recorded", "recorded_at"),
        Index("idx_billing_analytics_revenue", "total_revenue_usd"),
        Index("idx_billing_analytics_plan", "plan_name"),
        Index("idx_billing_analytics_segment", "user_segment"),
        Index("idx_billing_analytics_churn_risk", "churn_risk_score"),
    )

    def __repr__(self):
        return (
            f"<BillingAnalytics(id={self.id}, user_id={self.user_id}, "
            f"period_type={self.period_type}, period_start={self.period_start}, "
            f"revenue=${self.total_revenue_usd})>"
        )

    @property
    def total_hours_processed(self) -> float:
        """Get total hours processed."""
        return float(self.total_minutes_processed or 0) / 60.0

    @property
    def gross_margin_usd(self) -> float:
        """Calculate gross margin (revenue - provider costs)."""
        return float(self.total_revenue_usd or 0) - float(
            self.total_provider_cost_usd or 0
        )

    @property
    def gross_margin_percentage(self) -> float:
        """Calculate gross margin percentage."""
        if self.total_revenue_usd and self.total_revenue_usd > 0:
            return (self.gross_margin_usd / float(self.total_revenue_usd)) * 100
        return 0.0

    @property
    def revenue_per_minute(self) -> float:
        """Calculate revenue per minute processed."""
        if self.total_minutes_processed and self.total_minutes_processed > 0:
            return float(self.total_revenue_usd or 0) / float(
                self.total_minutes_processed
            )
        return 0.0

    @property
    def cost_per_minute(self) -> float:
        """Calculate provider cost per minute processed."""
        if self.total_minutes_processed and self.total_minutes_processed > 0:
            return float(self.total_provider_cost_usd or 0) / float(
                self.total_minutes_processed
            )
        return 0.0

    @property
    def avg_session_duration_minutes(self) -> float:
        """Calculate average session duration in minutes."""
        if self.transcriptions_completed and self.transcriptions_completed > 0:
            return (
                float(self.total_minutes_processed or 0) / self.transcriptions_completed
            )
        return 0.0

    @property
    def is_power_user(self) -> bool:
        """Determine if user is a power user based on usage patterns."""
        return (
            float(self.plan_utilization_percentage or 0) > 70
            and (self.days_active_in_period or 0) > (self._get_period_days() * 0.6)
            and float(self.avg_sessions_per_active_day or 0) > 3
        )

    @property
    def is_at_risk(self) -> bool:
        """Determine if user is at churn risk."""
        return (
            float(self.churn_risk_score or 0) > 0.7
            or (self.days_active_in_period or 0) < (self._get_period_days() * 0.2)
            or float(self.plan_utilization_percentage or 0) < 10
        )

    def _get_period_days(self) -> int:
        """Get number of days in the period."""
        return (self.period_end - self.period_start).days

    def calculate_customer_health_score(self) -> float:
        """Calculate overall customer health score (0-100)."""
        # Weighted scoring based on multiple factors
        utilization_score = min(float(self.plan_utilization_percentage or 0), 100) * 0.3
        activity_score = (
            ((self.days_active_in_period or 0) / self._get_period_days()) * 100 * 0.3
        )
        usage_score = min(float(self.avg_sessions_per_active_day or 0) * 10, 100) * 0.2
        success_score = float(self.success_rate_percentage or 100) * 0.2

        health_score = utilization_score + activity_score + usage_score + success_score
        return min(health_score, 100.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "recorded_at": (self.recorded_at.isoformat() if self.recorded_at else None),
            "period": {
                "type": self.period_type,
                "start": (self.period_start.isoformat() if self.period_start else None),
                "end": (self.period_end.isoformat() if self.period_end else None),
                "days": self._get_period_days(),
            },
            "plan_info": {
                "current_plan": self.plan_name,
                "plan_changed": self.plan_changed_during_period,
                "previous_plan": self.previous_plan,
                "change_date": (
                    self.plan_change_date.isoformat() if self.plan_change_date else None
                ),
            },
            "revenue": {
                "total": float(self.total_revenue_usd or 0),
                "subscription": float(self.subscription_revenue_usd or 0),
                "overage": float(self.usage_overage_usd or 0),
                "one_time": float(self.one_time_fees_usd or 0),
                "per_minute": self.revenue_per_minute,
            },
            "usage": {
                "sessions_created": self.sessions_created or 0,
                "transcriptions_completed": self.transcriptions_completed or 0,
                "total_minutes": float(self.total_minutes_processed or 0),
                "total_hours": self.total_hours_processed,
                "active_days": self.days_active_in_period or 0,
                "avg_sessions_per_day": float(self.avg_sessions_per_active_day or 0),
                "avg_session_duration": self.avg_session_duration_minutes,
            },
            "billing": {
                "original_transcriptions": self.original_transcriptions or 0,
                "free_retries": self.free_retries or 0,
                "paid_retranscriptions": self.paid_retranscriptions or 0,
                "overage_minutes": float(self.overage_minutes or 0),
            },
            "costs": {
                "google_stt": float(self.google_stt_cost_usd or 0),
                "assemblyai": float(self.assemblyai_cost_usd or 0),
                "total_provider": float(self.total_provider_cost_usd or 0),
                "per_minute": self.cost_per_minute,
            },
            "metrics": {
                "plan_utilization": float(self.plan_utilization_percentage or 0),
                "churn_risk_score": float(self.churn_risk_score or 0),
                "success_rate": float(self.success_rate_percentage or 100),
                "customer_health_score": (self.calculate_customer_health_score()),
                "gross_margin": self.gross_margin_usd,
                "gross_margin_percentage": self.gross_margin_percentage,
            },
            "predictions": {
                "next_month_usage": float(self.predicted_next_month_usage or 0),
                "upgrade_probability": float(self.upgrade_probability or 0),
                "lifetime_value": float(self.lifetime_value_estimate or 0),
            },
            "exports": {
                "by_format": self.exports_by_format or {},
                "total": self.total_exports or 0,
            },
            "user_profile": {
                "signup_date": (
                    self.user_signup_date.isoformat() if self.user_signup_date else None
                ),
                "tenure_days": self.user_tenure_days or 0,
                "segment": self.user_segment,
                "timezone": self.user_timezone,
                "country": self.user_country,
                "language": self.user_language,
            },
            "quality": {
                "avg_processing_time": float(self.avg_processing_time_seconds or 0),
                "support_tickets": self.support_tickets_count or 0,
                "features_used": self.features_used or [],
                "api_calls": self.api_calls_made or 0,
            },
            "flags": {
                "is_power_user": self.is_power_user,
                "is_at_risk": self.is_at_risk,
                "anomaly_flags": self.anomaly_flags or [],
                "billing_notes": self.billing_notes,
            },
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }

    @classmethod
    def create_from_usage_data(
        cls,
        user_id,  # Can be UUID or str
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        usage_data: Dict[str, Any],
        revenue_data: Dict[str, Any] = None,
        user_profile: Dict[str, Any] = None,
    ) -> "BillingAnalytics":
        """Create billing analytics record from aggregated data."""
        if revenue_data is None:
            revenue_data = {}
        if user_profile is None:
            user_profile = {}

        return cls(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            recorded_at=datetime.now(UTC),
            # Plan info
            plan_name=usage_data.get("plan_name", "FREE"),
            plan_changed_during_period=usage_data.get("plan_changed", False),
            previous_plan=usage_data.get("previous_plan"),
            plan_change_date=usage_data.get("plan_change_date"),
            # Revenue
            total_revenue_usd=Decimal(str(revenue_data.get("total_revenue", 0))),
            subscription_revenue_usd=Decimal(
                str(revenue_data.get("subscription_revenue", 0))
            ),
            usage_overage_usd=Decimal(str(revenue_data.get("overage_revenue", 0))),
            one_time_fees_usd=Decimal(str(revenue_data.get("one_time_fees", 0))),
            # Usage
            sessions_created=usage_data.get("sessions_created", 0),
            transcriptions_completed=usage_data.get("transcriptions_completed", 0),
            total_minutes_processed=Decimal(
                str(usage_data.get("total_minutes_processed", 0))
            ),
            unique_active_days=usage_data.get("unique_active_days", 0),
            # Billing breakdown
            original_transcriptions=usage_data.get("original_transcriptions", 0),
            free_retries=usage_data.get("free_retries", 0),
            paid_retranscriptions=usage_data.get("paid_retranscriptions", 0),
            overage_minutes=Decimal(str(usage_data.get("overage_minutes", 0))),
            # Provider costs
            google_stt_cost_usd=Decimal(str(usage_data.get("google_stt_cost", 0))),
            assemblyai_cost_usd=Decimal(str(usage_data.get("assemblyai_cost", 0))),
            total_provider_cost_usd=Decimal(
                str(usage_data.get("total_provider_cost", 0))
            ),
            # Metrics
            plan_utilization_percentage=Decimal(
                str(usage_data.get("plan_utilization", 0))
            ),
            days_active_in_period=usage_data.get("days_active", 0),
            avg_sessions_per_active_day=Decimal(
                str(usage_data.get("avg_sessions_per_day", 0))
            ),
            churn_risk_score=Decimal(str(usage_data.get("churn_risk_score", 0))),
            # Export and features
            exports_by_format=usage_data.get("exports_by_format", {}),
            total_exports=usage_data.get("total_exports", 0),
            features_used=usage_data.get("features_used", []),
            api_calls_made=usage_data.get("api_calls", 0),
            # User profile
            user_signup_date=user_profile.get("signup_date"),
            user_tenure_days=user_profile.get("tenure_days", 0),
            user_segment=user_profile.get("segment"),
            user_timezone=user_profile.get("timezone"),
            user_country=user_profile.get("country"),
            user_language=user_profile.get("language"),
            # Performance
            avg_processing_time_seconds=Decimal(
                str(usage_data.get("avg_processing_time", 0))
            ),
            success_rate_percentage=Decimal(str(usage_data.get("success_rate", 100))),
            support_tickets_count=usage_data.get("support_tickets", 0),
            # Predictions
            predicted_next_month_usage=Decimal(
                str(usage_data.get("predicted_usage", 0))
            ),
            upgrade_probability=Decimal(str(usage_data.get("upgrade_probability", 0))),
            lifetime_value_estimate=Decimal(str(usage_data.get("ltv_estimate", 0))),
            # Flags and notes
            anomaly_flags=usage_data.get("anomaly_flags", []),
            billing_notes=usage_data.get("billing_notes"),
        )
