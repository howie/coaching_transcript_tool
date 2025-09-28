"""PlanConfiguration domain model with business rules."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .user import UserPlan


@dataclass
class PlanFeatures:
    """Plan-specific features."""

    priority_support: bool = False
    team_collaboration: bool = False
    api_access: bool = False
    sso: bool = False
    custom_branding: bool = False


@dataclass
class PlanLimits:
    """Plan usage limits."""

    max_sessions: int = 0
    max_total_minutes: int = 0
    max_transcription_count: int = 0
    max_file_size_mb: int = 0
    export_formats: List[str] = field(default_factory=list)
    concurrent_processing: int = 1
    retention_days: int = 30


@dataclass
class PlanPricing:
    """Plan pricing information."""

    monthly_price_cents: int = 0
    annual_price_cents: int = 0
    currency: str = "USD"
    monthly_price_twd_cents: int = 0
    annual_price_twd_cents: int = 0


@dataclass
class PlanConfiguration:
    """Domain model for billing plan configuration."""

    # Required fields first
    id: UUID
    plan_type: UserPlan
    plan_name: str
    display_name: str
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    description: Optional[str] = None
    tagline: Optional[str] = None

    # Business rules embedded as value objects
    limits: PlanLimits = field(default_factory=PlanLimits)
    features: PlanFeatures = field(default_factory=PlanFeatures)
    pricing: PlanPricing = field(default_factory=PlanPricing)

    # Display configuration
    is_popular: bool = False
    is_enterprise: bool = False
    color_scheme: str = "gray"
    sort_order: int = 0

    # Status
    is_active: bool = True

    def get_monthly_price_usd(self) -> float:
        """Get monthly price in USD dollars."""
        return self.pricing.monthly_price_cents / 100.0

    def get_annual_price_usd(self) -> float:
        """Get annual price in USD dollars."""
        return self.pricing.annual_price_cents / 100.0

    def get_monthly_price_twd(self) -> float:
        """Get monthly price in TWD dollars."""
        return self.pricing.monthly_price_twd_cents / 100.0

    def get_annual_price_twd(self) -> float:
        """Get annual price in TWD dollars."""
        return self.pricing.annual_price_twd_cents / 100.0

    def has_feature(self, feature_name: str) -> bool:
        """Check if plan has a specific feature."""
        return getattr(self.features, feature_name, False)

    def can_export_format(self, format_name: str) -> bool:
        """Check if plan supports a specific export format."""
        return format_name in self.limits.export_formats

    def is_within_limits(
        self, sessions: int, minutes: int, transcriptions: int
    ) -> bool:
        """Check if usage is within plan limits."""
        return (
            sessions <= self.limits.max_sessions
            and minutes <= self.limits.max_total_minutes
            and transcriptions <= self.limits.max_transcription_count
        )
