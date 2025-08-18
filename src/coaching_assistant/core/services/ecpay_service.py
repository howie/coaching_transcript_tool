"""ECPay subscription service for SaaS billing."""

import hashlib
import urllib.parse
import logging
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..config import Settings
from ...models import (
    User, 
    ECPayCreditAuthorization, 
    SaasSubscription, 
    SubscriptionPayment,
    ECPayAuthStatus,
    SubscriptionStatus,
    PaymentStatus
)

logger = logging.getLogger(__name__)


class ECPaySubscriptionService:
    """ECPay subscription service for SaaS billing."""
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        
        # ECPay configuration
        self.merchant_id = settings.ECPAY_MERCHANT_ID
        self.hash_key = settings.ECPAY_HASH_KEY
        self.hash_iv = settings.ECPAY_HASH_IV
        self.environment = settings.ECPAY_ENVIRONMENT
        
        # API URLs
        if self.environment == "sandbox":
            self.aio_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
            self.credit_detail_url = "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"
        else:
            self.aio_url = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"
            self.credit_detail_url = "https://payment.ecpay.com.tw/CreditDetail/DoAction"
    
    def create_credit_authorization(
        self, 
        user_id: str, 
        plan_id: str, 
        billing_cycle: str
    ) -> Dict[str, Any]:
        """Create ECPay credit card authorization for recurring payments."""
        
        try:
            # Get plan pricing
            plan_pricing = self._get_plan_pricing(plan_id, billing_cycle)
            if not plan_pricing:
                raise ValueError(f"Invalid plan: {plan_id} with cycle: {billing_cycle}")
            
            # Generate unique merchant member ID
            timestamp = int(time.time())
            merchant_member_id = f"USER{user_id[:8]}{timestamp}"
            
            # Prepare authorization data
            auth_data = {
                "MerchantID": self.merchant_id,
                "MerchantMemberID": merchant_member_id,
                "ActionType": "CreateAuth",
                "TotalAmount": plan_pricing["amount_twd"] // 100,  # Convert cents to dollars
                "ProductDesc": f"{plan_pricing['plan_name']}方案訂閱",
                "OrderResultURL": f"{self.settings.FRONTEND_URL}/subscription/result",
                "ReturnURL": f"{self.settings.API_BASE_URL}/api/webhooks/ecpay-auth",
                "ClientBackURL": f"{self.settings.FRONTEND_URL}/billing",
                
                # Recurring payment settings
                "PeriodType": "Month" if billing_cycle == "monthly" else "Year",
                "Frequency": 1,
                "PeriodAmount": plan_pricing["amount_twd"] // 100,
                "ExecTimes": 0,  # Unlimited recurring payments
                
                # Payment method (credit card only)
                "PaymentType": "aio",
                "ChoosePayment": "Credit",
                
                # Additional fields
                "Remark": f"用戶: {user_id}, 方案: {plan_id}",
                "PlatformID": "",
                "EncryptType": "1"
            }
            
            # Generate CheckMacValue
            auth_data["CheckMacValue"] = self._generate_check_mac_value(auth_data)
            
            # Create authorization record
            auth_record = ECPayCreditAuthorization(
                user_id=user_id,
                merchant_member_id=merchant_member_id,
                auth_amount=plan_pricing["amount_twd"],
                period_type=auth_data["PeriodType"],
                period_amount=plan_pricing["amount_twd"],
                description=f"{plan_pricing['plan_name']}方案訂閱",
                auth_status=ECPayAuthStatus.PENDING.value
            )
            
            self.db.add(auth_record)
            self.db.commit()
            
            logger.info(f"Created ECPay authorization for user {user_id}, plan {plan_id}")
            
            return {
                "action_url": self.credit_detail_url,
                "form_data": auth_data,
                "merchant_member_id": merchant_member_id,
                "auth_id": str(auth_record.id)
            }
            
        except Exception as e:
            logger.error(f"Failed to create ECPay authorization: {e}")
            self.db.rollback()
            raise
    
    def handle_auth_callback(self, callback_data: Dict[str, str]) -> bool:
        """Handle ECPay authorization callback."""
        
        try:
            # Verify CheckMacValue
            if not self._verify_callback(callback_data):
                logger.error("ECPay auth callback verification failed")
                return False
            
            merchant_member_id = callback_data.get("MerchantMemberID")
            if not merchant_member_id:
                logger.error("Missing MerchantMemberID in callback")
                return False
            
            # Find authorization record
            auth_record = self.db.query(ECPayCreditAuthorization).filter(
                ECPayCreditAuthorization.merchant_member_id == merchant_member_id
            ).first()
            
            if not auth_record:
                logger.error(f"Authorization record not found: {merchant_member_id}")
                return False
            
            rtn_code = callback_data.get("RtnCode")
            if rtn_code == "1":  # Success
                # Update authorization record
                auth_record.auth_status = ECPayAuthStatus.ACTIVE.value
                auth_record.gwsr = callback_data.get("gwsr")
                auth_record.auth_code = callback_data.get("AuthCode")
                auth_record.card_last4 = callback_data.get("card4no")
                auth_record.card_brand = callback_data.get("card6no")
                auth_record.auth_date = datetime.now()
                
                # Calculate next payment date
                if auth_record.period_type == "Month":
                    auth_record.next_pay_date = date.today() + timedelta(days=30)
                else:  # Year
                    auth_record.next_pay_date = date.today() + timedelta(days=365)
                
                # Create subscription
                subscription = self._create_subscription(auth_record)
                
                # Upgrade user plan
                user = self.db.query(User).filter(User.id == auth_record.user_id).first()
                if user:
                    # Map plan_id to UserPlan enum
                    from ...models.user import UserPlan
                    plan_mapping = {
                        "PRO": UserPlan.PRO,
                        "ENTERPRISE": UserPlan.ENTERPRISE
                    }
                    user.plan = plan_mapping.get(subscription.plan_id, UserPlan.FREE)
                
                self.db.commit()
                
                logger.info(f"Authorization successful for {merchant_member_id}")
                return True
                
            else:  # Failed
                auth_record.auth_status = ECPayAuthStatus.FAILED.value
                self.db.commit()
                
                logger.warning(f"Authorization failed: {merchant_member_id}, {callback_data.get('RtnMsg')}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing auth callback: {e}")
            self.db.rollback()
            return False
    
    def handle_payment_webhook(self, webhook_data: Dict[str, str]) -> bool:
        """Handle ECPay automatic billing webhook."""
        
        try:
            # Verify CheckMacValue
            if not self._verify_callback(webhook_data):
                logger.error("ECPay payment webhook verification failed")
                return False
            
            merchant_member_id = webhook_data.get("MerchantMemberID")
            gwsr = webhook_data.get("gwsr")
            rtn_code = webhook_data.get("RtnCode")
            amount = int(webhook_data.get("amount", "0")) * 100  # Convert to cents
            
            # Find authorization and subscription
            auth_record = self.db.query(ECPayCreditAuthorization).filter(
                ECPayCreditAuthorization.merchant_member_id == merchant_member_id
            ).first()
            
            if not auth_record:
                logger.error(f"Auth record not found for payment: {merchant_member_id}")
                return False
            
            subscription = self.db.query(SaasSubscription).filter(
                SaasSubscription.auth_id == auth_record.id,
                SaasSubscription.status.in_([SubscriptionStatus.ACTIVE.value, SubscriptionStatus.PAST_DUE.value])
            ).first()
            
            if not subscription:
                logger.error(f"Active subscription not found for auth: {auth_record.id}")
                return False
            
            # Create payment record
            payment_record = SubscriptionPayment(
                subscription_id=subscription.id,
                auth_id=auth_record.id,
                gwsr=gwsr,
                amount=amount,
                currency="TWD",
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end,
                ecpay_response=webhook_data,
                processed_at=datetime.now()
            )
            
            if rtn_code == "1":  # Payment success
                payment_record.status = PaymentStatus.SUCCESS.value
                
                # Extend subscription period
                if auth_record.period_type == "Month":
                    new_period_start = subscription.current_period_end + timedelta(days=1)
                    new_period_end = new_period_start + timedelta(days=30)
                else:  # Year
                    new_period_start = subscription.current_period_end + timedelta(days=1)
                    new_period_end = new_period_start + timedelta(days=365)
                
                subscription.current_period_start = new_period_start
                subscription.current_period_end = new_period_end
                subscription.status = SubscriptionStatus.ACTIVE.value
                
                # Update next payment date
                auth_record.next_pay_date = new_period_end
                auth_record.exec_times += 1
                
                logger.info(f"Payment successful: {gwsr}, subscription extended")
                
            else:  # Payment failed
                payment_record.status = PaymentStatus.FAILED.value
                payment_record.failure_reason = webhook_data.get("RtnMsg")
                
                # Handle failed payment (implement retry logic)
                self._handle_failed_payment(subscription, payment_record)
                
                logger.warning(f"Payment failed: {gwsr}, reason: {payment_record.failure_reason}")
            
            self.db.add(payment_record)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error processing payment webhook: {e}")
            self.db.rollback()
            return False
    
    def _create_subscription(self, auth_record: ECPayCreditAuthorization) -> SaasSubscription:
        """Create subscription after successful authorization."""
        
        # Determine plan details from amount
        plan_details = self._get_plan_from_amount(auth_record.period_amount * 100)  # Convert to cents
        
        # Set subscription period
        if auth_record.period_type == "Month":
            period_start = date.today()
            period_end = period_start + timedelta(days=30)
            billing_cycle = "monthly"
        else:  # Year
            period_start = date.today()
            period_end = period_start + timedelta(days=365)
            billing_cycle = "annual"
        
        subscription = SaasSubscription(
            user_id=auth_record.user_id,
            auth_id=auth_record.id,
            plan_id=plan_details["plan_id"],
            plan_name=plan_details["plan_name"],
            billing_cycle=billing_cycle,
            amount_twd=auth_record.period_amount * 100,  # Convert to cents
            currency="TWD",
            status=SubscriptionStatus.ACTIVE.value,
            current_period_start=period_start,
            current_period_end=period_end
        )
        
        self.db.add(subscription)
        return subscription
    
    def _handle_failed_payment(self, subscription: SaasSubscription, payment: SubscriptionPayment):
        """Handle failed payment with retry logic."""
        
        # Get retry count from recent payments
        recent_failures = self.db.query(SubscriptionPayment).filter(
            SubscriptionPayment.subscription_id == subscription.id,
            SubscriptionPayment.status == PaymentStatus.FAILED.value,
            SubscriptionPayment.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        payment.retry_count = recent_failures
        
        if recent_failures >= 3:
            # Mark subscription as past due
            subscription.status = SubscriptionStatus.PAST_DUE.value
            logger.warning(f"Subscription {subscription.id} marked as past due after {recent_failures} failures")
            
            # TODO: Implement grace period and eventual cancellation
            # TODO: Send payment failure notifications
    
    def _get_plan_pricing(self, plan_id: str, billing_cycle: str) -> Optional[Dict[str, Any]]:
        """Get plan pricing configuration."""
        
        pricing = {
            "PRO": {
                "monthly": {"amount_twd": 89900, "plan_name": "專業方案"},
                "annual": {"amount_twd": 899900, "plan_name": "專業方案"}
            },
            "ENTERPRISE": {
                "monthly": {"amount_twd": 299900, "plan_name": "企業方案"},
                "annual": {"amount_twd": 2999900, "plan_name": "企業方案"}
            }
        }
        
        return pricing.get(plan_id, {}).get(billing_cycle)
    
    def _get_plan_from_amount(self, amount_cents: int) -> Dict[str, str]:
        """Get plan details from payment amount."""
        
        amount_mapping = {
            89900: {"plan_id": "PRO", "plan_name": "專業方案"},
            899900: {"plan_id": "PRO", "plan_name": "專業方案"},
            299900: {"plan_id": "ENTERPRISE", "plan_name": "企業方案"},
            2999900: {"plan_id": "ENTERPRISE", "plan_name": "企業方案"}
        }
        
        return amount_mapping.get(amount_cents, {"plan_id": "PRO", "plan_name": "專業方案"})
    
    def _generate_check_mac_value(self, data: Dict[str, str]) -> str:
        """Generate ECPay CheckMacValue for security verification."""
        
        # Remove CheckMacValue if present
        data = {k: v for k, v in data.items() if k != "CheckMacValue"}
        
        # Sort parameters by key
        sorted_data = sorted(data.items())
        
        # URL encode values
        encoded_params = []
        for key, value in sorted_data:
            encoded_value = urllib.parse.quote_plus(str(value))
            encoded_params.append(f"{key}={encoded_value}")
        
        # Create query string
        query_string = "&".join(encoded_params)
        
        # Add HashKey and HashIV
        raw_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"
        
        # URL encode entire string
        encoded_string = urllib.parse.quote_plus(raw_string).lower()
        
        # Generate SHA256 hash
        return hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
    
    def _verify_callback(self, callback_data: Dict[str, str]) -> bool:
        """Verify ECPay callback CheckMacValue."""
        
        received_mac = callback_data.get("CheckMacValue", "")
        calculated_mac = self._generate_check_mac_value(callback_data)
        
        return received_mac.upper() == calculated_mac.upper()
    
    def cancel_authorization(self, auth_id: str) -> bool:
        """Cancel ECPay credit card authorization."""
        
        try:
            auth_record = self.db.query(ECPayCreditAuthorization).filter(
                ECPayCreditAuthorization.id == auth_id
            ).first()
            
            if not auth_record:
                return False
            
            # TODO: Call ECPay API to cancel authorization
            # For now, just mark as cancelled locally
            auth_record.auth_status = ECPayAuthStatus.CANCELLED.value
            
            # Cancel associated subscriptions
            subscriptions = self.db.query(SaasSubscription).filter(
                SaasSubscription.auth_id == auth_record.id,
                SaasSubscription.status == SubscriptionStatus.ACTIVE.value
            ).all()
            
            for subscription in subscriptions:
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.cancelled_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Authorization cancelled: {auth_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling authorization: {e}")
            self.db.rollback()
            return False