"""Subscription ORM models with domain model conversion."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from ....core.models.subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionPendingChange,
    SubscriptionStatus,
    WebhookLog,
)
from .base import BaseModel


class ECPayCreditAuthorizationModel(BaseModel):
    """ORM model for ECPay credit card authorization."""

    __tablename__ = "ecpay_credit_authorizations"

    # User association
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )

    # ECPay identification
    merchant_member_id = Column(String(30), unique=True, nullable=False, index=True)
    gwsr = Column(String(100), nullable=True)
    auth_code = Column(String(20), nullable=True)

    # Authorization settings
    auth_amount = Column(Integer, nullable=False)  # Amount in TWD cents
    period_type = Column(String(10), nullable=False)  # 'Month' or 'Year'
    frequency = Column(Integer, default=1, nullable=False)
    period_amount = Column(Integer, nullable=False)  # Amount per period in TWD cents
    exec_times = Column(Integer, default=0, nullable=False)
    exec_times_limit = Column(Integer, nullable=True)

    # Credit card information (masked)
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(20), nullable=True)
    card_type = Column(String(20), nullable=True)

    # Status and timing
    auth_status = Column(
        SQLEnum(ECPayAuthStatus, values_callable=lambda x: [e.value for e in x]),
        default=ECPayAuthStatus.PENDING,
        nullable=False,
        index=True,
    )
    auth_date = Column(DateTime(timezone=True), nullable=True)
    next_pay_date = Column(Date, nullable=True, index=True)

    # Metadata
    description = Column(Text, nullable=True)

    def to_domain(self) -> ECPayCreditAuthorization:
        """Convert ORM model to domain model."""
        return ECPayCreditAuthorization(
            id=self.id,
            user_id=self.user_id,
            merchant_member_id=self.merchant_member_id,
            gwsr=self.gwsr,
            auth_code=self.auth_code,
            auth_amount=self.auth_amount,
            period_type=self.period_type,
            frequency=self.frequency,
            period_amount=self.period_amount,
            exec_times=self.exec_times,
            exec_times_limit=self.exec_times_limit,
            card_last4=self.card_last4,
            card_brand=self.card_brand,
            card_type=self.card_type,
            auth_status=self.auth_status,
            auth_date=self.auth_date,
            next_pay_date=self.next_pay_date,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(
        cls, auth: ECPayCreditAuthorization
    ) -> "ECPayCreditAuthorizationModel":
        """Create ORM model from domain model."""
        return cls(
            id=auth.id,
            user_id=auth.user_id,
            merchant_member_id=auth.merchant_member_id,
            gwsr=auth.gwsr,
            auth_code=auth.auth_code,
            auth_amount=auth.auth_amount,
            period_type=auth.period_type,
            frequency=auth.frequency,
            period_amount=auth.period_amount,
            exec_times=auth.exec_times,
            exec_times_limit=auth.exec_times_limit,
            card_last4=auth.card_last4,
            card_brand=auth.card_brand,
            card_type=auth.card_type,
            auth_status=auth.auth_status,
            auth_date=auth.auth_date,
            next_pay_date=auth.next_pay_date,
            description=auth.description,
            created_at=auth.created_at,
            updated_at=auth.updated_at,
        )

    def update_from_domain(self, auth: ECPayCreditAuthorization) -> None:
        """Update ORM model from domain model."""
        self.merchant_member_id = auth.merchant_member_id
        self.gwsr = auth.gwsr
        self.auth_code = auth.auth_code
        self.auth_amount = auth.auth_amount
        self.period_type = auth.period_type
        self.frequency = auth.frequency
        self.period_amount = auth.period_amount
        self.exec_times = auth.exec_times
        self.exec_times_limit = auth.exec_times_limit
        self.card_last4 = auth.card_last4
        self.card_brand = auth.card_brand
        self.card_type = auth.card_type
        self.auth_status = auth.auth_status
        self.auth_date = auth.auth_date
        self.next_pay_date = auth.next_pay_date
        self.description = auth.description
        self.updated_at = auth.updated_at


class SaasSubscriptionModel(BaseModel):
    """ORM model for SaaS subscription management."""

    __tablename__ = "saas_subscriptions"

    # User and authorization
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    auth_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ecpay_credit_authorizations.id"),
        nullable=True,
    )

    # Plan information
    plan_id = Column(String(20), nullable=False, index=True)
    plan_name = Column(String(50), nullable=False)
    billing_cycle = Column(String(10), nullable=False)

    # Pricing information
    amount_twd = Column(Integer, nullable=False)  # Amount in TWD cents
    currency = Column(String(3), default="TWD", nullable=False)

    # Subscription lifecycle
    status = Column(
        SQLEnum(SubscriptionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    current_period_start = Column(Date, nullable=False, index=True)
    current_period_end = Column(Date, nullable=False, index=True)

    # Cancellation settings
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Trial period (optional)
    trial_start = Column(Date, nullable=True)
    trial_end = Column(Date, nullable=True)

    # Grace period and downgrade tracking
    grace_period_ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    downgraded_at = Column(DateTime(timezone=True), nullable=True)
    downgrade_reason = Column(String(50), nullable=True)

    def to_domain(self) -> SaasSubscription:
        """Convert ORM model to domain model."""
        return SaasSubscription(
            id=self.id,
            user_id=self.user_id,
            auth_id=self.auth_id,
            plan_id=self.plan_id,
            plan_name=self.plan_name,
            billing_cycle=self.billing_cycle,
            amount_twd=self.amount_twd,
            currency=self.currency,
            status=self.status,
            current_period_start=self.current_period_start,
            current_period_end=self.current_period_end,
            cancel_at_period_end=self.cancel_at_period_end,
            cancelled_at=self.cancelled_at,
            cancellation_reason=self.cancellation_reason,
            trial_start=self.trial_start,
            trial_end=self.trial_end,
            grace_period_ends_at=self.grace_period_ends_at,
            downgraded_at=self.downgraded_at,
            downgrade_reason=self.downgrade_reason,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, subscription: SaasSubscription) -> "SaasSubscriptionModel":
        """Create ORM model from domain model."""
        return cls(
            id=subscription.id,
            user_id=subscription.user_id,
            auth_id=subscription.auth_id,
            plan_id=subscription.plan_id,
            plan_name=subscription.plan_name,
            billing_cycle=subscription.billing_cycle,
            amount_twd=subscription.amount_twd,
            currency=subscription.currency,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            cancelled_at=subscription.cancelled_at,
            cancellation_reason=subscription.cancellation_reason,
            trial_start=subscription.trial_start,
            trial_end=subscription.trial_end,
            grace_period_ends_at=subscription.grace_period_ends_at,
            downgraded_at=subscription.downgraded_at,
            downgrade_reason=subscription.downgrade_reason,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    def update_from_domain(self, subscription: SaasSubscription) -> None:
        """Update ORM model from domain model."""
        self.auth_id = subscription.auth_id
        self.plan_id = subscription.plan_id
        self.plan_name = subscription.plan_name
        self.billing_cycle = subscription.billing_cycle
        self.amount_twd = subscription.amount_twd
        self.currency = subscription.currency
        self.status = subscription.status
        self.current_period_start = subscription.current_period_start
        self.current_period_end = subscription.current_period_end
        self.cancel_at_period_end = subscription.cancel_at_period_end
        self.cancelled_at = subscription.cancelled_at
        self.cancellation_reason = subscription.cancellation_reason
        self.trial_start = subscription.trial_start
        self.trial_end = subscription.trial_end
        self.grace_period_ends_at = subscription.grace_period_ends_at
        self.downgraded_at = subscription.downgraded_at
        self.downgrade_reason = subscription.downgrade_reason
        self.updated_at = subscription.updated_at


class SubscriptionPaymentModel(BaseModel):
    """ORM model for subscription payment records."""

    __tablename__ = "subscription_payments"

    # Subscription and authorization
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_subscriptions.id"),
        nullable=False,
        index=True,
    )
    auth_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ecpay_credit_authorizations.id"),
        nullable=True,
    )

    # Payment information
    gwsr = Column(String(100), nullable=False, unique=True, index=True)
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="TWD", nullable=False)

    # Payment status
    status = Column(
        SQLEnum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Retry management
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    max_retries = Column(Integer, default=3, nullable=True)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Period information
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)

    # ECPay response
    ecpay_response = Column(JSON, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def to_domain(self) -> SubscriptionPayment:
        """Convert ORM model to domain model."""
        return SubscriptionPayment(
            id=self.id,
            subscription_id=self.subscription_id,
            auth_id=self.auth_id,
            gwsr=self.gwsr,
            amount=self.amount,
            currency=self.currency,
            status=self.status,
            failure_reason=self.failure_reason,
            retry_count=self.retry_count,
            next_retry_at=self.next_retry_at,
            max_retries=self.max_retries,
            last_retry_at=self.last_retry_at,
            period_start=self.period_start,
            period_end=self.period_end,
            ecpay_response=self.ecpay_response,
            processed_at=self.processed_at,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, payment: SubscriptionPayment) -> "SubscriptionPaymentModel":
        """Create ORM model from domain model."""
        return cls(
            id=payment.id,
            subscription_id=payment.subscription_id,
            auth_id=payment.auth_id,
            gwsr=payment.gwsr,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            failure_reason=payment.failure_reason,
            retry_count=payment.retry_count,
            next_retry_at=payment.next_retry_at,
            max_retries=payment.max_retries,
            last_retry_at=payment.last_retry_at,
            period_start=payment.period_start,
            period_end=payment.period_end,
            ecpay_response=payment.ecpay_response,
            processed_at=payment.processed_at,
            created_at=payment.created_at,
        )

    def update_from_domain(self, payment: SubscriptionPayment) -> None:
        """Update ORM model from domain model."""
        self.status = payment.status
        self.failure_reason = payment.failure_reason
        self.retry_count = payment.retry_count
        self.next_retry_at = payment.next_retry_at
        self.max_retries = payment.max_retries
        self.last_retry_at = payment.last_retry_at
        self.ecpay_response = payment.ecpay_response
        self.processed_at = payment.processed_at


class SubscriptionPendingChangeModel(BaseModel):
    """ORM model for pending subscription changes."""

    __tablename__ = "subscription_pending_changes"

    # Subscription
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_subscriptions.id"),
        nullable=False,
        index=True,
    )

    # Change details
    new_plan_id = Column(String(20), nullable=False)
    new_billing_cycle = Column(String(10), nullable=False)
    new_amount_twd = Column(Integer, nullable=False)

    # Timing
    effective_date = Column(Date, nullable=False, index=True)
    change_type = Column(String(20), nullable=False)  # upgrade, downgrade, cancel

    # Status
    status = Column(String(20), default="pending", nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> SubscriptionPendingChange:
        """Convert ORM model to domain model."""
        return SubscriptionPendingChange(
            id=self.id,
            subscription_id=self.subscription_id,
            new_plan_id=self.new_plan_id,
            new_billing_cycle=self.new_billing_cycle,
            new_amount_twd=self.new_amount_twd,
            effective_date=self.effective_date,
            change_type=self.change_type,
            status=self.status,
            applied_at=self.applied_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(
        cls, change: SubscriptionPendingChange
    ) -> "SubscriptionPendingChangeModel":
        """Create ORM model from domain model."""
        return cls(
            id=change.id,
            subscription_id=change.subscription_id,
            new_plan_id=change.new_plan_id,
            new_billing_cycle=change.new_billing_cycle,
            new_amount_twd=change.new_amount_twd,
            effective_date=change.effective_date,
            change_type=change.change_type,
            status=change.status,
            applied_at=change.applied_at,
            created_at=change.created_at,
            updated_at=change.updated_at,
        )

    def update_from_domain(self, change: SubscriptionPendingChange) -> None:
        """Update ORM model from domain model."""
        self.new_plan_id = change.new_plan_id
        self.new_billing_cycle = change.new_billing_cycle
        self.new_amount_twd = change.new_amount_twd
        self.effective_date = change.effective_date
        self.change_type = change.change_type
        self.status = change.status
        self.applied_at = change.applied_at
        self.updated_at = change.updated_at


class WebhookLogModel(BaseModel):
    """ORM model for webhook processing logs."""

    __tablename__ = "webhook_logs"

    # Webhook details
    webhook_type = Column(String(50), nullable=False, index=True)
    source = Column(String(50), default="ecpay", nullable=False)

    # Request information
    method = Column(String(10), default="POST", nullable=False)
    endpoint = Column(String(255), nullable=False)
    headers = Column(JSON, nullable=True)
    raw_body = Column(Text, nullable=True)
    form_data = Column(JSON, nullable=True)

    # Processing information
    status = Column(String(20), default="received", nullable=False, index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Result
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)

    # Related entities
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_subscriptions.id"),
        nullable=True,
        index=True,
    )
    payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_payments.id"),
        nullable=True,
        index=True,
    )

    # ECPay specific fields
    merchant_member_id = Column(String(30), nullable=True, index=True)
    gwsr = Column(String(30), nullable=True, index=True)
    rtn_code = Column(String(10), nullable=True)

    # Security verification
    check_mac_value_verified = Column(Boolean, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Retry information
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    received_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    def to_domain(self) -> WebhookLog:
        """Convert ORM model to domain model."""
        return WebhookLog(
            id=self.id,
            webhook_type=self.webhook_type,
            source=self.source,
            method=self.method,
            endpoint=self.endpoint,
            headers=self.headers,
            raw_body=self.raw_body,
            form_data=self.form_data,
            status=self.status,
            processing_started_at=self.processing_started_at,
            processing_completed_at=self.processing_completed_at,
            success=self.success,
            error_message=self.error_message,
            response_body=self.response_body,
            user_id=self.user_id,
            subscription_id=self.subscription_id,
            payment_id=self.payment_id,
            merchant_member_id=self.merchant_member_id,
            gwsr=self.gwsr,
            rtn_code=self.rtn_code,
            check_mac_value_verified=self.check_mac_value_verified,
            ip_address=self.ip_address,
            retry_count=self.retry_count,
            next_retry_at=self.next_retry_at,
            received_at=self.received_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, webhook: WebhookLog) -> "WebhookLogModel":
        """Create ORM model from domain model."""
        return cls(
            id=webhook.id,
            webhook_type=webhook.webhook_type,
            source=webhook.source,
            method=webhook.method,
            endpoint=webhook.endpoint,
            headers=webhook.headers,
            raw_body=webhook.raw_body,
            form_data=webhook.form_data,
            status=webhook.status,
            processing_started_at=webhook.processing_started_at,
            processing_completed_at=webhook.processing_completed_at,
            success=webhook.success,
            error_message=webhook.error_message,
            response_body=webhook.response_body,
            user_id=webhook.user_id,
            subscription_id=webhook.subscription_id,
            payment_id=webhook.payment_id,
            merchant_member_id=webhook.merchant_member_id,
            gwsr=webhook.gwsr,
            rtn_code=webhook.rtn_code,
            check_mac_value_verified=webhook.check_mac_value_verified,
            ip_address=webhook.ip_address,
            retry_count=webhook.retry_count,
            next_retry_at=webhook.next_retry_at,
            received_at=webhook.received_at,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
        )

    def update_from_domain(self, webhook: WebhookLog) -> None:
        """Update ORM model from domain model."""
        self.status = webhook.status
        self.processing_started_at = webhook.processing_started_at
        self.processing_completed_at = webhook.processing_completed_at
        self.success = webhook.success
        self.error_message = webhook.error_message
        self.response_body = webhook.response_body
        self.retry_count = webhook.retry_count
        self.next_retry_at = webhook.next_retry_at
        self.updated_at = webhook.updated_at
