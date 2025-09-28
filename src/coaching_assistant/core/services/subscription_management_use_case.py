"""Subscription management use cases for Clean Architecture.

This module contains business logic for subscription creation, management, and billing
operations. All external dependencies are injected through repository ports.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from numbers import Number
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ...exceptions import DomainException
from ..models.subscription import (
    ECPayAuthStatus,
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionStatus,
)
from ..models.user import UserPlan
from ..repositories.ports import (
    PlanConfigurationRepoPort,
    SubscriptionRepoPort,
    UserRepoPort,
)

logger = logging.getLogger(__name__)


def _resolve_plan_identifier(plan_id: str) -> UserPlan:
    """Resolve arbitrary plan identifiers to UserPlan enum values.

    Accepts plan identifiers regardless of case or common formatting variations
    (such as hyphens vs underscores) and raises ValueError for unknown plans.
    """
    if not isinstance(plan_id, str):
        raise ValueError(f"Invalid plan_id: {plan_id}")

    normalized = plan_id.strip()
    if not normalized:
        raise ValueError("plan_id cannot be empty")

    # Allow both enum values (lowercase) and names (uppercase) as input
    variants = [normalized, normalized.lower(), normalized.replace("-", "_")]

    for candidate in variants:
        try:
            return UserPlan(candidate)
        except ValueError:
            continue

    # Try matching against enum member names (e.g. PRO, COACHING_SCHOOL)
    try:
        return UserPlan[normalized.replace("-", "_").upper()]
    except KeyError as exc:
        raise ValueError(f"Invalid plan_id: {plan_id}") from exc


def _extract_plan_amount_cents(plan_config: Any, billing_cycle: str) -> int:
    """Return plan price in cents for the requested billing cycle.

    Supports both the newer nested `PlanConfiguration.pricing` dataclass and legacy
    flat attributes that may still be used in mocks or fixtures.
    """

    normalized_cycle = billing_cycle.lower()
    if normalized_cycle not in {"monthly", "annual"}:
        raise ValueError("Invalid billing cycle. Must be monthly or annual.")

    def _read_price(target: Any, field_name: str) -> Optional[int]:
        if not hasattr(target, field_name):
            return None
        raw_value = getattr(target, field_name)
        if isinstance(raw_value, Number):
            return int(raw_value)
        return None

    twd_field = f"{normalized_cycle}_price_twd_cents"
    usd_field = f"{normalized_cycle}_price_cents"

    amount = _read_price(plan_config, twd_field)
    if amount is None:
        pricing = getattr(plan_config, "pricing", None)
        if pricing is not None:
            amount = _read_price(pricing, twd_field)
    if amount is None:
        amount = _read_price(plan_config, usd_field)
    if amount is None:
        pricing = getattr(plan_config, "pricing", None)
        if pricing is not None:
            amount = _read_price(pricing, usd_field)

    if amount is None:
        raise ValueError(
            f"Pricing configuration missing for {plan_config.plan_type.value} {normalized_cycle}"
        )

    return amount


class SubscriptionCreationUseCase:
    """Use case for creating credit card authorizations and subscriptions."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepoPort,
        user_repo: UserRepoPort,
        plan_config_repo: PlanConfigurationRepoPort,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo
        self.plan_config_repo = plan_config_repo

    def create_authorization(
        self,
        user_id: UUID,
        plan_id: str,
        billing_cycle: str,
    ) -> Dict[str, Any]:
        """Create ECPay credit card authorization for subscription.

        Args:
            user_id: User ID
            plan_id: Plan identifier (STUDENT, PRO, ENTERPRISE)
            billing_cycle: Billing cycle (monthly, annual)

        Returns:
            Dictionary with authorization details

        Raises:
            ValueError: If user not found or invalid parameters
            DomainException: If user already has active authorization
        """
        # Validate user
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise DomainException(f"User not found: {user_id}")

        # Validate plan and billing cycle using relaxed case handling
        try:
            resolved_plan_type = _resolve_plan_identifier(plan_id)
        except ValueError as exc:
            raise ValueError(
                "Invalid plan_id. Must be a known subscription plan."
            ) from exc

        if resolved_plan_type not in {
            UserPlan.STUDENT,
            UserPlan.PRO,
            UserPlan.ENTERPRISE,
            UserPlan.COACHING_SCHOOL,
        }:
            raise ValueError(
                "Invalid plan_id. Must be STUDENT, PRO, ENTERPRISE or COACHING_SCHOOL."
            )

        normalized_billing = billing_cycle.lower()
        if normalized_billing not in ["monthly", "annual"]:
            raise ValueError("Invalid billing_cycle. Must be monthly or annual.")
        billing_cycle = normalized_billing

        # Check if user already has active authorization
        existing_auth = self.subscription_repo.get_credit_authorization_by_user_id(
            user_id
        )
        if existing_auth and existing_auth.auth_status == ECPayAuthStatus.ACTIVE:
            raise DomainException(
                "User already has an active credit card authorization"
            )

        # Create new authorization
        auth_id = f"AUTH_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        merchant_member_id = f"MEMBER_{user_id}"

        authorization = ECPayCreditAuthorization(
            id=uuid4(),
            user_id=user_id,
            merchant_member_id=merchant_member_id,
            auth_amount=100,  # 1 TWD for authorization
            period_type="Month",
            frequency=1,
            period_amount=0,  # Will be set later based on plan
            auth_status=ECPayAuthStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved_auth = self.subscription_repo.save_credit_authorization(authorization)

        # Generate ECPay form data (this would typically call ECPay service)
        form_data = self._generate_ecpay_form_data(
            saved_auth, plan_id=resolved_plan_type.value
        )

        return {
            "success": True,
            "action_url": ("https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"),
            "form_data": form_data,
            "merchant_member_id": merchant_member_id,
            "auth_id": auth_id,
        }

    def create_subscription(
        self,
        user_id: UUID,
        authorization_id: UUID,
        plan_id: str,
        billing_cycle: str,
    ) -> SaasSubscription:
        """Create subscription after successful authorization.

        Args:
            user_id: User ID
            authorization_id: Authorization ID
            plan_id: Plan identifier
            billing_cycle: Billing cycle

        Returns:
            Created subscription

        Raises:
            ValueError: If authorization not found or invalid
            DomainException: If user already has active subscription
        """
        # Validate authorization
        authorization = self.subscription_repo.get_credit_authorization_by_user_id(
            user_id
        )
        if not authorization or authorization.id != authorization_id:
            raise ValueError("Authorization not found or invalid")

        if authorization.auth_status != ECPayAuthStatus.ACTIVE:
            raise ValueError("Authorization is not active")

        # Check for existing active subscription
        existing_subscription = self.subscription_repo.get_subscription_by_user_id(
            user_id
        )
        if (
            existing_subscription
            and existing_subscription.status == SubscriptionStatus.ACTIVE
        ):
            raise DomainException("User already has an active subscription")

        # Get plan configuration for pricing
        try:
            plan_type = _resolve_plan_identifier(plan_id)
        except ValueError as exc:
            raise ValueError(f"Invalid plan_id: {plan_id}") from exc

        plan_config = self.plan_config_repo.get_by_plan_type(plan_type)
        if not plan_config:
            raise ValueError(f"Plan configuration not found for: {plan_id}")

        # Calculate subscription details
        # Map billing cycle to actual price fields
        normalized_billing = billing_cycle.lower()
        amount_cents = _extract_plan_amount_cents(plan_config, normalized_billing)

        if amount_cents <= 0:
            raise ValueError(f"Invalid pricing for {plan_id} {billing_cycle}")

        # Create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=user_id,
            plan_id=plan_type.value,
            plan_name=f"{plan_id} Plan",
            billing_cycle=normalized_billing,
            status=SubscriptionStatus.ACTIVE,
            amount_twd=amount_cents,
            currency="TWD",
            auth_id=authorization_id,
            current_period_start=datetime.utcnow().date(),
            current_period_end=self._calculate_next_billing_date(normalized_billing),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved_subscription = self.subscription_repo.save_subscription(subscription)

        # Update user plan
        self.user_repo.update_plan(user_id, plan_type)

        return saved_subscription

    def _generate_ecpay_form_data(
        self,
        authorization: ECPayCreditAuthorization,
        plan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate ECPay form data for authorization."""
        # This would typically call the ECPay service to generate proper form data
        # For now, return mock data structure
        plan_label = plan_id or "subscription"
        return {
            "MerchantID": "Mock_Merchant_ID",
            "MerchantTradeNo": authorization.merchant_member_id,
            "PaymentType": "aio",
            "TotalAmount": "1",  # Minimal amount for authorization
            "TradeDesc": f"Credit card authorization for {plan_label}",
            "ItemName": f"Authorization for {plan_label} plan",
            "ReturnURL": "https://your-domain.com/api/webhooks/ecpay/return",
            "ChoosePayment": "Credit",
            "EncryptType": "1",
        }

    def _calculate_next_billing_date(self, billing_cycle: str) -> date:
        """Calculate next billing date based on cycle."""
        now = datetime.utcnow().date()

        if billing_cycle == "monthly":
            # Add one month
            if now.month == 12:
                return date(now.year + 1, 1, now.day)
            else:
                return date(now.year, now.month + 1, now.day)
        elif billing_cycle == "annual":
            # Add one year
            return date(now.year + 1, now.month, now.day)
        else:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}")


class SubscriptionRetrievalUseCase:
    """Use case for retrieving subscription information."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepoPort,
        user_repo: UserRepoPort,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo

    def get_current_subscription(self, user_id: UUID) -> Dict[str, Any]:
        """Get current subscription for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with subscription and payment method info
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise DomainException(f"User not found: {user_id}")

            # Isolate subscription queries with explicit error handling
            subscription = None
            try:
                subscription = self.subscription_repo.get_subscription_by_user_id(
                    user_id
                )
            except Exception as e:
                logger.error(f"Failed to get subscription for user {user_id}: {e}")
                # Continue with None subscription - this is recoverable

            authorization = None
            try:
                authorization = (
                    self.subscription_repo.get_credit_authorization_by_user_id(user_id)
                )
            except Exception as e:
                logger.error(f"Failed to get authorization for user {user_id}: {e}")
                # Continue with None authorization - this is recoverable

            if not subscription:
                return {
                    "subscription": None,
                    "payment_method": None,
                    "status": "no_subscription",
                }

            subscription_data = {
                "id": str(subscription.id),
                "plan_id": subscription.plan_id,
                "billing_cycle": subscription.billing_cycle,
                "status": (
                    subscription.status.value
                    if hasattr(subscription.status, "value")
                    else str(subscription.status)
                ),
                "amount_cents": getattr(subscription, "amount_twd", 0),
                "currency": subscription.currency,
                "created_at": subscription.created_at.isoformat(),
                "next_billing_date": (
                    subscription.current_period_end.isoformat()
                    if subscription.current_period_end
                    else None
                ),
            }

            payment_method_data = None
            if authorization:
                payment_method_data = {
                    "auth_id": authorization.merchant_member_id,
                    "auth_status": (
                        authorization.auth_status.value
                        if hasattr(authorization.auth_status, "value")
                        else str(authorization.auth_status)
                    ),
                    "created_at": authorization.created_at.isoformat(),
                }

            return {
                "subscription": subscription_data,
                "payment_method": payment_method_data,
                "status": (
                    subscription.status.value
                    if hasattr(subscription.status, "value")
                    else str(subscription.status)
                ),
            }

        except Exception as e:
            logger.error(
                f"Critical error in get_current_subscription for user {user_id}: {e}"
            )
            # Return safe fallback response
            return {
                "subscription": None,
                "payment_method": None,
                "status": "error",
            }

    def get_subscription_payments(self, user_id: UUID) -> Dict[str, Any]:
        """Get payment history for user's subscription.

        Args:
            user_id: User ID

        Returns:
            Dictionary with payment history
        """
        subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
        if not subscription:
            return {"payments": [], "total": 0}

        payments = self.subscription_repo.get_payments_for_subscription(subscription.id)

        payment_data = [
            {
                "id": str(payment.id),
                "amount_cents": getattr(payment, "amount_twd", 0),
                "currency": payment.currency,
                "status": payment.status.value,
                "payment_date": (
                    payment.payment_date.isoformat() if payment.payment_date else None
                ),
                "ecpay_trade_no": payment.ecpay_trade_no,
                "created_at": payment.created_at.isoformat(),
            }
            for payment in payments
        ]

        return {
            "payments": payment_data,
            "total": len(payment_data),
            "subscription_id": str(subscription.id),
        }


class SubscriptionModificationUseCase:
    """Use case for modifying subscriptions (upgrade, downgrade, cancel)."""

    def __init__(
        self,
        subscription_repo: SubscriptionRepoPort,
        user_repo: UserRepoPort,
        plan_config_repo: PlanConfigurationRepoPort,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo
        self.plan_config_repo = plan_config_repo

    def upgrade_subscription(
        self,
        user_id: UUID,
        new_plan_id: str,
        new_billing_cycle: str,
    ) -> Dict[str, Any]:
        """Upgrade user's subscription to a higher tier.

        Args:
            user_id: User ID
            new_plan_id: New plan identifier
            new_billing_cycle: New billing cycle

        Returns:
            Dictionary with upgrade result
        """
        return self._modify_subscription(
            user_id, new_plan_id, new_billing_cycle, "upgrade"
        )

    def downgrade_subscription(
        self,
        user_id: UUID,
        new_plan_id: str,
        new_billing_cycle: str,
    ) -> Dict[str, Any]:
        """Downgrade user's subscription to a lower tier.

        Args:
            user_id: User ID
            new_plan_id: New plan identifier
            new_billing_cycle: New billing cycle

        Returns:
            Dictionary with downgrade result
        """
        return self._modify_subscription(
            user_id, new_plan_id, new_billing_cycle, "downgrade"
        )

    def cancel_subscription(
        self,
        user_id: UUID,
        immediate: bool = False,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel user's subscription.

        Args:
            user_id: User ID
            immediate: Whether to cancel immediately or at end of billing period
            reason: Cancellation reason

        Returns:
            Dictionary with cancellation result
        """
        subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
        if not subscription:
            raise ValueError("No active subscription found")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise DomainException("Subscription is not active")

        # Update subscription status
        if immediate:
            new_status = SubscriptionStatus.CANCELLED
            updated_subscription = self.subscription_repo.update_subscription_status(
                subscription.id, new_status
            )
        else:
            # Schedule cancellation at period end: keep ACTIVE status and mark
            # flag if available
            try:
                # Directly mark cancel_at_period_end flag when repository does
                # not expose a method
                subscription.cancel_at_period_end = True
                updated_subscription = self.subscription_repo.save_subscription(
                    subscription
                )  # type: ignore[attr-defined]
            except Exception:
                # Fallback: leave status ACTIVE without flag if repository
                # lacks save method
                updated_subscription = subscription

        # If immediate cancellation, update user plan to FREE
        if immediate:
            self.user_repo.update_plan(user_id, UserPlan.FREE)

        return {
            "success": True,
            "subscription_id": str(updated_subscription.id),
            "status": (
                updated_subscription.status.value
                if hasattr(updated_subscription.status, "value")
                else updated_subscription.status
            ),
            "effective_date": (
                "immediate"
                if immediate
                else (
                    getattr(
                        updated_subscription, "current_period_end", None
                    ).isoformat()
                    if getattr(updated_subscription, "current_period_end", None)
                    else "period_end"
                )
            ),
            "message": (
                f"Subscription {'canceled' if immediate else 'scheduled for cancellation'}"
            ),
        }

    def _modify_subscription(
        self,
        user_id: UUID,
        new_plan_id: str,
        new_billing_cycle: str,
        operation: str,
    ) -> Dict[str, Any]:
        """Internal method for subscription modifications."""
        subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
        if not subscription:
            raise ValueError("No active subscription found")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise DomainException("Subscription is not active")

        # Validate new plan (handle case-insensitive plan_id)
        try:
            new_plan_type = _resolve_plan_identifier(new_plan_id)
        except ValueError as exc:
            raise ValueError(f"Invalid plan_id: {new_plan_id}") from exc

        new_plan_config = self.plan_config_repo.get_by_plan_type(new_plan_type)
        if not new_plan_config:
            raise ValueError(f"Plan configuration not found for: {new_plan_id}")

        # Calculate new pricing
        # Map billing cycle to actual price fields
        normalized_cycle = new_billing_cycle.lower()
        new_amount_cents = _extract_plan_amount_cents(new_plan_config, normalized_cycle)

        # Validate pricing based on plan type
        if new_amount_cents < 0:
            raise ValueError(
                f"Invalid pricing configuration for {new_plan_id} "
                f"{new_billing_cycle}: negative amount"
            )

        # FREE plan should have 0 amount, which is valid
        if new_plan_type == UserPlan.FREE:
            if new_amount_cents != 0:
                logger.warning(
                    f"FREE plan has non-zero amount: {new_amount_cents}, setting to 0"
                )
                new_amount_cents = 0
        elif new_amount_cents == 0:
            raise ValueError(
                f"Paid plan {new_plan_id} cannot have zero pricing for "
                f"{new_billing_cycle} billing cycle"
            )

        # Update subscription
        previous_plan_id = subscription.plan_id
        subscription.plan_id = new_plan_type.value  # Use the enum value (lowercase)
        subscription.billing_cycle = normalized_cycle
        subscription.amount_twd = new_amount_cents
        subscription.updated_at = datetime.utcnow()

        updated_subscription = self.subscription_repo.save_subscription(subscription)

        # Update user plan
        self.user_repo.update_plan(user_id, new_plan_type)

        return {
            "success": True,
            "subscription_id": str(updated_subscription.id),
            "old_plan": previous_plan_id,
            "new_plan": new_plan_type.value,
            "requested_plan": new_plan_id,
            "operation": operation,
            "effective_date": "immediate",
            "message": f"Subscription {operation}d successfully",
        }

    def calculate_proration(
        self,
        user_id: UUID,
        new_plan_id: str,
        new_billing_cycle: str,
    ) -> Dict[str, Any]:
        """Calculate proration for subscription change.

        Args:
            user_id: User ID
            new_plan_id: New plan identifier
            new_billing_cycle: New billing cycle

        Returns:
            Dictionary with proration calculation
        """
        subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
        if not subscription:
            raise ValueError("No active subscription found")

        # Get new plan pricing
        try:
            new_plan_type = _resolve_plan_identifier(new_plan_id)
        except ValueError as exc:
            raise ValueError(f"Invalid plan_id: {new_plan_id}") from exc

        new_plan_config = self.plan_config_repo.get_by_plan_type(new_plan_type)
        if not new_plan_config:
            raise ValueError(f"Plan configuration not found for: {new_plan_id}")

        # Map billing cycle to actual price fields
        normalized_cycle = new_billing_cycle.lower()
        new_amount_cents = _extract_plan_amount_cents(new_plan_config, normalized_cycle)

        # Calculate remaining value of current subscription
        # This is a simplified calculation - in practice, you'd need more
        # complex logic
        current_amount = getattr(subscription, "amount_twd", 0)
        remaining_days = (
            subscription.current_period_end - datetime.utcnow().date()
        ).days
        billing_period_days = 30 if subscription.billing_cycle == "monthly" else 365

        remaining_value = int((current_amount * remaining_days) / billing_period_days)
        net_charge = max(0, new_amount_cents - remaining_value)

        return {
            "current_plan_remaining_value": remaining_value,
            "new_plan_prorated_cost": new_amount_cents,
            "net_charge": net_charge,
            "effective_date": datetime.utcnow().date().isoformat(),
        }
