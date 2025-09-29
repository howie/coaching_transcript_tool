"""Subscription domain models with business rules."""

import enum
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Dict, Optional
from uuid import UUID


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


@dataclass
class ECPayCreditAuthorization:
    """Domain model for ECPay credit card authorization."""

    # Required fields first
    id: UUID
    user_id: UUID
    merchant_member_id: str
    auth_amount: int  # Amount in TWD cents
    period_type: str
    period_amount: int  # Amount per period in TWD cents
    auth_status: ECPayAuthStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    gwsr: Optional[str] = None
    auth_code: Optional[str] = None
    frequency: int = 1
    exec_times: int = 0
    exec_times_limit: Optional[int] = None
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    card_type: Optional[str] = None
    auth_date: Optional[datetime] = None
    next_pay_date: Optional[date] = None
    description: Optional[str] = None

    def is_active(self) -> bool:
        """Check if authorization is active."""
        return self.auth_status == ECPayAuthStatus.ACTIVE

    def is_valid_for_payment(self) -> bool:
        """Check if authorization can be used for payments."""
        return self.auth_status in [
            ECPayAuthStatus.ACTIVE,
            ECPayAuthStatus.PENDING,
        ]

    def get_amount_twd(self) -> float:
        """Get authorization amount in TWD dollars."""
        return self.auth_amount / 100.0

    def get_period_amount_twd(self) -> float:
        """Get period amount in TWD dollars."""
        return self.period_amount / 100.0


@dataclass
class SaasSubscription:
    """Domain model for SaaS subscription management."""

    # Required fields first
    id: UUID
    user_id: UUID
    plan_id: str
    plan_name: str
    billing_cycle: str
    amount_twd: int  # Amount in TWD cents
    status: SubscriptionStatus
    current_period_start: date
    current_period_end: date
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    auth_id: Optional[UUID] = None
    currency: str = "TWD"
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    trial_start: Optional[date] = None
    trial_end: Optional[date] = None
    grace_period_ends_at: Optional[datetime] = None
    downgraded_at: Optional[datetime] = None
    downgrade_reason: Optional[str] = None

    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE

    def is_past_due(self) -> bool:
        """Check if subscription is past due."""
        return self.status == SubscriptionStatus.PAST_DUE

    def is_in_trial(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING

    def days_until_renewal(self) -> int:
        """Get days until next renewal."""
        if not self.current_period_end:
            return 0
        return (self.current_period_end - date.today()).days

    def get_amount_twd(self) -> float:
        """Get subscription amount in TWD dollars."""
        return self.amount_twd / 100.0

    def is_renewable(self) -> bool:
        """Check if subscription can be renewed."""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE,
        ]

    def should_cancel_at_period_end(self) -> bool:
        """Check if subscription should be cancelled at period end."""
        return self.cancel_at_period_end and not self.cancelled_at


@dataclass
class SubscriptionPayment:
    """Domain model for subscription payment records."""

    # Required fields first
    id: UUID
    subscription_id: UUID
    gwsr: str  # ECPay transaction number
    amount: int  # Amount in cents
    status: PaymentStatus
    period_start: date
    period_end: date
    created_at: datetime

    # Optional fields with defaults
    auth_id: Optional[UUID] = None
    currency: str = "TWD"
    failure_reason: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    max_retries: int = 3
    last_retry_at: Optional[datetime] = None
    ecpay_response: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None

    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.SUCCESS

    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED

    def can_retry(self) -> bool:
        """Check if payment can be retried."""
        return (
            self.status == PaymentStatus.FAILED and self.retry_count < self.max_retries
        )

    def get_amount_twd(self) -> float:
        """Get payment amount in TWD dollars."""
        return self.amount / 100.0


@dataclass
class SubscriptionPendingChange:
    """Domain model for pending subscription changes."""

    # Required fields first
    id: UUID
    subscription_id: UUID
    new_plan_id: str
    new_billing_cycle: str
    new_amount_twd: int
    effective_date: date
    change_type: str  # upgrade, downgrade, cancel
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    status: str = "pending"  # pending, applied, cancelled
    applied_at: Optional[datetime] = None

    def is_pending(self) -> bool:
        """Check if change is pending."""
        return self.status == "pending"

    def is_applied(self) -> bool:
        """Check if change has been applied."""
        return self.status == "applied"

    def is_effective_today(self) -> bool:
        """Check if change is effective today."""
        return self.effective_date <= date.today()

    def is_upgrade(self) -> bool:
        """Check if change is an upgrade."""
        return self.change_type == "upgrade"

    def is_downgrade(self) -> bool:
        """Check if change is a downgrade."""
        return self.change_type == "downgrade"

    def get_new_amount_twd(self) -> float:
        """Get new amount in TWD dollars."""
        return self.new_amount_twd / 100.0


@dataclass
class WebhookLog:
    """Domain model for webhook processing logs."""

    # Required fields first
    id: UUID
    webhook_type: str
    method: str
    endpoint: str
    status: str
    received_at: datetime
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    source: str = "ecpay"
    headers: Optional[Dict[str, Any]] = None
    raw_body: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    response_body: Optional[str] = None
    user_id: Optional[UUID] = None
    subscription_id: Optional[UUID] = None
    payment_id: Optional[UUID] = None
    merchant_member_id: Optional[str] = None
    gwsr: Optional[str] = None
    rtn_code: Optional[str] = None
    check_mac_value_verified: Optional[bool] = None
    ip_address: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None

    def is_successful(self) -> bool:
        """Check if webhook was processed successfully."""
        return self.success is True

    def is_failed(self) -> bool:
        """Check if webhook processing failed."""
        return self.success is False

    def is_pending(self) -> bool:
        """Check if webhook is pending processing."""
        return self.success is None

    def can_retry(self) -> bool:
        """Check if webhook can be retried."""
        return self.is_failed() and self.retry_count < 5

    def mark_processing(self) -> None:
        """Mark webhook as processing."""
        self.status = "processing"
        self.processing_started_at = datetime.now(UTC)

    def mark_success(self, response_body: Optional[str] = None) -> None:
        """Mark webhook as successfully processed."""
        self.status = "success"
        self.success = True
        self.processing_completed_at = datetime.now(UTC)
        if response_body:
            self.response_body = response_body

    def mark_failed(self, error_message: str) -> None:
        """Mark webhook as failed."""
        self.status = "failed"
        self.success = False
        self.error_message = error_message
        self.processing_completed_at = datetime.now(UTC)
