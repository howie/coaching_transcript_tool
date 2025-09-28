"""
Plan Configuration model for dynamic billing plan management.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    JSON,
    Boolean,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin
from .user import UserPlan


class PlanConfiguration(Base, TimestampMixin):
    """
    Dynamic configuration for billing plans.
    Stores plan limits, features, and pricing in the database.
    """

    __tablename__ = "plan_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan identification
    plan_type = Column(
        SQLEnum(UserPlan, values_callable=lambda x: [e.value for e in x], native_enum=False), unique=True, nullable=False, index=True
    )
    plan_name = Column(String(50), nullable=False)  # free, pro, business
    display_name = Column(
        String(100), nullable=False
    )  # "Free Trial", "Pro Plan", etc.
    description = Column(String(500))
    tagline = Column(String(200))

    # Usage limits (stored as JSON for flexibility)
    limits = Column(JSON, nullable=False, default=dict)
    # Expected structure:
    # {
    #     "max_sessions": 10,
    #     "max_total_minutes": 120,
    #     "max_transcription_count": 20,
    #     "max_file_size_mb": 50,
    #     "export_formats": ["json", "txt"],
    #     "concurrent_processing": 1,
    #     "retention_days": 30
    # }

    # Features (stored as JSON for flexibility)
    features = Column(JSON, nullable=False, default=dict)
    # Expected structure:
    # {
    #     "priority_support": false,
    #     "team_collaboration": false,
    #     "api_access": false,
    #     "sso": false,
    #     "custom_branding": false
    # }

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
    color_scheme = Column(String(20), default="gray")  # gray, blue, purple
    sort_order = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)  # Hide plans without deleting

    # Additional data
    extra_data = Column(JSON, default=dict)
    # Can store additional info like:
    # {
    #     "stripe_product_id": "prod_xxx",
    #     "stripe_price_id_monthly": "price_xxx",
    #     "stripe_price_id_annual": "price_xxx",
    #     "promotional_discount": 0.2,
    #     "trial_days": 14
    # }

    def to_dict(self) -> dict:
        """Convert plan configuration to dictionary."""
        return {
            "id": str(self.id),
            "plan_type": self.plan_type.value,
            "plan_name": self.plan_name,
            "display_name": self.display_name,
            "description": self.description,
            "tagline": self.tagline,
            "limits": self.limits,
            "features": self.features,
            "pricing": {
                "monthly_usd": self.monthly_price_cents / 100,
                "annual_usd": self.annual_price_cents / 100,
                "monthly_twd": self.monthly_price_twd_cents / 100,
                "annual_twd": self.annual_price_twd_cents / 100,
                "currency": self.currency,
                "annual_discount_percentage": self._calculate_annual_discount(),
                "annual_savings_usd": self._calculate_annual_savings(),
            },
            "display": {
                "is_popular": self.is_popular,
                "is_enterprise": self.is_enterprise,
                "color_scheme": self.color_scheme,
                "sort_order": self.sort_order,
            },
            "is_active": self.is_active,
            "is_visible": self.is_visible,
            "extra_data": self.extra_data,
        }

    def _calculate_annual_discount(self) -> float:
        """Calculate annual discount percentage."""
        if self.monthly_price_cents == 0:
            return 0
        monthly_yearly = self.monthly_price_cents * 12
        annual_total = self.annual_price_cents * 12
        if monthly_yearly == 0:
            return 0
        return round((1 - (annual_total / monthly_yearly)) * 100, 1)

    def _calculate_annual_savings(self) -> float:
        """Calculate annual savings in USD."""
        monthly_yearly = self.monthly_price_cents * 12
        annual_total = self.annual_price_cents * 12
        return (monthly_yearly - annual_total) / 100

    def __repr__(self):
        return f"<PlanConfiguration(plan_type={self.plan_type}, display_name={self.display_name})>"


class SubscriptionHistory(Base, TimestampMixin):
    """
    Track user subscription changes and plan migrations.
    """

    __tablename__ = "subscription_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Plan change details
    old_plan = Column(SQLEnum(UserPlan, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=True)
    new_plan = Column(SQLEnum(UserPlan, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=False)

    # Change metadata
    change_type = Column(
        String(50), nullable=False
    )  # upgrade, downgrade, renewal, cancellation
    change_reason = Column(String(500))

    # Billing information
    amount_charged_cents = Column(Integer, default=0)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50))  # stripe, manual, promotion
    stripe_payment_intent_id = Column(String(255))

    # Proration details (for mid-cycle changes)
    is_prorated = Column(Boolean, default=False)
    prorated_amount_cents = Column(Integer, default=0)

    # Subscription period
    subscription_start = Column(String(50))  # ISO datetime string
    subscription_end = Column(String(50))  # ISO datetime string

    # Additional data
    extra_data = Column(JSON, default=dict)

    def __repr__(self):
        return f"<SubscriptionHistory(user_id={self.user_id}, old={self.old_plan}, new={self.new_plan})>"
