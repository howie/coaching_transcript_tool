"""ECPay webhook handlers for payment processing."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.services.ecpay_service import ECPaySubscriptionService
from ...core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/ecpay-auth")
async def handle_authorization_callback(
    MerchantID: str = Form(...),
    MerchantMemberID: str = Form(...),
    RtnCode: str = Form(...),
    RtnMsg: str = Form(...),
    gwsr: str = Form(None),
    AuthCode: str = Form(None),
    card4no: str = Form(None),  # Last 4 digits of card
    card6no: str = Form(None),  # Card brand
    CheckMacValue: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle ECPay credit card authorization callback."""
    
    logger.info(f"Received ECPay auth callback for {MerchantMemberID}")
    
    try:
        # Prepare callback data
        callback_data = {
            "MerchantID": MerchantID,
            "MerchantMemberID": MerchantMemberID,
            "RtnCode": RtnCode,
            "RtnMsg": RtnMsg,
            "CheckMacValue": CheckMacValue
        }
        
        # Add optional fields if present
        if gwsr:
            callback_data["gwsr"] = gwsr
        if AuthCode:
            callback_data["AuthCode"] = AuthCode
        if card4no:
            callback_data["card4no"] = card4no
        if card6no:
            callback_data["card6no"] = card6no
        
        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)
        
        # Process callback
        success = ecpay_service.handle_auth_callback(callback_data)
        
        if success:
            logger.info(f"Authorization callback processed successfully: {MerchantMemberID}")
            return "1|OK"  # ECPay expects this response format
        else:
            logger.error(f"Authorization callback processing failed: {MerchantMemberID}")
            return "0|Processing Failed"
            
    except Exception as e:
        logger.error(f"Error processing authorization callback: {e}")
        return "0|Internal Error"


@router.post("/ecpay-billing")
async def handle_billing_callback(
    MerchantID: str = Form(...),
    MerchantMemberID: str = Form(...),
    gwsr: str = Form(...),
    amount: str = Form(...),
    process_date: str = Form(...),
    auth_code: str = Form(...),
    RtnCode: str = Form(...),
    RtnMsg: str = Form(...),
    CheckMacValue: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle ECPay automatic billing callback."""
    
    logger.info(f"Received ECPay billing callback: {gwsr}")
    
    try:
        # Prepare webhook data
        webhook_data = {
            "MerchantID": MerchantID,
            "MerchantMemberID": MerchantMemberID,
            "gwsr": gwsr,
            "amount": amount,
            "process_date": process_date,
            "auth_code": auth_code,
            "RtnCode": RtnCode,
            "RtnMsg": RtnMsg,
            "CheckMacValue": CheckMacValue
        }
        
        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)
        
        # Process webhook
        success = ecpay_service.handle_payment_webhook(webhook_data)
        
        if success:
            logger.info(f"Billing webhook processed successfully: {gwsr}")
            return "1|OK"  # ECPay expects this response format
        else:
            logger.error(f"Billing webhook processing failed: {gwsr}")
            return "0|Processing Failed"
            
    except Exception as e:
        logger.error(f"Error processing billing webhook: {e}")
        return "0|Internal Error"


# Health check endpoint for webhook monitoring
@router.get("/health")
async def webhook_health_check():
    """Health check endpoint for webhook monitoring."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "service": "ecpay-webhooks"
    }