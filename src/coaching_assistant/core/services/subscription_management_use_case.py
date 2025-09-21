"""Subscription management use cases for Clean Architecture.

This module contains business logic for subscription creation, management, and billing
operations. All external dependencies are injected through repository ports.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal

from ..repositories.ports import (
    SubscriptionRepoPort,
    UserRepoPort,
    PlanConfigurationRepoPort,
)
from ..models.user import User, UserPlan
from ..models.subscription import (
    SaasSubscription,
    SubscriptionPayment,
    ECPayCreditAuthorization,
    SubscriptionStatus,
    PaymentStatus,
    ECPayAuthStatus,
)
from ...exceptions import DomainException

logger = logging.getLogger(__name__)


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

        # Validate plan and billing cycle
        if plan_id not in ["STUDENT", "PRO", "ENTERPRISE"]:
            raise ValueError("Invalid plan_id. Must be STUDENT, PRO or ENTERPRISE.")
        
        if billing_cycle not in ["monthly", "annual"]:
            raise ValueError("Invalid billing_cycle. Must be monthly or annual.")

        # Check if user already has active authorization
        existing_auth = self.subscription_repo.get_credit_authorization_by_user_id(user_id)
        if existing_auth and existing_auth.auth_status == ECPayAuthStatus.ACTIVE:
            raise DomainException("User already has an active credit card authorization")

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
        )

        saved_auth = self.subscription_repo.save_credit_authorization(authorization)

        # Generate ECPay form data (this would typically call ECPay service)
        form_data = self._generate_ecpay_form_data(saved_auth)

        return {
            "success": True,
            "action_url": "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5",
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
        authorization = self.subscription_repo.get_credit_authorization_by_user_id(user_id)
        if not authorization or authorization.id != authorization_id:
            raise ValueError("Authorization not found or invalid")

        if authorization.auth_status != ECPayAuthStatus.ACTIVE:
            raise ValueError("Authorization is not active")

        # Check for existing active subscription
        existing_subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
        if existing_subscription and existing_subscription.status == SubscriptionStatus.ACTIVE:
            raise DomainException("User already has an active subscription")

        # Get plan configuration for pricing
        try:
            plan_type = UserPlan(plan_id)
        except ValueError:
            raise ValueError(f"Invalid plan_id: {plan_id}")

        plan_config = self.plan_config_repo.get_by_plan_type(plan_type)
        if not plan_config:
            raise ValueError(f"Plan configuration not found for: {plan_id}")

        # Calculate subscription details
        # Map billing cycle to actual price fields
        if billing_cycle == "monthly":
            amount_cents = plan_config.monthly_price_twd_cents
        elif billing_cycle == "annual":
            amount_cents = plan_config.annual_price_twd_cents
        else:
            amount_cents = 0
        
        if amount_cents <= 0:
            raise ValueError(f"Invalid pricing for {plan_id} {billing_cycle}")

        # Create subscription
        subscription = SaasSubscription(
            id=uuid4(),
            user_id=user_id,
            plan_id=plan_id,
            plan_name=f"{plan_id} Plan",
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.ACTIVE,
            amount_twd=amount_cents,
            currency="TWD",
            auth_id=authorization_id,
            current_period_start=datetime.utcnow().date(),
            current_period_end=self._calculate_next_billing_date(billing_cycle),
            created_at=datetime.utcnow(),
        )

        saved_subscription = self.subscription_repo.save_subscription(subscription)

        # Update user plan
        self.user_repo.update_plan(user_id, plan_type)

        return saved_subscription

    def _generate_ecpay_form_data(self, authorization: ECPayCreditAuthorization) -> Dict[str, Any]:
        """Generate ECPay form data for authorization."""
        # This would typically call the ECPay service to generate proper form data
        # For now, return mock data structure
        return {
            "MerchantID": "Mock_Merchant_ID",
            "MerchantTradeNo": authorization.merchant_member_id,
            "PaymentType": "aio",
            "TotalAmount": "1",  # Minimal amount for authorization
            "TradeDesc": f"Credit card authorization for {authorization.plan_id}",
            "ItemName": f"Authorization for {authorization.plan_id} plan",
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
                subscription = self.subscription_repo.get_subscription_by_user_id(user_id)
            except Exception as e:
                logger.error(f"Failed to get subscription for user {user_id}: {e}")
                # Continue with None subscription - this is recoverable

            authorization = None
            try:
                authorization = self.subscription_repo.get_credit_authorization_by_user_id(user_id)
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
                "status": subscription.status.value if hasattr(subscription.status, 'value') else str(subscription.status),
                "amount_cents": getattr(subscription, 'amount_twd', 0),
                "currency": subscription.currency,
                "created_at": subscription.created_at.isoformat(),
                "next_billing_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            }

            payment_method_data = None
            if authorization:
                payment_method_data = {
                    "auth_id": authorization.merchant_member_id,
                    "auth_status": authorization.auth_status.value if hasattr(authorization.auth_status, 'value') else str(authorization.auth_status),
                    "created_at": authorization.created_at.isoformat(),
                }

            return {
                "subscription": subscription_data,
                "payment_method": payment_method_data,
                "status": subscription.status.value if hasattr(subscription.status, 'value') else str(subscription.status),
            }

        except Exception as e:
            logger.error(f"Critical error in get_current_subscription for user {user_id}: {e}")
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
                "amount_cents": getattr(payment, 'amount_twd', 0),
                "currency": payment.currency,
                "status": payment.status.value,
                "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
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
        return self._modify_subscription(user_id, new_plan_id, new_billing_cycle, "upgrade")

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
        return self._modify_subscription(user_id, new_plan_id, new_billing_cycle, "downgrade")

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
            # Schedule cancellation at period end: keep ACTIVE status and mark flag if available
            try:
                # Directly mark cancel_at_period_end flag when repository does not expose a method
                subscription.cancel_at_period_end = True
                updated_subscription = self.subscription_repo.save_subscription(subscription)  # type: ignore[attr-defined]
            except Exception:
                # Fallback: leave status ACTIVE without flag if repository lacks save method
                updated_subscription = subscription

        # If immediate cancellation, update user plan to FREE
        if immediate:
            self.user_repo.update_plan(user_id, UserPlan.FREE)

        return {
            "success": True,
            "subscription_id": str(updated_subscription.id),
            "status": updated_subscription.status.value if hasattr(updated_subscription.status, "value") else updated_subscription.status,
            "effective_date": "immediate" if immediate else (getattr(updated_subscription, "current_period_end", None).isoformat() if getattr(updated_subscription, "current_period_end", None) else "period_end"),
            "message": f"Subscription {'canceled' if immediate else 'scheduled for cancellation'}",
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

        # Validate new plan
        try:
            new_plan_type = UserPlan(new_plan_id)
        except ValueError:
            raise ValueError(f"Invalid plan_id: {new_plan_id}")

        new_plan_config = self.plan_config_repo.get_by_plan_type(new_plan_type)
        if not new_plan_config:
            raise ValueError(f"Plan configuration not found for: {new_plan_id}")

        # Calculate new pricing
        # Map billing cycle to actual price fields
        if new_billing_cycle == "monthly":
            new_amount_cents = new_plan_config.monthly_price_twd_cents
        elif new_billing_cycle == "annual":
            new_amount_cents = new_plan_config.annual_price_twd_cents
        else:
            new_amount_cents = 0

        if new_amount_cents <= 0:
            raise ValueError(f"Invalid pricing for {new_plan_id} {new_billing_cycle}")

        # Update subscription
        subscription.plan_id = new_plan_id
        subscription.billing_cycle = new_billing_cycle
        subscription.amount_twd = new_amount_cents
        subscription.updated_at = datetime.utcnow()

        updated_subscription = self.subscription_repo.save_subscription(subscription)

        # Update user plan
        self.user_repo.update_plan(user_id, new_plan_type)

        return {
            "success": True,
            "subscription_id": str(updated_subscription.id),
            "old_plan": subscription.plan_id,
            "new_plan": new_plan_id,
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
            new_plan_type = UserPlan(new_plan_id)
        except ValueError:
            raise ValueError(f"Invalid plan_id: {new_plan_id}")

        new_plan_config = self.plan_config_repo.get_by_plan_type(new_plan_type)
        if not new_plan_config:
            raise ValueError(f"Plan configuration not found for: {new_plan_id}")

        # Map billing cycle to actual price fields
        if new_billing_cycle == "monthly":
            new_amount_cents = new_plan_config.monthly_price_twd_cents
        elif new_billing_cycle == "annual":
            new_amount_cents = new_plan_config.annual_price_twd_cents
        else:
            new_amount_cents = 0

        # Calculate remaining value of current subscription
        # This is a simplified calculation - in practice, you'd need more complex logic
        current_amount = getattr(subscription, 'amount_twd', 0)
        remaining_days = (subscription.current_period_end - datetime.utcnow().date()).days
        billing_period_days = 30 if subscription.billing_cycle == "monthly" else 365
        
        remaining_value = int((current_amount * remaining_days) / billing_period_days)
        net_charge = max(0, new_amount_cents - remaining_value)

        return {
            "current_plan_remaining_value": remaining_value,
            "new_plan_prorated_cost": new_amount_cents,
            "net_charge": net_charge,
            "effective_date": datetime.utcnow().date().isoformat(),
        }
