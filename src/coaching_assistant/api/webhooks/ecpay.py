"""ECPay webhook handlers for payment processing."""

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.services.ecpay_service import ECPaySubscriptionService
from ...models import (
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionPayment,
    WebhookLog,
    WebhookStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _create_webhook_log(
    request: Request, webhook_type: str, form_data: Dict[str, Any], db: Session
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
        received_at=datetime.now(UTC),
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
    db: Session = Depends(get_db),
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
            "CheckMacValue": CheckMacValue,
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

        logger.info(
            f"🔵 Processing ECPay auth callback for {MerchantMemberID} (webhook_id: {webhook_log.id})"
        )

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
        auth_record = (
            db.query(ECPayCreditAuthorization)
            .filter(ECPayCreditAuthorization.merchant_member_id == MerchantMemberID)
            .first()
        )

        if auth_record:
            webhook_log.user_id = auth_record.user_id
            if auth_record.subscription:
                webhook_log.subscription_id = auth_record.subscription.id

        if success:
            response_msg = "1|OK"
            webhook_log.mark_success(response_msg)
            processing_time = round((time.time() - start_time) * 1000, 2)
            logger.info(
                f"✅ Authorization callback processed successfully: "
                f"{MerchantMemberID} ({processing_time}ms)"
            )
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
    db: Session = Depends(get_db),
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
            "CheckMacValue": CheckMacValue,
        }

        # Create webhook log
        webhook_log = _create_webhook_log(request, "billing_callback", webhook_data, db)
        webhook_log.mark_processing()
        db.commit()

        logger.info(
            f"🔵 Processing ECPay billing callback for {gwsr} (webhook_id: {webhook_log.id})"
        )

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
        auth_record = (
            db.query(ECPayCreditAuthorization)
            .filter(ECPayCreditAuthorization.merchant_member_id == MerchantMemberID)
            .first()
        )

        if auth_record:
            webhook_log.user_id = auth_record.user_id
            subscription = (
                db.query(SaasSubscription)
                .filter(SaasSubscription.auth_id == auth_record.id)
                .first()
            )
            if subscription:
                webhook_log.subscription_id = subscription.id

        # Process webhook
        success = ecpay_service.handle_payment_webhook(webhook_data)

        # Find payment record for logging
        if success:
            payment_record = (
                db.query(SubscriptionPayment)
                .filter(SubscriptionPayment.gwsr == gwsr)
                .order_by(SubscriptionPayment.created_at.desc())
                .first()
            )
            if payment_record:
                webhook_log.payment_id = payment_record.id

        if success:
            response_msg = "1|OK"
            webhook_log.mark_success(response_msg)
            processing_time = round((time.time() - start_time) * 1000, 2)

            # Enhanced logging for billing events
            payment_status = "SUCCESS" if RtnCode == "1" else "FAILED"
            logger.info(
                f"✅ Billing callback processed successfully: {gwsr} | "
                f"Status: {payment_status} | Amount: {amount} | "
                f"Processing: {processing_time}ms"
            )

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
        recent_webhooks = (
            db.query(WebhookLog)
            .filter(WebhookLog.received_at >= datetime.now(UTC) - timedelta(minutes=30))
            .count()
        )

        # Check for failed webhooks
        failed_webhooks = (
            db.query(WebhookLog)
            .filter(
                WebhookLog.received_at >= datetime.now(UTC) - timedelta(hours=24),
                WebhookLog.status == WebhookStatus.FAILED.value,
            )
            .count()
        )

        # Calculate success rate
        total_webhooks = (
            db.query(WebhookLog)
            .filter(WebhookLog.received_at >= datetime.now(UTC) - timedelta(hours=24))
            .count()
        )

        success_rate = 100.0
        if total_webhooks > 0:
            successful_webhooks = total_webhooks - failed_webhooks
            success_rate = (successful_webhooks / total_webhooks) * 100

        health_status = "healthy" if success_rate >= 95.0 else "degraded"

        return {
            "status": health_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "ecpay-webhooks",
            "metrics": {
                "recent_webhooks_30min": recent_webhooks,
                "failed_webhooks_24h": failed_webhooks,
                "total_webhooks_24h": total_webhooks,
                "success_rate_24h": round(success_rate, 2),
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "ecpay-webhooks",
            "error": str(e),
        }


@router.post("/ecpay-manual-retry")
async def handle_manual_payment_retry(
    request: Request,
    payment_id: str = Form(...),
    admin_token: str = Form(...),  # Simple admin authentication
    db: Session = Depends(get_db),
):
    """
    Manual webhook endpoint for triggering payment retries.
    This is for administrative use when automatic retries fail.
    """

    start_time = time.time()

    try:
        # Simple admin token validation
        if admin_token != settings.ADMIN_WEBHOOK_TOKEN:
            logger.warning(
                f"🚨 Unauthorized manual retry attempt from {_get_client_ip(request)}"
            )
            raise HTTPException(status_code=401, detail="Unauthorized")

        logger.info(f"🔧 Manual payment retry requested for payment {payment_id}")

        # Get payment record
        payment = (
            db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.id == payment_id)
            .first()
        )

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Get related subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(SaasSubscription.id == payment.subscription_id)
            .first()
        )

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Create ECPay service
        ecpay_service = ECPaySubscriptionService(db, settings)

        # Attempt manual retry
        success = ecpay_service.retry_failed_payments()

        if success:
            processing_time = round((time.time() - start_time) * 1000, 2)
            logger.info(
                f"✅ Manual payment retry completed successfully ({processing_time}ms)"
            )

            return {
                "status": "success",
                "payment_id": payment_id,
                "processing_time_ms": processing_time,
                "message": "Payment retry processed successfully",
            }
        else:
            logger.error(f"❌ Manual payment retry failed for {payment_id}")
            raise HTTPException(status_code=500, detail="Retry processing failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Manual retry endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/subscription-status/{user_id}")
async def get_subscription_webhook_status(
    user_id: str, admin_token: str, db: Session = Depends(get_db)
):
    """
    Get subscription webhook processing status for a specific user.
    Useful for debugging webhook processing issues.
    """

    try:
        # Simple admin token validation
        if admin_token != settings.ADMIN_WEBHOOK_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Get user's subscription
        subscription = (
            db.query(SaasSubscription)
            .filter(SaasSubscription.user_id == user_id)
            .first()
        )

        if not subscription:
            return {
                "user_id": user_id,
                "subscription_found": False,
                "message": "No subscription found for user",
            }

        # Get recent webhook activity
        recent_webhooks = (
            db.query(WebhookLog)
            .filter(
                WebhookLog.user_id == user_id,
                WebhookLog.received_at >= datetime.now(UTC) - timedelta(days=30),
            )
            .order_by(WebhookLog.received_at.desc())
            .limit(10)
            .all()
        )

        # Get recent payments
        recent_payments = (
            db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription.id)
            .order_by(SubscriptionPayment.created_at.desc())
            .limit(5)
            .all()
        )

        # Prepare webhook summary
        webhook_summary = []
        for webhook in recent_webhooks:
            webhook_summary.append(
                {
                    "id": str(webhook.id),
                    "type": webhook.webhook_type,
                    "status": webhook.status,
                    "received_at": webhook.received_at.isoformat(),
                    "processing_time_ms": webhook.processing_time_ms,
                    "check_mac_verified": webhook.check_mac_value_verified,
                }
            )

        # Prepare payment summary
        payment_summary = []
        for payment in recent_payments:
            payment_summary.append(
                {
                    "id": str(payment.id),
                    "status": payment.status,
                    "amount_twd": payment.amount / 100,  # Convert from cents
                    "retry_count": payment.retry_count,
                    "next_retry_at": (
                        payment.next_retry_at.isoformat()
                        if payment.next_retry_at
                        else None
                    ),
                    "created_at": payment.created_at.isoformat(),
                }
            )

        return {
            "user_id": user_id,
            "subscription_found": True,
            "subscription": {
                "id": str(subscription.id),
                "plan_id": subscription.plan_id,
                "status": subscription.status,
                "current_period_end": (subscription.current_period_end.isoformat()),
                "grace_period_ends_at": (
                    subscription.grace_period_ends_at.isoformat()
                    if subscription.grace_period_ends_at
                    else None
                ),
                "downgrade_reason": subscription.downgrade_reason,
            },
            "recent_webhooks": webhook_summary,
            "recent_payments": payment_summary,
            "summary": {
                "total_webhooks_30d": len(webhook_summary),
                "total_payments": len(payment_summary),
                "failed_payments": len(
                    [p for p in payment_summary if p["status"] == "failed"]
                ),
                "pending_retries": len(
                    [p for p in payment_summary if p["next_retry_at"] is not None]
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Subscription status endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/trigger-maintenance")
async def trigger_subscription_maintenance(
    admin_token: str = Form(...),
    force: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Manually trigger subscription maintenance tasks.
    Useful for testing and emergency maintenance.
    """

    try:
        # Simple admin token validation
        if admin_token != settings.ADMIN_WEBHOOK_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")

        logger.info("🔧 Manual subscription maintenance triggered")

        ecpay_service = ECPaySubscriptionService(db, settings)

        # Run maintenance tasks
        expired_processed = ecpay_service.check_and_handle_expired_subscriptions()
        retries_processed = ecpay_service.retry_failed_payments()

        # Get current stats
        active_subs = (
            db.query(SaasSubscription)
            .filter(SaasSubscription.status == "active")
            .count()
        )

        past_due_subs = (
            db.query(SaasSubscription)
            .filter(SaasSubscription.status == "past_due")
            .count()
        )

        result = {
            "status": "completed",
            "maintenance_run_at": datetime.now(UTC).isoformat(),
            "results": {
                "expired_subscriptions_processed": expired_processed or 0,
                "payment_retries_processed": retries_processed or 0,
                "current_active_subscriptions": active_subs,
                "current_past_due_subscriptions": past_due_subs,
            },
        }

        logger.info(f"✅ Manual maintenance completed: {result['results']}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Manual maintenance trigger error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook-stats")
async def webhook_statistics(hours: int = 24, db: Session = Depends(get_db)):
    """Get webhook statistics for monitoring."""

    try:
        since = datetime.now(UTC) - timedelta(hours=hours)

        # Total webhooks by type
        webhook_stats = (
            db.query(
                WebhookLog.webhook_type,
                WebhookLog.status,
                db.func.count(WebhookLog.id).label("count"),
            )
            .filter(WebhookLog.received_at >= since)
            .group_by(WebhookLog.webhook_type, WebhookLog.status)
            .all()
        )

        # Process statistics
        stats_summary = {}
        for webhook_type, status, count in webhook_stats:
            if webhook_type not in stats_summary:
                stats_summary[webhook_type] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "processing": 0,
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
            "generated_at": datetime.now(UTC).isoformat(),
            "webhook_types": stats_summary,
        }

    except Exception as e:
        logger.error(f"Failed to get webhook statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook statistics",
        )
