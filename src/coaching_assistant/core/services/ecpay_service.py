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
            
            # Generate unique merchant member ID and trade number
            timestamp = int(time.time())
            # Sanitize user ID to ensure safe characters (alphanumeric only)
            safe_user_prefix = ''.join(c for c in user_id[:8].upper() if c.isalnum())[:8]
            # Pad with zeros if too short after sanitization
            safe_user_prefix = safe_user_prefix.ljust(8, '0')[:8]
            
            merchant_member_id = f"USER{safe_user_prefix}{timestamp}"
            # ECPay MerchantTradeNo must be <= 20 characters
            # Format: SUB + last 6 digits of timestamp + sanitized 8 chars of user_id
            merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"
            
            # Prepare authorization data for ECPay AioCheckOut recurring payment API
            auth_data = {
                # Required basic fields
                "MerchantID": self.merchant_id,
                "MerchantMemberID": merchant_member_id,
                "MerchantTradeNo": merchant_trade_no,
                "TotalAmount": str(plan_pricing["amount_twd"] // 100),  # Convert to string for ECPay
                # Note: ECPay V5 API does not have ProductDesc field, only TradeDesc and ItemName
                
                # URLs for callbacks
                "OrderResultURL": f"{self.settings.FRONTEND_URL}/subscription/result",
                "ReturnURL": f"{self.settings.API_BASE_URL}/api/webhooks/ecpay-auth", 
                "ClientBackURL": f"{self.settings.FRONTEND_URL}/billing",
                
                # Credit card recurring payment specific fields
                "PeriodType": "M" if billing_cycle == "monthly" else "Y",  # ECPay uses M/Y not Month/Year
                "Frequency": "1",  # String format for ECPay
                "PeriodAmount": str(plan_pricing["amount_twd"] // 100),  # Amount per period as string
                # ECPay ExecTimes rules updated: M=2-999, Y=2-99 (both limited)
                "ExecTimes": str(999 if billing_cycle == "monthly" else 99),  # Monthly=999 times, Yearly=99 times as string
                
                # Payment method specification
                "PaymentType": "aio",
                "ChoosePayment": "Credit",
                
                # Additional required fields for credit card authorization
                "TradeDesc": "教練助手訂閱",  # Chinese trade description
                "ItemName": f"訂閱方案#1#個#{plan_pricing['amount_twd'] // 100}",  # Already string format
                "Remark": "",  # Empty to avoid any format issues
                "ChooseSubPayment": "",  # Empty for general credit card
                "PlatformID": "",
                "EncryptType": "1",
                
                # Required fields for ECPay payments
                "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),  # Trade date
                "ExpireDate": "7",  # Order expires in 7 days
                # Note: TradeNo is ECPay-generated, should NOT be included in order creation
                
                # Credit card authorization specific fields  
                "BindingCard": "0",  # 0=不記憶卡號, 1=記憶卡號
                "CustomField1": plan_id,  # Store plan ID for reference
                "CustomField2": billing_cycle,  # Store billing cycle for reference
                "CustomField3": user_id[:8],  # Store user ID prefix for reference
                "CustomField4": "",
                
                # Additional fields that might be required
                "NeedExtraPaidInfo": "N",  # Don't need extra payment info
                "DeviceSource": "",  # Empty for web
                "IgnorePayment": "",  # Don't ignore any payment methods
                "Language": "",  # Use default language
            }
            
            # Generate CheckMacValue
            calculated_mac = self._generate_check_mac_value(auth_data)
            auth_data["CheckMacValue"] = calculated_mac
            
            # Comprehensive debugging output (按照用戶建議)
            logger.info("=== ECPay Backend Authorization Debug ===")
            logger.info(f"🕐 MerchantTradeDate: '{auth_data['MerchantTradeDate']}' (length: {len(auth_data['MerchantTradeDate'])})")
            logger.info(f"📋 完整參數列表 (按 ASCII 排序):")
            
            # 按 ASCII 排序輸出所有參數（與前端一致）
            for key in sorted(auth_data.keys()):
                value = auth_data[key]
                if key != "CheckMacValue":  # CheckMacValue 單獨處理
                    logger.info(f"   {key}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})")
            
            # 特別標注關鍵參數
            critical_fields = ['MerchantTradeDate', 'TotalAmount', 'TradeDesc', 'ItemName', 'PeriodType', 'ExecTimes']
            logger.info(f"🔍 關鍵參數檢查:")
            for field in critical_fields:
                if field in auth_data:
                    value = auth_data[field]
                    logger.info(f"   {field}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})")
            
            # CheckMacValue 計算結果
            logger.info(f"🔐 CheckMacValue 計算結果:")
            logger.info(f"   計算出的值: {calculated_mac}")
            logger.info(f"   值長度: {len(calculated_mac)}")
            
            # 輸出完整 JSON 供比較
            import json
            logger.info(f"📤 後端生成的完整參數 JSON:")
            sorted_auth_data = {k: auth_data[k] for k in sorted(auth_data.keys())}
            logger.info(json.dumps(sorted_auth_data, ensure_ascii=False, indent=2))
            
            # Create authorization record
            auth_record = ECPayCreditAuthorization(
                user_id=user_id,
                merchant_member_id=merchant_member_id,
                auth_amount=plan_pricing["amount_twd"],
                period_type=auth_data["PeriodType"],
                period_amount=plan_pricing["amount_twd"],
                description=f"{plan_id} Plan Subscription",
                auth_status=ECPayAuthStatus.PENDING.value
            )
            
            self.db.add(auth_record)
            self.db.commit()
            
            logger.info(f"Created ECPay authorization for user {user_id}, plan {plan_id}")
            
            return {
                "action_url": self.aio_url,  # Use AioCheckOut for recurring payments
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
                if auth_record.period_type == "M":
                    auth_record.next_pay_date = date.today() + timedelta(days=30)
                else:  # Y
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
                if auth_record.period_type == "M":
                    new_period_start = subscription.current_period_end + timedelta(days=1)
                    new_period_end = new_period_start + timedelta(days=30)
                else:  # Y
                    new_period_start = subscription.current_period_end + timedelta(days=1)
                    new_period_end = new_period_start + timedelta(days=365)
                
                subscription.current_period_start = new_period_start
                subscription.current_period_end = new_period_end
                subscription.status = SubscriptionStatus.ACTIVE.value
                
                # Update next payment date
                auth_record.next_pay_date = new_period_end
                auth_record.exec_times += 1
                
                # Send success notifications
                self._handle_payment_success_notifications(subscription, payment_record)
                
                logger.info(f"Payment successful: {gwsr}, subscription extended")
                
            else:  # Payment failed
                payment_record.status = PaymentStatus.FAILED.value
                payment_record.failure_reason = webhook_data.get("RtnMsg")
                
                # Handle failed payment (implement retry logic)
                self._handle_failed_payment(subscription, payment_record)
                
                # Send failure notifications
                self._handle_payment_failure_notifications(subscription, payment_record)
                
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
        if auth_record.period_type == "M":
            period_start = date.today()
            period_end = period_start + timedelta(days=30)
            billing_cycle = "monthly"
        else:  # Y
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
    
    def calculate_prorated_charge(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str
    ) -> Dict[str, Any]:
        """Calculate prorated charge for plan upgrade."""
        
        # Get current date and subscription period info
        today = date.today()
        current_period_start = subscription.current_period_start
        current_period_end = subscription.current_period_end
        
        # Calculate remaining days in current period
        total_days = (current_period_end - current_period_start).days
        remaining_days = (current_period_end - today).days
        
        if remaining_days <= 0:
            remaining_days = 0
        
        # Calculate current plan remaining value
        current_remaining_value = int(
            (subscription.amount_twd * remaining_days) / total_days
        ) if total_days > 0 else 0
        
        # Get new plan pricing
        new_plan_pricing = self._get_plan_pricing(new_plan_id, new_billing_cycle)
        if not new_plan_pricing:
            raise ValueError(f"Invalid plan: {new_plan_id} with cycle: {new_billing_cycle}")
        
        # Calculate new plan prorated cost
        new_plan_prorated_cost = int(
            (new_plan_pricing["amount_twd"] * remaining_days) / total_days
        ) if total_days > 0 else new_plan_pricing["amount_twd"]
        
        # Net charge (additional amount needed)
        net_charge = max(0, new_plan_prorated_cost - current_remaining_value)
        
        return {
            "current_plan_remaining_value": current_remaining_value,
            "new_plan_prorated_cost": new_plan_prorated_cost,
            "net_charge": net_charge,
            "effective_date": datetime.now().isoformat()
        }
    
    def upgrade_subscription(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str
    ) -> Dict[str, Any]:
        """Upgrade subscription plan with prorated billing."""
        
        try:
            # Calculate prorated charge
            proration = self.calculate_prorated_charge(
                subscription, new_plan_id, new_billing_cycle
            )
            
            # Get new plan details
            new_plan_pricing = self._get_plan_pricing(new_plan_id, new_billing_cycle)
            
            # TODO: If there's a net charge, process payment via ECPay
            # For now, we'll assume payment is successful
            if proration["net_charge"] > 0:
                logger.info(f"Prorated charge required: {proration['net_charge']} cents")
                # In production, this would trigger an ECPay payment request
            
            # Update subscription immediately
            subscription.plan_id = new_plan_id
            subscription.plan_name = new_plan_pricing["plan_name"]
            subscription.billing_cycle = new_billing_cycle
            subscription.amount_twd = new_plan_pricing["amount_twd"]
            
            # Update ECPay authorization amount if needed
            if subscription.auth_record:
                subscription.auth_record.period_amount = new_plan_pricing["amount_twd"]
                subscription.auth_record.auth_amount = new_plan_pricing["amount_twd"]
            
            self.db.commit()
            
            logger.info(f"Subscription {subscription.id} upgraded to {new_plan_id}")
            
            return {
                "subscription": subscription,
                "prorated_charge": proration["net_charge"]
            }
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            self.db.rollback()
            raise
    
    def schedule_downgrade(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str
    ) -> Dict[str, Any]:
        """Schedule subscription downgrade for period end."""
        
        try:
            # Get new plan details
            new_plan_pricing = self._get_plan_pricing(new_plan_id, new_billing_cycle)
            if not new_plan_pricing:
                raise ValueError(f"Invalid plan: {new_plan_id} with cycle: {new_billing_cycle}")
            
            # For simplicity, we'll use a custom field or create a pending changes table
            # For now, we'll store the pending change in subscription metadata
            subscription.cancellation_reason = f"DOWNGRADE_TO:{new_plan_id}:{new_billing_cycle}"
            subscription.cancel_at_period_end = True
            
            self.db.commit()
            
            logger.info(f"Subscription {subscription.id} scheduled for downgrade to {new_plan_id}")
            
            return {
                "effective_date": subscription.current_period_end.isoformat(),
                "new_plan": new_plan_pricing
            }
            
        except Exception as e:
            logger.error(f"Error scheduling downgrade: {e}")
            self.db.rollback()
            raise
    
    def cancel_subscription(
        self,
        subscription: SaasSubscription,
        immediate: bool = False,
        reason: str = None
    ) -> Dict[str, Any]:
        """Cancel subscription with immediate or period-end options."""
        
        try:
            if immediate:
                # Immediate cancellation
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.cancelled_at = datetime.now()
                subscription.cancellation_reason = reason or "Immediate cancellation"
                
                # Cancel ECPay authorization
                if subscription.auth_record:
                    subscription.auth_record.auth_status = ECPayAuthStatus.CANCELLED.value
                
                # TODO: In production, call ECPay API to cancel authorization
                # self._cancel_ecpay_authorization(subscription.auth_record.merchant_member_id)
                
                effective_date = datetime.now()
                refund_amount = 0  # TODO: Calculate refund if applicable
                
            else:
                # Period-end cancellation
                subscription.cancel_at_period_end = True
                subscription.cancellation_reason = reason or "Period-end cancellation"
                
                effective_date = subscription.current_period_end
                refund_amount = 0
            
            self.db.commit()
            
            logger.info(f"Subscription {subscription.id} cancelled ({'immediate' if immediate else 'period-end'})")
            
            return {
                "effective_date": effective_date.isoformat(),
                "refund_amount": refund_amount
            }
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            self.db.rollback()
            raise
    
    def send_payment_notification(
        self, 
        user_id: str, 
        notification_type: str, 
        subscription: SaasSubscription = None,
        payment: SubscriptionPayment = None
    ):
        """Send payment-related notifications to users."""
        
        try:
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User not found for notification: {user_id}")
                return
            
            # Prepare notification data
            notification_data = {
                "user_email": user.email,
                "user_name": getattr(user, 'name', user.email.split('@')[0]),
                "timestamp": datetime.now().isoformat(),
                "notification_type": notification_type
            }
            
            if subscription:
                notification_data.update({
                    "plan_name": subscription.plan_name,
                    "billing_cycle": subscription.billing_cycle,
                    "amount": f"NT${subscription.amount_twd / 100:,.0f}",
                    "next_billing_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None
                })
            
            if payment:
                notification_data.update({
                    "payment_amount": f"NT${payment.amount / 100:,.0f}",
                    "payment_date": payment.processed_at.isoformat() if payment.processed_at else None,
                    "failure_reason": payment.failure_reason
                })
            
            # Log notification (in production, this would send email/SMS)
            logger.info(f"📧 Notification: {notification_type} for user {user.email}")
            logger.info(f"📊 Notification data: {notification_data}")
            
            # TODO: Implement actual notification sending
            # - Email via SendGrid/AWS SES
            # - In-app notifications
            # - SMS for critical alerts
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification_type} to user {user_id}: {e}")
    
    def _handle_payment_success_notifications(
        self, 
        subscription: SaasSubscription, 
        payment: SubscriptionPayment
    ):
        """Handle notifications for successful payments."""
        
        try:
            # Send payment success notification
            self.send_payment_notification(
                subscription.user_id,
                "payment_success",
                subscription=subscription,
                payment=payment
            )
            
            # Send subscription renewal notification
            self.send_payment_notification(
                subscription.user_id,
                "subscription_renewed",
                subscription=subscription,
                payment=payment
            )
            
            logger.info(f"✅ Payment success notifications sent for subscription {subscription.id}")
            
        except Exception as e:
            logger.error(f"Failed to send payment success notifications: {e}")
    
    def _handle_payment_failure_notifications(
        self, 
        subscription: SaasSubscription, 
        payment: SubscriptionPayment
    ):
        """Handle notifications for failed payments."""
        
        try:
            # Send payment failure notification
            self.send_payment_notification(
                subscription.user_id,
                "payment_failed",
                subscription=subscription,
                payment=payment
            )
            
            # Check if this triggers grace period
            if payment.retry_count >= 3:
                self.send_payment_notification(
                    subscription.user_id,
                    "subscription_past_due",
                    subscription=subscription,
                    payment=payment
                )
            
            # Send retry notification if applicable
            if payment.retry_count < 3:
                self.send_payment_notification(
                    subscription.user_id,
                    "payment_retry_scheduled",
                    subscription=subscription,
                    payment=payment
                )
            
            logger.info(f"❌ Payment failure notifications sent for subscription {subscription.id}")
            
        except Exception as e:
            logger.error(f"Failed to send payment failure notifications: {e}")