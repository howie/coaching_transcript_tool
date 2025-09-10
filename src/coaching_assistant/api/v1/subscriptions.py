"""SaaS subscription management API endpoints."""

import logging
from typing import Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.auth import get_current_user_dependency
from ...core.services.ecpay_service import ECPaySubscriptionService
from ...core.config import settings
from ...models import (
    User,
    SaasSubscription,
    ECPayCreditAuthorization,
    SubscriptionPayment,
)
from ...models.ecpay_subscription import PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])


# Request/Response models
class CreateAuthorizationRequest(BaseModel):
    plan_id: str  # "PRO" or "ENTERPRISE"
    billing_cycle: str  # "monthly" or "annual"


class AuthorizationResponse(BaseModel):
    success: bool
    action_url: str
    form_data: Dict[str, Any]
    merchant_member_id: str
    auth_id: str


class CurrentSubscriptionResponse(BaseModel):
    subscription: Dict[str, Any] = None
    payment_method: Dict[str, Any] = None
    status: str = "no_subscription"


class UpgradeRequest(BaseModel):
    plan_id: str
    billing_cycle: str


class DowngradeRequest(BaseModel):
    plan_id: str
    billing_cycle: str


class CancelRequest(BaseModel):
    immediate: bool = False
    reason: str = None


class ProrationPreviewResponse(BaseModel):
    current_plan_remaining_value: int
    new_plan_prorated_cost: int
    net_charge: int
    effective_date: str


@router.post("/authorize", response_model=AuthorizationResponse)
async def create_authorization(
    request: CreateAuthorizationRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Create ECPay credit card authorization for subscription."""

    try:
        # Validate request
        if request.plan_id not in ["PRO", "ENTERPRISE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan_id. Must be PRO or ENTERPRISE.",
            )

        if request.billing_cycle not in ["monthly", "annual"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid billing_cycle. Must be monthly or annual.",
            )

        # Check if user already has active authorization
        existing_auth = (
            db.query(ECPayCreditAuthorization)
            .filter(
                ECPayCreditAuthorization.user_id == current_user.id,
                ECPayCreditAuthorization.auth_status == "active",
            )
            .first()
        )

        if existing_auth:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has active payment authorization.",
            )

        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)

        # Create authorization
        auth_data = ecpay_service.create_credit_authorization(
            user_id=str(current_user.id),
            plan_id=request.plan_id,
            billing_cycle=request.billing_cycle,
        )

        logger.info(
            f"Created authorization for user {current_user.id}, plan {request.plan_id}"
        )

        return AuthorizationResponse(
            success=True,
            action_url=auth_data["action_url"],
            form_data=auth_data["form_data"],
            merchant_member_id=auth_data["merchant_member_id"],
            auth_id=auth_data["auth_id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create authorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment authorization.",
        )


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Get user's current subscription details."""

    try:
        # Find active subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status.in_(["active", "past_due"]),
            )
            .first()
        )

        if not subscription:
            return CurrentSubscriptionResponse(status="no_subscription")

        # Get authorization details
        auth_record = subscription.auth_record
        payment_method = None

        if auth_record:
            payment_method = {
                "card_last4": auth_record.card_last4,
                "card_brand": auth_record.card_brand,
                "auth_status": auth_record.auth_status,
            }

        subscription_data = {
            "id": str(subscription.id),
            "plan_id": subscription.plan_id,
            "plan_name": subscription.plan_name,
            "billing_cycle": subscription.billing_cycle,
            "amount_twd": subscription.amount_twd,
            "currency": subscription.currency,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "next_payment_date": (
                auth_record.next_pay_date.isoformat()
                if auth_record and auth_record.next_pay_date
                else None
            ),
        }

        return CurrentSubscriptionResponse(
            subscription=subscription_data,
            payment_method=payment_method,
            status="active",
        )

    except Exception as e:
        logger.error(f"Failed to get current subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription information.",
        )


@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Cancel user's subscription."""

    try:
        # Find subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.id == subscription_id,
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active subscription not found.",
            )

        # Cancel at period end to avoid user loss
        subscription.cancel_at_period_end = True
        subscription.cancellation_reason = "User requested cancellation"

        db.commit()

        logger.info(
            f"Subscription {subscription_id} scheduled for cancellation"
        )

        return {
            "success": True,
            "message": "Subscription will be cancelled at period end",
            "effective_date": subscription.current_period_end.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription.",
        )


@router.post("/reactivate/{subscription_id}")
async def reactivate_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Reactivate a cancelled subscription."""

    try:
        # Find subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.id == subscription_id,
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.cancel_at_period_end == True,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cancelled subscription not found.",
            )

        # Reactivate subscription
        subscription.cancel_at_period_end = False
        subscription.cancellation_reason = None

        db.commit()

        logger.info(f"Subscription {subscription_id} reactivated")

        return {
            "success": True,
            "message": "Subscription reactivated successfully",
            "next_payment_date": subscription.current_period_end.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription.",
        )


@router.post("/preview-change", response_model=ProrationPreviewResponse)
async def preview_plan_change(
    request: UpgradeRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Preview prorated billing for plan change."""

    try:
        # Find current subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found.",
            )

        # Calculate proration
        ecpay_service = ECPaySubscriptionService(db, settings)
        proration = ecpay_service.calculate_prorated_charge(
            subscription, request.plan_id, request.billing_cycle
        )

        return ProrationPreviewResponse(**proration)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview plan change: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate proration preview.",
        )


@router.post("/upgrade")
async def upgrade_subscription(
    request: UpgradeRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Upgrade subscription plan with immediate effect and prorated billing."""

    try:
        # Validate request
        if request.plan_id not in ["PRO", "ENTERPRISE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan_id. Must be PRO or ENTERPRISE.",
            )

        # Find current subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found.",
            )

        # Check if it's actually an upgrade
        plan_hierarchy = {"PRO": 1, "ENTERPRISE": 2}
        current_level = plan_hierarchy.get(subscription.plan_id, 0)
        new_level = plan_hierarchy.get(request.plan_id, 0)

        if new_level <= current_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only upgrade to higher tier plans.",
            )

        # Perform upgrade
        ecpay_service = ECPaySubscriptionService(db, settings)
        result = ecpay_service.upgrade_subscription(
            subscription, request.plan_id, request.billing_cycle
        )

        logger.info(
            f"Subscription {subscription.id} upgraded to {request.plan_id}"
        )

        return {
            "success": True,
            "message": "Subscription upgraded successfully",
            "prorated_charge": result.get("prorated_charge", 0),
            "effective_date": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upgrade subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade subscription.",
        )


@router.post("/downgrade")
async def downgrade_subscription(
    request: DowngradeRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Downgrade subscription plan (effective at period end)."""

    try:
        # Validate request
        if request.plan_id not in ["FREE", "PRO", "ENTERPRISE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan_id.",
            )

        # Find current subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found.",
            )

        # Check if it's actually a downgrade
        plan_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        current_level = plan_hierarchy.get(subscription.plan_id, 0)
        new_level = plan_hierarchy.get(request.plan_id, 0)

        if new_level >= current_level:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only downgrade to lower tier plans.",
            )

        # Schedule downgrade for period end
        ecpay_service = ECPaySubscriptionService(db, settings)
        result = ecpay_service.schedule_downgrade(
            subscription, request.plan_id, request.billing_cycle
        )

        logger.info(
            f"Subscription {subscription.id} scheduled for downgrade to {request.plan_id}"
        )

        return {
            "success": True,
            "message": "Downgrade scheduled for period end",
            "effective_date": subscription.current_period_end.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to downgrade subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule downgrade.",
        )


@router.post("/cancel")
async def cancel_subscription_new(
    request: CancelRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Cancel subscription with immediate or period-end options."""

    try:
        # Find active subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found.",
            )

        # Perform cancellation
        ecpay_service = ECPaySubscriptionService(db, settings)
        result = ecpay_service.cancel_subscription(
            subscription, request.immediate, request.reason
        )

        logger.info(
            f"Subscription {subscription.id} cancelled ({'immediate' if request.immediate else 'period-end'})"
        )

        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "cancelled_at": datetime.now().isoformat(),
            "effective_date": result["effective_date"],
            "refund_amount": result.get("refund_amount", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription.",
        )


@router.post("/reactivate")
async def reactivate_subscription_new(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Reactivate a cancelled subscription."""

    try:
        # Find subscription scheduled for cancellation
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.cancel_at_period_end == True,
                SaasSubscription.status == "active",
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription scheduled for cancellation found.",
            )

        # Reactivate subscription
        subscription.cancel_at_period_end = False
        subscription.cancellation_reason = None

        db.commit()

        logger.info(f"Subscription {subscription.id} reactivated")

        return {
            "success": True,
            "message": "Subscription reactivated successfully",
            "subscription": {
                "id": str(subscription.id),
                "status": subscription.status,
                "plan_id": subscription.plan_id,
            },
            "next_payment_date": subscription.current_period_end.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription.",
        )


@router.get("/billing-history")
async def get_billing_history(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """Get user's billing history."""

    try:
        # Get all payments for user's subscriptions
        payments = (
            db.query(SubscriptionPayment)
            .join(
                SaasSubscription,
                SubscriptionPayment.subscription_id == SaasSubscription.id,
            )
            .filter(SaasSubscription.user_id == current_user.id)
            .order_by(SubscriptionPayment.processed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        payment_data = []
        for payment in payments:
            payment_data.append(
                {
                    "id": str(payment.id),
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "period_start": payment.period_start.isoformat(),
                    "period_end": payment.period_end.isoformat(),
                    "processed_at": (
                        payment.processed_at.isoformat()
                        if payment.processed_at
                        else None
                    ),
                    "failure_reason": payment.failure_reason,
                    "retry_count": payment.retry_count,
                }
            )

        return {
            "payments": payment_data,
            "total": len(payment_data),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to get billing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing history.",
        )


@router.get("/payment/{payment_id}/receipt")
async def generate_payment_receipt(
    payment_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Generate and download receipt for a specific payment."""

    try:
        # Find the payment
        payment = (
            db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.id == payment_id)
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found.",
            )

        # Find the associated subscription to verify ownership
        subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.id == payment.subscription_id,
                SaasSubscription.user_id == current_user.id,
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Payment does not belong to current user.",
            )

        # Only generate receipts for successful payments
        if payment.status != PaymentStatus.SUCCESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt can only be generated for successful payments.",
            )

        # Generate receipt data
        receipt_data = {
            "receipt_id": f"RCP-{str(payment.id)[:8].upper()}",
            "payment_id": str(payment.id),
            "issue_date": (
                payment.processed_at.strftime("%Y-%m-%d")
                if payment.processed_at
                else date.today().strftime("%Y-%m-%d")
            ),
            "customer": {
                "name": current_user.name or current_user.email.split("@")[0],
                "email": current_user.email,
                "user_id": str(current_user.id),
            },
            "subscription": {
                "plan_name": subscription.plan_name,
                "billing_cycle": subscription.billing_cycle,
                "period_start": payment.period_start.strftime("%Y-%m-%d"),
                "period_end": payment.period_end.strftime("%Y-%m-%d"),
            },
            "payment": {
                "amount": payment.amount / 100,  # Convert from cents
                "currency": payment.currency,
                "payment_date": (
                    payment.processed_at.strftime("%Y-%m-%d %H:%M:%S")
                    if payment.processed_at
                    else None
                ),
                "payment_method": "信用卡 (ECPay)",
            },
            "company": {
                "name": "Coaching Transcript Tool",
                "address": "台灣",
                "tax_id": "統一編號待補",
                "website": "https://coaching-transcript-tool.com",
            },
        }

        return {"receipt": receipt_data, "status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to generate receipt for payment {payment_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate receipt.",
        )
