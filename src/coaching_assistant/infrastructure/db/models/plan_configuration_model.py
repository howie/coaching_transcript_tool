"""PlanConfigurationModel ORM with domain model conversion."""

import uuid

from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from ....core.models.plan_configuration import (
    PlanConfiguration,
    PlanFeatures,
    PlanLimits,
    PlanPricing,
)
from ....core.models.user import UserPlan
from .base import BaseModel


class PlanConfigurationModel(BaseModel):
    """ORM model for PlanConfiguration entity with SQLAlchemy mappings."""

    __tablename__ = "plan_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan identification
    plan_type = Column(
        SQLEnum(UserPlan, values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
        index=True,
    )
    plan_name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500))
    tagline = Column(String(200))

    # Usage limits (stored as JSON for flexibility)
    limits = Column(JSON, nullable=False, default=dict)
    # Features (stored as JSON for flexibility)
    features = Column(JSON, nullable=False, default=dict)

    # Pricing - all amounts in cents (integer) to avoid float precision issues
    monthly_price_cents = Column(Integer, nullable=False, default=0)
    annual_price_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")

    # Pricing in TWD (Taiwan Dollar)
    monthly_price_twd_cents = Column(Integer, nullable=False, default=0)
    annual_price_twd_cents = Column(Integer, nullable=False, default=0)

    # Display configuration
    is_popular = Column(Boolean, default=False)
    is_enterprise = Column(Boolean, default=False)
    color_scheme = Column(String(20), default="gray")
    sort_order = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    def to_domain(self) -> PlanConfiguration:
        """Convert ORM model to domain model."""
        # Parse limits JSON into PlanLimits object
        limits_data = self.limits or {}
        limits = PlanLimits(
            max_sessions=limits_data.get("max_sessions", 0),
            max_total_minutes=limits_data.get("max_total_minutes", 0),
            max_transcription_count=limits_data.get("max_transcription_count", 0),
            max_file_size_mb=limits_data.get("max_file_size_mb", 0),
            export_formats=limits_data.get("export_formats", []),
            concurrent_processing=limits_data.get("concurrent_processing", 1),
            retention_days=limits_data.get("retention_days", 30),
        )

        # Parse features JSON into PlanFeatures object
        features_data = self.features or {}
        features = PlanFeatures(
            priority_support=features_data.get("priority_support", False),
            team_collaboration=features_data.get("team_collaboration", False),
            api_access=features_data.get("api_access", False),
            sso=features_data.get("sso", False),
            custom_branding=features_data.get("custom_branding", False),
        )

        # Create pricing object
        pricing = PlanPricing(
            monthly_price_cents=self.monthly_price_cents,
            annual_price_cents=self.annual_price_cents,
            currency=self.currency,
            monthly_price_twd_cents=self.monthly_price_twd_cents,
            annual_price_twd_cents=self.annual_price_twd_cents,
        )

        return PlanConfiguration(
            id=self.id,
            plan_type=self.plan_type,
            plan_name=self.plan_name,
            display_name=self.display_name,
            description=self.description,
            tagline=self.tagline,
            limits=limits,
            features=features,
            pricing=pricing,
            is_popular=self.is_popular,
            is_enterprise=self.is_enterprise,
            color_scheme=self.color_scheme,
            sort_order=self.sort_order,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, plan_config: PlanConfiguration) -> "PlanConfigurationModel":
        """Create ORM model from domain model."""
        # Convert limits to JSON
        limits_dict = {
            "max_sessions": plan_config.limits.max_sessions,
            "max_total_minutes": plan_config.limits.max_total_minutes,
            "max_transcription_count": (plan_config.limits.max_transcription_count),
            "max_file_size_mb": plan_config.limits.max_file_size_mb,
            "export_formats": plan_config.limits.export_formats,
            "concurrent_processing": plan_config.limits.concurrent_processing,
            "retention_days": plan_config.limits.retention_days,
        }

        # Convert features to JSON
        features_dict = {
            "priority_support": plan_config.features.priority_support,
            "team_collaboration": plan_config.features.team_collaboration,
            "api_access": plan_config.features.api_access,
            "sso": plan_config.features.sso,
            "custom_branding": plan_config.features.custom_branding,
        }

        return cls(
            id=plan_config.id,
            plan_type=plan_config.plan_type,
            plan_name=plan_config.plan_name,
            display_name=plan_config.display_name,
            description=plan_config.description,
            tagline=plan_config.tagline,
            limits=limits_dict,
            features=features_dict,
            monthly_price_cents=plan_config.pricing.monthly_price_cents,
            annual_price_cents=plan_config.pricing.annual_price_cents,
            currency=plan_config.pricing.currency,
            monthly_price_twd_cents=plan_config.pricing.monthly_price_twd_cents,
            annual_price_twd_cents=plan_config.pricing.annual_price_twd_cents,
            is_popular=plan_config.is_popular,
            is_enterprise=plan_config.is_enterprise,
            color_scheme=plan_config.color_scheme,
            sort_order=plan_config.sort_order,
            is_active=plan_config.is_active,
            created_at=plan_config.created_at,
            updated_at=plan_config.updated_at,
        )

    def update_from_domain(self, plan_config: PlanConfiguration) -> None:
        """Update ORM model from domain model."""
        # Update basic fields
        self.plan_name = plan_config.plan_name
        self.display_name = plan_config.display_name
        self.description = plan_config.description
        self.tagline = plan_config.tagline

        # Update limits
        self.limits = {
            "max_sessions": plan_config.limits.max_sessions,
            "max_total_minutes": plan_config.limits.max_total_minutes,
            "max_transcription_count": (plan_config.limits.max_transcription_count),
            "max_file_size_mb": plan_config.limits.max_file_size_mb,
            "export_formats": plan_config.limits.export_formats,
            "concurrent_processing": plan_config.limits.concurrent_processing,
            "retention_days": plan_config.limits.retention_days,
        }

        # Update features
        self.features = {
            "priority_support": plan_config.features.priority_support,
            "team_collaboration": plan_config.features.team_collaboration,
            "api_access": plan_config.features.api_access,
            "sso": plan_config.features.sso,
            "custom_branding": plan_config.features.custom_branding,
        }

        # Update pricing
        self.monthly_price_cents = plan_config.pricing.monthly_price_cents
        self.annual_price_cents = plan_config.pricing.annual_price_cents
        self.currency = plan_config.pricing.currency
        self.monthly_price_twd_cents = plan_config.pricing.monthly_price_twd_cents
        self.annual_price_twd_cents = plan_config.pricing.annual_price_twd_cents

        # Update display configuration
        self.is_popular = plan_config.is_popular
        self.is_enterprise = plan_config.is_enterprise
        self.color_scheme = plan_config.color_scheme
        self.sort_order = plan_config.sort_order
        self.is_active = plan_config.is_active
        self.updated_at = plan_config.updated_at
