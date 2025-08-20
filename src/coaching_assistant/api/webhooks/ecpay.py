"""ECPay webhook handlers for payment processing."""

import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, Form, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.services.ecpay_service import ECPaySubscriptionService
from ...core.config import settings
from ...models import WebhookLog, WebhookStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _create_webhook_log(
    request: Request,
    webhook_type: str,
    form_data: Dict[str, Any],
    db: Session
) -> WebhookLog:
    """Create initial webhook log entry."""
    
    webhook_log = WebhookLog(
        webhook_type=webhook_type,
        source="ecpay",
        method=request.method,
        endpoint=str(request.url),
        headers=dict(request.headers),
        form_data=form_data,
        merchant_member_id=form_data.get("MerchantMemberID"),
        gwsr=form_data.get("gwsr"),
        rtn_code=form_data.get("RtnCode"),
        ip_address=_get_client_ip(request),
        received_at=datetime.utcnow()
    )
    
    db.add(webhook_log)
    db.commit()
    return webhook_log


@router.post("/ecpay-auth")
async def handle_authorization_callback(
    request: Request,
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
    
    start_time = time.time()
    webhook_log = None
    
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
        
        # Create webhook log
        webhook_log = _create_webhook_log(request, "auth_callback", callback_data, db)
        webhook_log.mark_processing()
        db.commit()
        
        logger.info(f"🔵 Processing ECPay auth callback for {MerchantMemberID} (webhook_id: {webhook_log.id})")
        
        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)
        
        # Verify CheckMacValue
        mac_verified = ecpay_service._verify_callback(callback_data)
        webhook_log.check_mac_value_verified = mac_verified
        
        if not mac_verified:
            error_msg = f"CheckMacValue verification failed for {MerchantMemberID}"
            logger.error(f"❌ {error_msg}")
            webhook_log.mark_failed(error_msg)
            db.commit()
            return "0|Security Verification Failed"
        
        # Process callback
        success = ecpay_service.handle_auth_callback(callback_data)
        
        # Update user and subscription references in webhook log
        auth_record = db.query(ECPayCreditAuthorization).filter(
            ECPayCreditAuthorization.merchant_member_id == MerchantMemberID
        ).first()
        
        if auth_record:
            webhook_log.user_id = auth_record.user_id
            if auth_record.subscription:
                webhook_log.subscription_id = auth_record.subscription.id
        
        if success:
            response_msg = "1|OK"
            webhook_log.mark_success(response_msg)
            processing_time = round((time.time() - start_time) * 1000, 2)
            logger.info(f"✅ Authorization callback processed successfully: {MerchantMemberID} ({processing_time}ms)")
            db.commit()
            return response_msg
        else:
            error_msg = f"Authorization callback processing failed: {MerchantMemberID}"
            webhook_log.mark_failed(error_msg)
            logger.error(f"❌ {error_msg}")
            db.commit()
            return "0|Processing Failed"
            
    except Exception as e:
        error_msg = f"Error processing authorization callback: {str(e)}"
        logger.error(f"💥 {error_msg}")
        
        if webhook_log:
            webhook_log.mark_failed(error_msg)
            db.commit()
        
        return "0|Internal Error"


@router.post("/ecpay-billing")
async def handle_billing_callback(
    request: Request,
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
    
    start_time = time.time()
    webhook_log = None
    
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
        
        # Create webhook log
        webhook_log = _create_webhook_log(request, "billing_callback", webhook_data, db)
        webhook_log.mark_processing()
        db.commit()
        
        logger.info(f"🔵 Processing ECPay billing callback for {gwsr} (webhook_id: {webhook_log.id})")
        
        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)
        
        # Verify CheckMacValue
        mac_verified = ecpay_service._verify_callback(webhook_data)
        webhook_log.check_mac_value_verified = mac_verified
        
        if not mac_verified:
            error_msg = f"CheckMacValue verification failed for billing callback {gwsr}"
            logger.error(f"❌ {error_msg}")
            webhook_log.mark_failed(error_msg)
            db.commit()
            return "0|Security Verification Failed"
        
        # Find related subscription for logging
        auth_record = db.query(ECPayCreditAuthorization).filter(
            ECPayCreditAuthorization.merchant_member_id == MerchantMemberID
        ).first()
        
        if auth_record:
            webhook_log.user_id = auth_record.user_id
            subscription = db.query(SaasSubscription).filter(
                SaasSubscription.auth_id == auth_record.id
            ).first()
            if subscription:
                webhook_log.subscription_id = subscription.id
        
        # Process webhook
        success = ecpay_service.handle_payment_webhook(webhook_data)
        
        # Find payment record for logging
        if success:
            payment_record = db.query(SubscriptionPayment).filter(
                SubscriptionPayment.gwsr == gwsr
            ).order_by(SubscriptionPayment.created_at.desc()).first()
            if payment_record:
                webhook_log.payment_id = payment_record.id
        
        if success:
            response_msg = "1|OK"
            webhook_log.mark_success(response_msg)
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            # Enhanced logging for billing events
            payment_status = "SUCCESS" if RtnCode == "1" else "FAILED"
            logger.info(f"✅ Billing callback processed successfully: {gwsr} | Status: {payment_status} | Amount: {amount} | Processing: {processing_time}ms")
            
            db.commit()
            return response_msg
        else:
            error_msg = f"Billing webhook processing failed: {gwsr}"
            webhook_log.mark_failed(error_msg)
            logger.error(f"❌ {error_msg}")
            db.commit()
            return "0|Processing Failed"
            
    except Exception as e:
        error_msg = f"Error processing billing webhook: {str(e)}"
        logger.error(f"💥 {error_msg}")
        
        if webhook_log:
            webhook_log.mark_failed(error_msg)
            db.commit()
        
        return "0|Internal Error"


# Health check endpoint for webhook monitoring
@router.get("/health")
async def webhook_health_check(db: Session = Depends(get_db)):
    """Health check endpoint for webhook monitoring."""
    
    try:
        # Check recent webhook activity
        recent_webhooks = db.query(WebhookLog).filter(
            WebhookLog.received_at >= datetime.utcnow() - timedelta(minutes=30)
        ).count()
        
        # Check for failed webhooks
        failed_webhooks = db.query(WebhookLog).filter(
            WebhookLog.received_at >= datetime.utcnow() - timedelta(hours=24),
            WebhookLog.status == WebhookStatus.FAILED.value
        ).count()
        
        # Calculate success rate
        total_webhooks = db.query(WebhookLog).filter(
            WebhookLog.received_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        success_rate = 100.0
        if total_webhooks > 0:
            successful_webhooks = total_webhooks - failed_webhooks
            success_rate = (successful_webhooks / total_webhooks) * 100
        
        health_status = "healthy" if success_rate >= 95.0 else "degraded"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ecpay-webhooks",
            "metrics": {
                "recent_webhooks_30min": recent_webhooks,
                "failed_webhooks_24h": failed_webhooks,
                "total_webhooks_24h": total_webhooks,
                "success_rate_24h": round(success_rate, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ecpay-webhooks",
            "error": str(e)
        }


@router.get("/webhook-stats")
async def webhook_statistics(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get webhook statistics for monitoring."""
    
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Total webhooks by type
        webhook_stats = db.query(
            WebhookLog.webhook_type,
            WebhookLog.status,
            db.func.count(WebhookLog.id).label('count')
        ).filter(
            WebhookLog.received_at >= since
        ).group_by(
            WebhookLog.webhook_type,
            WebhookLog.status
        ).all()
        
        # Process statistics
        stats_summary = {}
        for webhook_type, status, count in webhook_stats:
            if webhook_type not in stats_summary:
                stats_summary[webhook_type] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "processing": 0
                }
            
            stats_summary[webhook_type]["total"] += count
            if status == WebhookStatus.SUCCESS.value:
                stats_summary[webhook_type]["success"] += count
            elif status == WebhookStatus.FAILED.value:
                stats_summary[webhook_type]["failed"] += count
            elif status == WebhookStatus.PROCESSING.value:
                stats_summary[webhook_type]["processing"] += count
        
        # Calculate success rates
        for webhook_type in stats_summary:
            total = stats_summary[webhook_type]["total"]
            if total > 0:
                success_rate = (stats_summary[webhook_type]["success"] / total) * 100
                stats_summary[webhook_type]["success_rate"] = round(success_rate, 2)
            else:
                stats_summary[webhook_type]["success_rate"] = 100.0
        
        return {
            "period_hours": hours,
            "generated_at": datetime.utcnow().isoformat(),
            "webhook_types": stats_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook statistics"
        )