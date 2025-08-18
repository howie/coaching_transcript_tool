"""ECPay subscription models for SaaS billing system."""

import enum
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, DECIMAL, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel


class ECPayAuthStatus(enum.Enum):
    """ECPay authorization status."""
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"


class SubscriptionStatus(enum.Enum):
    """SaaS subscription status."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class PaymentStatus(enum.Enum):
    """Payment status for subscription payments."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class PeriodType(enum.Enum):
    """Billing period types."""
    MONTH = "Month"
    YEAR = "Year"


class ECPayCreditAuthorization(BaseModel):
    """ECPay credit card authorization for recurring payments."""
    
    __tablename__ = "ecpay_credit_authorizations"
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    
    # ECPay identification
    merchant_member_id = Column(String(30), unique=True, nullable=False, index=True)
    gwsr = Column(String(100), nullable=True)  # ECPay transaction number
    auth_code = Column(String(20), nullable=True)  # Authorization code
    
    # Authorization settings
    auth_amount = Column(Integer, nullable=False)  # Amount in TWD cents
    period_type = Column(String(10), nullable=False)  # 'Month' or 'Year'
    frequency = Column(Integer, default=1, nullable=False)
    period_amount = Column(Integer, nullable=False)  # Amount per period in TWD cents
    exec_times = Column(Integer, default=0, nullable=False)  # Times executed
    exec_times_limit = Column(Integer, nullable=True)  # Execution limit (null = unlimited)
    
    # Credit card information (masked)
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(20), nullable=True)  # VISA, MASTERCARD, JCB
    card_type = Column(String(20), nullable=True)
    
    # Status and timing
    auth_status = Column(String(20), default=ECPayAuthStatus.PENDING.value, nullable=False, index=True)
    auth_date = Column(DateTime(timezone=True), nullable=True)
    next_pay_date = Column(Date, nullable=True, index=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="ecpay_authorizations")
    subscriptions = relationship("SaasSubscription", back_populates="auth_record", lazy="dynamic")
    payments = relationship("SubscriptionPayment", back_populates="auth_record", lazy="dynamic")

    def __repr__(self):
        return f"<ECPayCreditAuthorization(user_id={self.user_id}, merchant_member_id={self.merchant_member_id}, status={self.auth_status})>"


class SaasSubscription(BaseModel):
    """SaaS subscription management."""
    
    __tablename__ = "saas_subscriptions"
    
    # User and authorization
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    auth_id = Column(UUID(as_uuid=True), ForeignKey("ecpay_credit_authorizations.id"), nullable=True)
    
    # Plan information
    plan_id = Column(String(20), nullable=False, index=True)  # FREE, PRO, ENTERPRISE
    plan_name = Column(String(50), nullable=False)
    billing_cycle = Column(String(10), nullable=False)  # monthly, annual
    
    # Pricing information
    amount_twd = Column(Integer, nullable=False)  # Amount in TWD cents
    currency = Column(String(3), default="TWD", nullable=False)
    
    # Subscription lifecycle
    status = Column(String(20), default=SubscriptionStatus.ACTIVE.value, nullable=False, index=True)
    current_period_start = Column(Date, nullable=False, index=True)
    current_period_end = Column(Date, nullable=False, index=True)
    
    # Cancellation settings
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Trial period (optional)
    trial_start = Column(Date, nullable=True)
    trial_end = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saas_subscriptions")
    auth_record = relationship("ECPayCreditAuthorization", back_populates="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription", lazy="dynamic")
    pending_changes = relationship("SubscriptionPendingChange", back_populates="subscription", lazy="dynamic")

    def __repr__(self):
        return f"<SaasSubscription(user_id={self.user_id}, plan_id={self.plan_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE.value
    
    @property
    def is_past_due(self) -> bool:
        """Check if subscription is past due."""
        return self.status == SubscriptionStatus.PAST_DUE.value
    
    @property
    def days_until_renewal(self) -> int:
        """Get days until next renewal."""
        if not self.current_period_end:
            return 0
        return (self.current_period_end - date.today()).days


class SubscriptionPayment(BaseModel):
    """Automatic subscription payment records."""
    
    __tablename__ = "subscription_payments"
    
    # Subscription and authorization
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("saas_subscriptions.id"), nullable=False, index=True)
    auth_id = Column(UUID(as_uuid=True), ForeignKey("ecpay_credit_authorizations.id"), nullable=True)
    
    # Payment information
    gwsr = Column(String(100), nullable=False, unique=True, index=True)  # ECPay transaction number
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="TWD", nullable=False)
    
    # Payment status
    status = Column(String(20), nullable=False, index=True)  # success, failed, pending
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Period information
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    
    # ECPay response
    ecpay_response = Column(JSON, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    subscription = relationship("SaasSubscription", back_populates="payments")
    auth_record = relationship("ECPayCreditAuthorization", back_populates="payments")

    def __repr__(self):
        return f"<SubscriptionPayment(gwsr={self.gwsr}, amount={self.amount}, status={self.status})>"


class SubscriptionPendingChange(BaseModel):
    """Pending subscription changes (e.g., downgrades effective at period end)."""
    
    __tablename__ = "subscription_pending_changes"
    
    # Subscription
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("saas_subscriptions.id"), nullable=False, index=True)
    
    # Change details
    new_plan_id = Column(String(20), nullable=False)
    new_billing_cycle = Column(String(10), nullable=False)
    new_amount_twd = Column(Integer, nullable=False)
    
    # Timing
    effective_date = Column(Date, nullable=False, index=True)
    change_type = Column(String(20), nullable=False)  # upgrade, downgrade, cancel
    
    # Status
    status = Column(String(20), default="pending", nullable=False)  # pending, applied, cancelled
    applied_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscription = relationship("SaasSubscription", back_populates="pending_changes")

    def __repr__(self):
        return f"<SubscriptionPendingChange(subscription_id={self.subscription_id}, new_plan={self.new_plan_id}, effective_date={self.effective_date})>"


class PaymentRetryAttempt(BaseModel):
    """Payment retry attempt tracking."""
    
    __tablename__ = "payment_retry_attempts"
    
    # Subscription and payment
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("saas_subscriptions.id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("subscription_payments.id"), nullable=True)
    
    # Retry information
    retry_attempt = Column(Integer, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Result
    success = Column(Boolean, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PaymentRetryAttempt(subscription_id={self.subscription_id}, attempt={self.retry_attempt}, success={self.success})>"


class GracePeriod(BaseModel):
    """Grace period tracking for failed payments."""
    
    __tablename__ = "grace_periods"
    
    # Subscription
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("saas_subscriptions.id"), nullable=False, index=True)
    
    # Grace period settings
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False, index=True)
    reason = Column(String(100), nullable=False)  # payment_failure, card_expired
    
    # Status
    status = Column(String(20), default="active", nullable=False)  # active, resolved, expired
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_type = Column(String(50), nullable=True)  # payment_success, manual_intervention, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<GracePeriod(subscription_id={self.subscription_id}, end_date={self.end_date}, status={self.status})>"