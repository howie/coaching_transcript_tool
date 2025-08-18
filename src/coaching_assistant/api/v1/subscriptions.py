"""SaaS subscription management API endpoints."""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.auth import get_current_user_dependency
from ...core.services.ecpay_service import ECPaySubscriptionService
from ...core.config import settings
from ...models import User, SaasSubscription, ECPayCreditAuthorization

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


@router.post("/authorize", response_model=AuthorizationResponse)
async def create_authorization(
    request: CreateAuthorizationRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create ECPay credit card authorization for subscription."""
    
    try:
        # Validate request
        if request.plan_id not in ["PRO", "ENTERPRISE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan_id. Must be PRO or ENTERPRISE."
            )
        
        if request.billing_cycle not in ["monthly", "annual"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid billing_cycle. Must be monthly or annual."
            )
        
        # Check if user already has active authorization
        existing_auth = db.query(ECPayCreditAuthorization).filter(
            ECPayCreditAuthorization.user_id == current_user.id,
            ECPayCreditAuthorization.auth_status == "active"
        ).first()
        
        if existing_auth:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has active payment authorization."
            )
        
        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)
        
        # Create authorization
        auth_data = ecpay_service.create_credit_authorization(
            user_id=str(current_user.id),
            plan_id=request.plan_id,
            billing_cycle=request.billing_cycle
        )
        
        logger.info(f"Created authorization for user {current_user.id}, plan {request.plan_id}")
        
        return AuthorizationResponse(
            success=True,
            action_url=auth_data["action_url"],
            form_data=auth_data["form_data"],
            merchant_member_id=auth_data["merchant_member_id"],
            auth_id=auth_data["auth_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create authorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment authorization."
        )


@router.get("/current", response_model=CurrentSubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get user's current subscription details."""
    
    try:
        # Find active subscription
        subscription = db.query(SaasSubscription).filter(
            SaasSubscription.user_id == current_user.id,
            SaasSubscription.status.in_(["active", "past_due"])
        ).first()
        
        if not subscription:
            return CurrentSubscriptionResponse(status="no_subscription")
        
        # Get authorization details
        auth_record = subscription.auth_record
        payment_method = None
        
        if auth_record:
            payment_method = {
                "card_last4": auth_record.card_last4,
                "card_brand": auth_record.card_brand,
                "auth_status": auth_record.auth_status
            }
        
        subscription_data = {
            "id": str(subscription.id),
            "plan_id": subscription.plan_id,
            "plan_name": subscription.plan_name,
            "billing_cycle": subscription.billing_cycle,
            "amount": subscription.amount_twd,
            "currency": subscription.currency,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "next_payment_date": auth_record.next_pay_date.isoformat() if auth_record and auth_record.next_pay_date else None
        }
        
        return CurrentSubscriptionResponse(
            subscription=subscription_data,
            payment_method=payment_method,
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Failed to get current subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription information."
        )


@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Cancel user's subscription."""
    
    try:
        # Find subscription
        subscription = db.query(SaasSubscription).filter(
            SaasSubscription.id == subscription_id,
            SaasSubscription.user_id == current_user.id,
            SaasSubscription.status == "active"
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active subscription not found."
            )
        
        # Cancel at period end to avoid user loss
        subscription.cancel_at_period_end = True
        subscription.cancellation_reason = "User requested cancellation"
        
        db.commit()
        
        logger.info(f"Subscription {subscription_id} scheduled for cancellation")
        
        return {
            "success": True,
            "message": "Subscription will be cancelled at period end",
            "effective_date": subscription.current_period_end.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription."
        )


@router.post("/reactivate/{subscription_id}")
async def reactivate_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Reactivate a cancelled subscription."""
    
    try:
        # Find subscription
        subscription = db.query(SaasSubscription).filter(
            SaasSubscription.id == subscription_id,
            SaasSubscription.user_id == current_user.id,
            SaasSubscription.cancel_at_period_end == True,
            SaasSubscription.status == "active"
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cancelled subscription not found."
            )
        
        # Reactivate subscription
        subscription.cancel_at_period_end = False
        subscription.cancellation_reason = None
        
        db.commit()
        
        logger.info(f"Subscription {subscription_id} reactivated")
        
        return {
            "success": True,
            "message": "Subscription reactivated successfully",
            "next_payment_date": subscription.current_period_end.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription."
        )