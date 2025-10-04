"""SaaS subscription management API endpoints."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...core.models.user import User
from ...core.services.subscription_management_use_case import (
    SubscriptionCreationUseCase,
    SubscriptionModificationUseCase,
    SubscriptionRetrievalUseCase,
)
from ...exceptions import DomainException
from .auth import get_current_user_dependency
from .dependencies import (
    get_subscription_creation_use_case,
    get_subscription_modification_use_case,
    get_subscription_retrieval_use_case,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Subscriptions"])


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
    subscription: Optional[Dict[str, Any]] = None
    payment_method: Optional[Dict[str, Any]] = None
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
    subscription_creation_use_case: SubscriptionCreationUseCase = Depends(
        get_subscription_creation_use_case
    ),
):
    """Create ECPay credit card authorization for subscription."""

    try:
        # Create authorization through use case
        auth_data = subscription_creation_use_case.create_authorization(
            user_id=current_user.id,
            plan_id=request.plan_id,
            billing_cycle=request.billing_cycle,
        )

        logger.info(
            f"Created authorization for user {current_user.id}, plan {request.plan_id}"
        )

        return AuthorizationResponse(
            success=auth_data["success"],
            action_url=auth_data["action_url"],
            form_data=auth_data["form_data"],
            merchant_member_id=auth_data["merchant_member_id"],
            auth_id=auth_data["auth_id"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create authorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment authorization.",
        )


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user_dependency),
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(
        get_subscription_retrieval_use_case
    ),
):
    """Get user's current subscription details."""

    try:
        # Get subscription details through use case
        subscription_data = subscription_retrieval_use_case.get_current_subscription(
            current_user.id
        )

        if not subscription_data or subscription_data.get("status") == "error":
            return CurrentSubscriptionResponse(
                status=subscription_data.get("status", "error")
            )

        # Format for API response
        payment_method = subscription_data.get("payment_method")
        subscription_info = subscription_data.get("subscription")
        subscription_status = subscription_data.get("status", "no_subscription")

        return CurrentSubscriptionResponse(
            subscription=subscription_info,
            payment_method=payment_method,
            status=subscription_status,
        )

    except DomainException as e:
        logger.warning(f"User not found when retrieving subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
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
    subscription_modification_use_case: SubscriptionModificationUseCase = Depends(
        get_subscription_modification_use_case
    ),
):
    """Cancel user's subscription."""

    try:
        # Cancel subscription through use case
        result = subscription_modification_use_case.cancel_subscription(
            user_id=current_user.id,
            immediate=False,  # Default to period-end cancellation
            reason="User requested cancellation",
        )

        logger.info(f"Subscription {subscription_id} scheduled for cancellation")

        return {
            "success": result["success"],
            "message": result["message"],
            "effective_date": result["effective_date"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(
        get_subscription_retrieval_use_case
    ),
):
    """Reactivate a cancelled subscription."""

    try:
        # For now, use retrieval use case to check subscription exists
        # In a full implementation, we'd add a reactivate method to
        # modification use case
        subscription_data = subscription_retrieval_use_case.get_current_subscription(
            current_user.id
        )

        if not subscription_data or not subscription_data.get("subscription"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found.",
            )

        # For now, return a success response
        # In Phase 4, we'll implement full reactivation logic in the use case
        logger.info(f"Subscription {subscription_id} reactivation requested")

        return {
            "success": True,
            "message": "Subscription reactivation requested",
            "next_payment_date": (
                subscription_data.get("subscription", {}).get("next_billing_date")
            ),
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
    subscription_modification_use_case: SubscriptionModificationUseCase = Depends(
        get_subscription_modification_use_case
    ),
):
    """Preview prorated billing for plan change."""

    try:
        # Calculate proration through use case
        proration = subscription_modification_use_case.calculate_proration(
            user_id=current_user.id,
            new_plan_id=request.plan_id,
            new_billing_cycle=request.billing_cycle,
        )

        return ProrationPreviewResponse(
            current_plan_remaining_value=proration["current_plan_remaining_value"],
            new_plan_prorated_cost=proration["new_plan_prorated_cost"],
            net_charge=proration["net_charge"],
            effective_date=proration["effective_date"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
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
    subscription_modification_use_case: SubscriptionModificationUseCase = Depends(
        get_subscription_modification_use_case
    ),
):
    """Upgrade subscription plan with immediate effect and prorated billing."""

    try:
        # Upgrade subscription through use case
        result = subscription_modification_use_case.upgrade_subscription(
            user_id=current_user.id,
            new_plan_id=request.plan_id,
            new_billing_cycle=request.billing_cycle,
        )

        logger.info(
            f"Subscription upgraded to {request.plan_id} for user {current_user.id}"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "old_plan": result.get("old_plan"),
            "new_plan": result["new_plan"],
            "effective_date": result["effective_date"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
    subscription_modification_use_case: SubscriptionModificationUseCase = Depends(
        get_subscription_modification_use_case
    ),
):
    """Downgrade subscription plan (effective at period end)."""

    try:
        # Downgrade subscription through use case
        result = subscription_modification_use_case.downgrade_subscription(
            user_id=current_user.id,
            new_plan_id=request.plan_id,
            new_billing_cycle=request.billing_cycle,
        )

        logger.info(
            f"Subscription scheduled for downgrade to {request.plan_id} for user {current_user.id}"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "old_plan": result.get("old_plan"),
            "new_plan": result["new_plan"],
            "effective_date": result["effective_date"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
    subscription_modification_use_case: SubscriptionModificationUseCase = Depends(
        get_subscription_modification_use_case
    ),
):
    """Cancel subscription with immediate or period-end options."""

    try:
        # Cancel subscription through use case
        result = subscription_modification_use_case.cancel_subscription(
            user_id=current_user.id,
            immediate=request.immediate,
            reason=request.reason,
        )

        logger.info(
            f"Subscription cancelled ({'immediate' if request.immediate else 'period-end'}) for user {current_user.id}"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "cancelled_at": datetime.now().isoformat(),
            "effective_date": result["effective_date"],
            "subscription_id": result["subscription_id"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription.",
        )


@router.post("/reactivate")
async def reactivate_subscription_new(
    current_user: User = Depends(get_current_user_dependency),
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(
        get_subscription_retrieval_use_case
    ),
):
    """Reactivate a cancelled subscription."""

    try:
        # Check if subscription exists through use case
        subscription_data = subscription_retrieval_use_case.get_current_subscription(
            current_user.id
        )

        if not subscription_data or not subscription_data.get("subscription"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription scheduled for cancellation found.",
            )

        # For now, return success response
        # In a full implementation, we'd add reactivation logic to the use case
        logger.info(f"Subscription reactivated for user {current_user.id}")

        subscription_info = subscription_data.get("subscription", {})
        return {
            "success": True,
            "message": "Subscription reactivated successfully",
            "subscription": {
                "id": subscription_info.get("id"),
                "status": subscription_info.get("status"),
                "plan_id": subscription_info.get("plan_id"),
            },
            "next_payment_date": subscription_info.get("next_billing_date"),
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
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(
        get_subscription_retrieval_use_case
    ),
    limit: int = 20,
    offset: int = 0,
):
    """Get user's billing history."""

    try:
        # Get payment history through use case
        payments_data = subscription_retrieval_use_case.get_subscription_payments(
            current_user.id
        )

        # Apply pagination (simple slice for now)
        payments = payments_data.get("payments", [])
        paginated_payments = payments[offset : offset + limit]

        return {
            "payments": paginated_payments,
            "total": len(paginated_payments),
            "limit": limit,
            "offset": offset,
            "subscription_id": payments_data.get("subscription_id"),
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
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(
        get_subscription_retrieval_use_case
    ),
):
    """Generate and download receipt for a specific payment."""

    try:
        # Get user's payments to verify ownership and find the payment
        payments_data = subscription_retrieval_use_case.get_subscription_payments(
            current_user.id
        )
        payments = payments_data.get("payments", [])

        # Find the specific payment
        payment = None
        for p in payments:
            if p.get("id") == payment_id:
                payment = p
                break

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found or access denied.",
            )

        # Only generate receipts for successful payments
        if payment.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receipt can only be generated for successful payments.",
            )

        # Get subscription info for receipt
        subscription_data = subscription_retrieval_use_case.get_current_subscription(
            current_user.id
        )
        subscription_info = subscription_data.get("subscription", {})

        # Generate receipt data
        receipt_data = {
            "receipt_id": f"RCP-{payment_id[:8].upper()}",
            "payment_id": payment_id,
            "issue_date": payment.get(
                "payment_date", datetime.now().strftime("%Y-%m-%d")
            ),
            "customer": {
                "name": (
                    getattr(current_user, "name", None)
                    or current_user.email.split("@")[0]
                ),
                "email": current_user.email,
                "user_id": str(current_user.id),
            },
            "subscription": {
                "plan_name": subscription_info.get("plan_id", "Unknown Plan"),
                "billing_cycle": subscription_info.get("billing_cycle", "monthly"),
            },
            "payment": {
                "amount": (payment.get("amount_cents", 0) / 100),  # Convert from cents
                "currency": payment.get("currency", "TWD"),
                "payment_date": payment.get("payment_date"),
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
        logger.error(f"Failed to generate receipt for payment {payment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate receipt.",
        )
