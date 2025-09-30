"""ECPay subscription service for SaaS billing."""

import hashlib
import logging
import time
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

# Import SQLAlchemy models for database operations
from ...models.ecpay_subscription import (
    ECPayCreditAuthorization,
)
from ...models.ecpay_subscription import (
    SaasSubscription as SaasSubscriptionORM,
)
from ...models.ecpay_subscription import (
    SubscriptionPayment as SubscriptionPaymentORM,
)
from ..config import Settings
from ..models.subscription import (
    ECPayAuthStatus,
    PaymentStatus,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)
from ..models.user import User
from ..repositories.ports import (
    ECPayClientPort,
    NotificationPort,
    SubscriptionRepoPort,
    UserRepoPort,
)

logger = logging.getLogger(__name__)


class ECPaySubscriptionService:
    """ECPay subscription service for SaaS billing following Clean Architecture."""

    def __init__(
        self,
        user_repo: UserRepoPort,
        subscription_repo: SubscriptionRepoPort,
        settings: Settings,
        ecpay_client: ECPayClientPort,
        notification_service: NotificationPort,
    ):
        self.user_repo = user_repo
        self.subscription_repo = subscription_repo
        self.settings = settings
        self.ecpay_client = ecpay_client
        self.notification_service = notification_service

        # ECPay configuration (keeping for backwards compatibility)
        self.merchant_id = settings.ECPAY_MERCHANT_ID
        self.hash_key = settings.ECPAY_HASH_KEY
        self.hash_iv = settings.ECPAY_HASH_IV
        self.environment = settings.ECPAY_ENVIRONMENT

        # API URLs (keeping for backwards compatibility)
        if self.environment == "sandbox":
            self.aio_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
            self.credit_detail_url = (
                "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"
            )
        else:
            self.aio_url = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"
            self.credit_detail_url = (
                "https://payment.ecpay.com.tw/CreditDetail/DoAction"
            )

    def create_credit_authorization(
        self, user_id: str, plan_id: str, billing_cycle: str
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
            safe_user_prefix = "".join(c for c in user_id[:8].upper() if c.isalnum())[
                :8
            ]
            # Pad with zeros if too short after sanitization
            safe_user_prefix = safe_user_prefix.ljust(8, "0")[:8]

            merchant_member_id = f"USER{safe_user_prefix}{timestamp}"
            # ECPay MerchantTradeNo must be <= 20 characters
            # Format: SUB + last 6 digits of timestamp + sanitized 8 chars of
            # user_id
            merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"

            # Prepare authorization data for ECPay AioCheckOut recurring
            # payment API
            auth_data = {  # Required basic fields
                "MerchantID": self.merchant_id,
                "MerchantMemberID": merchant_member_id,
                "MerchantTradeNo": merchant_trade_no,
                "TotalAmount": str(
                    plan_pricing["amount_twd"] // 100
                ),  # Convert to string for ECPay
                # Note: ECPay V5 API does not have ProductDesc field, only TradeDesc and ItemName
                # URLs for callbacks
                "OrderResultURL": (
                    f"{self.settings.FRONTEND_URL}/api/subscription/result"
                ),
                "ReturnURL": (f"{self.settings.API_BASE_URL}/api/webhooks/ecpay-auth"),
                "ClientBackURL": f"{self.settings.FRONTEND_URL}/billing",
                # Credit card recurring payment specific fields
                "PeriodType": (
                    "M" if billing_cycle == "monthly" else "Y"
                ),  # ECPay uses M/Y not Month/Year
                "Frequency": "1",  # String format for ECPay
                "PeriodAmount": str(
                    plan_pricing["amount_twd"] // 100
                ),  # Amount per period as string
                # ECPay ExecTimes rules updated: M=2-999, Y=2-99 (both limited)
                "ExecTimes": str(
                    999 if billing_cycle == "monthly" else 99
                ),  # Monthly=999 times, Yearly=99 times as string
                # Payment method specification
                "PaymentType": "aio",
                "ChoosePayment": "Credit",
                # Additional required fields for credit card authorization
                "TradeDesc": "教練助手訂閱",  # Chinese trade description
                "ItemName": (
                    f"訂閱方案#1#個#{plan_pricing['amount_twd'] // 100}"
                ),  # Already string format
                "Remark": "",  # Empty to avoid any format issues
                "ChooseSubPayment": "",  # Empty for general credit card
                "PlatformID": "",
                "EncryptType": "1",
                # Required fields for ECPay payments
                "MerchantTradeDate": (
                    datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                ),  # Trade date
                "ExpireDate": "7",  # Order expires in 7 days
                # Note: TradeNo is ECPay-generated, should NOT be included in order creation
                # Credit card authorization specific fields
                "BindingCard": "0",  # 0=不記憶卡號, 1=記憶卡號
                "CustomField1": plan_id,  # Store plan ID for reference
                "CustomField2": (billing_cycle),  # Store billing cycle for reference
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
            logger.info(
                f"🕐 MerchantTradeDate: '{auth_data['MerchantTradeDate']}' (length: {len(auth_data['MerchantTradeDate'])})"
            )
            logger.info("📋 完整參數列表 (按 ASCII 排序):")

            # 按 ASCII 排序輸出所有參數（與前端一致）
            for key in sorted(auth_data.keys()):
                value = auth_data[key]
                if key != "CheckMacValue":  # CheckMacValue 單獨處理
                    logger.info(
                        f"   {key}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})"
                    )

            # 特別標注關鍵參數
            critical_fields = [
                "MerchantTradeDate",
                "TotalAmount",
                "TradeDesc",
                "ItemName",
                "PeriodType",
                "ExecTimes",
            ]
            logger.info("🔍 關鍵參數檢查:")
            for field in critical_fields:
                if field in auth_data:
                    value = auth_data[field]
                    logger.info(
                        f"   {field}: '{value}' (type: {type(value).__name__}, len: {len(str(value))})"
                    )

            # CheckMacValue 計算結果（使用修正後的官方規範方法）
            logger.info("🔐 CheckMacValue 計算結果 (官方8步法):")
            logger.info(f"   計算出的值: {calculated_mac}")
            logger.info(f"   值長度: {len(calculated_mac)}")
            logger.info(
                "   ✅ 使用嚴格官方規範: A-Z排序 → URL編碼 → 小寫 → .NET替換 → SHA256大寫"
            )

            # 輸出完整 JSON 供比較
            import json

            logger.info("📤 後端生成的完整參數 JSON:")
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
                auth_status=ECPayAuthStatus.PENDING.value,
            )

            self.db.add(auth_record)
            self.db.commit()

            logger.info(
                f"Created ECPay authorization for user {user_id}, plan {plan_id}"
            )

            return {
                "action_url": (self.aio_url),  # Use AioCheckOut for recurring payments
                "form_data": auth_data,
                "merchant_member_id": merchant_member_id,
                "auth_id": str(auth_record.id),
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
            auth_record = (
                self.db.query(ECPayCreditAuthorization)
                .filter(
                    ECPayCreditAuthorization.merchant_member_id == merchant_member_id
                )
                .first()
            )

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
                user = (
                    self.db.query(User).filter(User.id == auth_record.user_id).first()
                )
                if user:
                    # Map plan_id to UserPlan enum
                    from ..models.user import UserPlan

                    plan_mapping = {
                        "PRO": UserPlan.PRO,
                        "ENTERPRISE": UserPlan.ENTERPRISE,
                    }
                    user.plan = plan_mapping.get(subscription.plan_id, UserPlan.FREE)

                self.db.commit()

                logger.info(f"Authorization successful for {merchant_member_id}")
                return True

            else:  # Failed
                auth_record.auth_status = ECPayAuthStatus.FAILED.value
                self.db.commit()

                logger.warning(
                    f"Authorization failed: {merchant_member_id}, {callback_data.get('RtnMsg')}"
                )
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
            auth_record = (
                self.db.query(ECPayCreditAuthorization)
                .filter(
                    ECPayCreditAuthorization.merchant_member_id == merchant_member_id
                )
                .first()
            )

            if not auth_record:
                logger.error(f"Auth record not found for payment: {merchant_member_id}")
                return False

            subscription = (
                self.db.query(SaasSubscriptionORM)
                .filter(
                    SaasSubscriptionORM.auth_id == auth_record.id,
                    SaasSubscriptionORM.status.in_(
                        [
                            SubscriptionStatus.ACTIVE.value,
                            SubscriptionStatus.PAST_DUE.value,
                        ]
                    ),
                )
                .first()
            )

            if not subscription:
                logger.error(
                    f"Active subscription not found for auth: {auth_record.id}"
                )
                return False

            # Create payment record
            payment_record = SubscriptionPaymentORM(
                subscription_id=subscription.id,
                auth_id=auth_record.id,
                gwsr=gwsr,
                amount=amount,
                currency="TWD",
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end,
                ecpay_response=webhook_data,
                processed_at=datetime.now(),
            )

            if rtn_code == "1":  # Payment success
                payment_record.status = PaymentStatus.SUCCESS.value

                # Extend subscription period
                if auth_record.period_type == "M":
                    new_period_start = subscription.current_period_end + timedelta(
                        days=1
                    )
                    new_period_end = new_period_start + timedelta(days=30)
                else:  # Y
                    new_period_start = subscription.current_period_end + timedelta(
                        days=1
                    )
                    new_period_end = new_period_start + timedelta(days=365)

                subscription.current_period_start = new_period_start
                subscription.current_period_end = new_period_end
                subscription.status = SubscriptionStatus.ACTIVE.value

                # Update next payment date
                auth_record.next_pay_date = new_period_end
                auth_record.exec_times += 1

                # Send success notifications
                # Schedule notifications in background
                import asyncio

                asyncio.create_task(
                    self._handle_payment_success_notifications(
                        subscription, payment_record
                    )
                )

                logger.info(f"Payment successful: {gwsr}, subscription extended")

            else:  # Payment failed
                payment_record.status = PaymentStatus.FAILED.value
                payment_record.failure_reason = webhook_data.get("RtnMsg")

                # Handle failed payment (implement retry logic)
                self._handle_failed_payment(subscription, payment_record)

                # Send failure notifications
                # Schedule notifications in background
                import asyncio

                asyncio.create_task(
                    self._handle_payment_failure_notifications(
                        subscription, payment_record
                    )
                )

                logger.warning(
                    f"Payment failed: {gwsr}, reason: {payment_record.failure_reason}"
                )

            self.db.add(payment_record)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"💥 Error processing payment webhook: {e}")
            self.db.rollback()
            return False

    def _create_subscription(
        self, auth_record: ECPayCreditAuthorization
    ) -> SaasSubscription:
        """Create subscription after successful authorization."""

        # Determine plan details from amount
        plan_details = self._get_plan_from_amount(
            auth_record.period_amount * 100
        )  # Convert to cents

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
            current_period_end=period_end,
        )

        self.db.add(subscription)
        return subscription

    def _handle_failed_payment(
        self, subscription: SaasSubscription, payment: SubscriptionPayment
    ):
        """Handle failed payment with enhanced retry logic and grace period."""

        # Get retry count from recent payments
        recent_failures = (
            self.db.query(SubscriptionPaymentORM)
            .filter(
                SubscriptionPaymentORM.subscription_id == subscription.id,
                SubscriptionPaymentORM.status == PaymentStatus.FAILED.value,
                SubscriptionPaymentORM.created_at >= datetime.now() - timedelta(days=7),
            )
            .count()
        )

        payment.retry_count = recent_failures

        # Enhanced retry logic with grace period
        if recent_failures == 1:
            # First failure - mark as past due, start grace period
            subscription.status = SubscriptionStatus.PAST_DUE.value
            subscription.grace_period_ends_at = datetime.now() + timedelta(days=7)
            logger.warning(
                f"🟡 First payment failure for subscription {subscription.id} - grace period started"
            )

        elif recent_failures == 2:
            # Second failure - extend grace period slightly
            subscription.grace_period_ends_at = datetime.now() + timedelta(days=3)
            logger.warning(
                f"🟠 Second payment failure for subscription {subscription.id} - grace period extended"
            )

        elif recent_failures >= 3:
            # Third failure - check if grace period expired
            if (
                subscription.grace_period_ends_at
                and datetime.now() > subscription.grace_period_ends_at
            ):
                # Grace period expired - downgrade to FREE
                self._downgrade_to_free_plan(subscription)
                logger.error(
                    f"❌ Subscription {subscription.id} downgraded to FREE after {recent_failures} failures"
                )
            else:
                # Still within grace period
                logger.warning(
                    f"⚠️ Third payment failure for subscription {subscription.id} - final grace period"
                )

        # Schedule automated retry (handled by background task)
        self._schedule_payment_retry(subscription, payment)

        # Send payment failure notifications asynchronously
        # Only create task if there's a running event loop (production environment)
        import asyncio

        try:
            asyncio.create_task(
                self._send_payment_failure_notification(
                    subscription, payment, recent_failures
                )
            )
        except RuntimeError:
            # No event loop running (e.g., in tests) - skip async notification
            logger.debug("No event loop available for payment failure notification")
            pass

    def _get_plan_pricing(
        self, plan_id: str, billing_cycle: str
    ) -> Optional[Dict[str, Any]]:
        """Get plan pricing configuration."""

        pricing = {
            "STUDENT": {
                "monthly": {"amount_twd": 29900, "plan_name": "學習方案"},
                "annual": {"amount_twd": 300000, "plan_name": "學習方案"},
            },
            "PRO": {
                "monthly": {"amount_twd": 89900, "plan_name": "專業方案"},
                "annual": {"amount_twd": 899900, "plan_name": "專業方案"},
            },
            "ENTERPRISE": {
                "monthly": {"amount_twd": 299900, "plan_name": "企業方案"},
                "annual": {"amount_twd": 2999900, "plan_name": "企業方案"},
            },
        }

        return pricing.get(plan_id, {}).get(billing_cycle)

    def _get_plan_from_amount(self, amount_cents: int) -> Dict[str, str]:
        """Get plan details from payment amount."""

        amount_mapping = {
            29900: {"plan_id": "STUDENT", "plan_name": "學習方案"},
            300000: {"plan_id": "STUDENT", "plan_name": "學習方案"},
            89900: {"plan_id": "PRO", "plan_name": "專業方案"},
            899900: {"plan_id": "PRO", "plan_name": "專業方案"},
            299900: {"plan_id": "ENTERPRISE", "plan_name": "企業方案"},
            2999900: {"plan_id": "ENTERPRISE", "plan_name": "企業方案"},
        }

        return amount_mapping.get(
            amount_cents, {"plan_id": "PRO", "plan_name": "專業方案"}
        )

    def _downgrade_to_free_plan(self, subscription: SaasSubscription):
        """Downgrade subscription to FREE plan after payment failures."""

        # Update subscription to FREE plan
        subscription.plan_id = "FREE"
        subscription.status = SubscriptionStatus.ACTIVE.value  # Active but on FREE
        subscription.amount_twd = 0
        subscription.downgraded_at = datetime.now()
        subscription.downgrade_reason = "payment_failure"

        # Update user plan
        user = self.db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.plan = "FREE"
            user.updated_at = datetime.now()

        logger.info(
            f"📉 Subscription {subscription.id} downgraded to FREE plan due to payment failures"
        )

    def _schedule_payment_retry(
        self, subscription: SaasSubscription, payment: SubscriptionPayment
    ):
        """Schedule automated payment retry using exponential backoff."""

        retry_count = payment.retry_count or 0

        # Exponential backoff: 1 day, 3 days, 7 days
        retry_delays = [1, 3, 7]  # days

        if retry_count < len(retry_delays):
            retry_delay = retry_delays[retry_count]
            next_retry_at = datetime.now() + timedelta(days=retry_delay)

            # Store retry info (to be processed by background task)
            payment.next_retry_at = next_retry_at
            payment.max_retries = 3

            logger.info(
                f"📅 Payment retry scheduled for {next_retry_at} (attempt {retry_count + 1}/3)"
            )
        else:
            logger.warning(f"⚠️ Max retries reached for payment {payment.id}")

    async def _send_payment_failure_notification(
        self,
        subscription: SaasSubscription,
        payment: SubscriptionPayment,
        failure_count: int,
    ):
        """Send payment failure notifications to user."""

        user = self.db.query(User).filter(User.id == subscription.user_id).first()
        if not user:
            logger.error(f"User not found for subscription {subscription.id}")
            return

        # Determine notification type based on failure count
        if failure_count == 1:
            notification_type = "first_payment_failure"
            subject = "付款失敗通知 - Payment Failure Notice"
            urgency = "medium"
        elif failure_count == 2:
            notification_type = "second_payment_failure"
            subject = "第二次付款失敗 - Second Payment Failure"
            urgency = "high"
        else:
            notification_type = "final_payment_failure"
            subject = "最終付款失敗通知 - Final Payment Failure Notice"
            urgency = "critical"

        # Create notification record (to be sent by background task)
        notification_data = {
            "user_id": user.id,
            "user_email": user.email,
            "subscription_id": subscription.id,
            "payment_id": payment.id,
            "failure_count": failure_count,
            "grace_period_ends": (
                subscription.grace_period_ends_at.isoformat()
                if subscription.grace_period_ends_at
                else None
            ),
            "amount_twd": subscription.amount_twd,
            "plan_name": subscription.plan_id,
            "notification_type": notification_type,
            "subject": subject,
            "urgency": urgency,
        }

        # Send email notification via notification service
        try:
            await self.notification_service.send_payment_failure_notification(
                user_email=user.email,
                payment_details={
                    "amount": subscription.amount_twd,
                    "plan_name": subscription.plan_id,
                    "failure_count": notification_data.get("failure_count", 0),
                    "next_retry_date": (
                        payment.next_retry_at.strftime("%Y-%m-%d")
                        if payment.next_retry_at
                        else "N/A"
                    ),
                    "grace_period_ends": (
                        subscription.grace_period_ends_at.strftime("%Y-%m-%d")
                        if subscription.grace_period_ends_at
                        else "N/A"
                    ),
                },
            )
            logger.info(f"📧 Payment failure notification sent to {user.email}")
        except Exception as e:
            logger.error(f"❌ Failed to send payment failure notification: {e}")

        logger.info(
            f"📧 Payment failure notification processed: {notification_type} for {user.email}"
        )

    def _generate_check_mac_value(self, data: Dict[str, str]) -> str:
        """
        Generate ECPay CheckMacValue following official specification exactly.

        Official 8-step process:
        1. Remove CheckMacValue parameter
        2. Sort parameters A-Z
        3. Create key=value query string
        4. Add HashKey and HashIV: HashKey={key}&{query}&HashIV={iv}
        5. URL encode entire string
        6. Convert to lowercase
        7. .NET style replacements
        8. SHA256 hash and convert to uppercase
        """

        # Step 1: Remove CheckMacValue if present
        clean_data = {k: v for k, v in data.items() if k != "CheckMacValue"}

        # Step 2: Sort parameters by key (A-Z)
        sorted_items = sorted(clean_data.items())

        # Step 3: Create key=value query string
        param_strings = []
        for key, value in sorted_items:
            param_strings.append(f"{key}={value}")
        query_string = "&".join(param_strings)

        # Step 4: Add HashKey and HashIV
        raw_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"
        # Step 5: URL encode entire string
        encoded_string = urllib.parse.quote_plus(raw_string)

        # Step 6: Convert to lowercase
        encoded_lower = encoded_string.lower()

        # Step 7: .NET style replacements
        replacements = {
            "%2d": "-",
            "%5f": "_",
            "%2e": ".",
            "%21": "!",
            "%2a": "*",
            "%28": "(",
            "%29": ")",
        }

        final_string = encoded_lower
        for old, new in replacements.items():
            final_string = final_string.replace(old, new)

        # Step 8: SHA256 hash and convert to uppercase
        return hashlib.sha256(final_string.encode("utf-8")).hexdigest().upper()

    def _verify_callback(self, callback_data: Dict[str, str]) -> bool:
        """Verify ECPay callback CheckMacValue."""

        received_mac = callback_data.get("CheckMacValue", "")
        calculated_mac = self._generate_check_mac_value(callback_data)

        return received_mac.upper() == calculated_mac.upper()

    async def cancel_authorization(self, auth_id: str) -> bool:
        """Cancel ECPay credit card authorization."""

        try:
            auth_record = (
                self.db.query(ECPayCreditAuthorization)
                .filter(ECPayCreditAuthorization.id == auth_id)
                .first()
            )

            if not auth_record:
                return False

            # Call ECPay API to cancel authorization
            try:
                cancel_result = await self.ecpay_client.cancel_credit_authorization(
                    auth_code=auth_record.auth_code,
                    merchant_trade_no=auth_record.merchant_trade_no,
                )

                if cancel_result.get("success"):
                    logger.info(
                        f"✅ ECPay authorization cancelled successfully: {auth_record.auth_code}"
                    )
                    auth_record.auth_status = ECPayAuthStatus.CANCELLED.value
                else:
                    logger.error(
                        f"❌ ECPay cancel failed: {cancel_result.get('message')}"
                    )
                    return False

            except Exception as e:
                logger.error(f"❌ ECPay API call failed: {e}")
                # Still mark as cancelled locally for data consistency
                auth_record.auth_status = ECPayAuthStatus.CANCELLED.value

            # Cancel associated subscriptions
            subscriptions = (
                self.db.query(SaasSubscriptionORM)
                .filter(
                    SaasSubscriptionORM.auth_id == auth_record.id,
                    SaasSubscriptionORM.status == SubscriptionStatus.ACTIVE.value,
                )
                .all()
            )

            for subscription in subscriptions:
                subscription.status = SubscriptionStatus.CANCELLED.value
                subscription.cancelled_at = datetime.now()

            self.db.commit()

            logger.info(f"🚫 Authorization cancelled: {auth_id}")
            return True

        except Exception as e:
            logger.error(f"💥 Error cancelling authorization {auth_id}: {e}")
            self.db.rollback()
            return False

    async def check_and_handle_expired_subscriptions(self):
        """Check for expired subscriptions and handle them appropriately."""

        try:
            # Find subscriptions past grace period
            expired_subscriptions = (
                self.db.query(SaasSubscriptionORM)
                .filter(
                    SaasSubscriptionORM.status == SubscriptionStatus.PAST_DUE.value,
                    SaasSubscriptionORM.grace_period_ends_at < datetime.now(),
                )
                .all()
            )

            for subscription in expired_subscriptions:
                logger.info(f"⏰ Processing expired subscription: {subscription.id}")
                self._downgrade_to_free_plan(subscription)

                # Send final downgrade notification
                user = (
                    self.db.query(User).filter(User.id == subscription.user_id).first()
                )
                if user:
                    logger.info(f"📧 Sending downgrade notification to {user.email}")
                    # Send downgrade notification email
                    try:
                        await (
                            self.notification_service.send_plan_downgrade_notification(
                                user_email=user.email,
                                downgrade_details={
                                    "old_plan": subscription.plan_name,
                                    "new_plan": "FREE",
                                    "effective_date": (
                                        datetime.now().strftime("%Y-%m-%d")
                                    ),
                                    "reason": "Payment failure after grace period",
                                },
                            )
                        )
                        logger.info(f"📧 Downgrade notification sent to {user.email}")
                    except Exception as e:
                        logger.error(f"❌ Failed to send downgrade notification: {e}")

            if expired_subscriptions:
                self.db.commit()
                logger.info(
                    f"✅ Processed {len(expired_subscriptions)} expired subscriptions"
                )

            return True

        except Exception as e:
            logger.error(f"💥 Error processing expired subscriptions: {e}")
            self.db.rollback()
            return False

    async def retry_failed_payments(self):
        """Process scheduled payment retries."""

        try:
            # Find payments scheduled for retry
            payments_to_retry = (
                self.db.query(SubscriptionPaymentORM)
                .filter(
                    SubscriptionPaymentORM.status == PaymentStatus.FAILED.value,
                    SubscriptionPaymentORM.next_retry_at <= datetime.now(),
                    SubscriptionPaymentORM.retry_count
                    < SubscriptionPaymentORM.max_retries,
                )
                .all()
            )

            for payment in payments_to_retry:
                logger.info(f"🔄 Retrying failed payment: {payment.id}")

                # Get subscription and auth info
                subscription = (
                    self.db.query(SaasSubscriptionORM)
                    .filter(SaasSubscriptionORM.id == payment.subscription_id)
                    .first()
                )

                if not subscription:
                    logger.error(f"Subscription not found for payment {payment.id}")
                    continue

                auth_record = (
                    self.db.query(ECPayCreditAuthorization)
                    .filter(ECPayCreditAuthorization.id == subscription.auth_id)
                    .first()
                )

                if not auth_record:
                    logger.error(
                        f"Auth record not found for subscription {subscription.id}"
                    )
                    continue

                # Implement ECPay manual retry API call
                try:
                    retry_result = await self.ecpay_client.retry_payment(
                        auth_code=auth_record.auth_code,
                        merchant_trade_no=auth_record.merchant_trade_no,
                        amount=subscription.amount_twd,
                    )

                    payment.retry_count += 1
                    payment.last_retry_at = datetime.now()

                    if retry_result.get("success"):
                        logger.info(
                            f"✅ ECPay payment retry successful for subscription {subscription.id}"
                        )
                        payment.status = PaymentStatus.PAID.value
                        subscription.status = SubscriptionStatus.ACTIVE.value

                        # Send success notification
                        await self.notification_service.send_payment_retry_notification(
                            user_email=subscription.user.email,
                            retry_details={
                                "amount": subscription.amount_twd,
                                "plan_name": subscription.plan_id,
                                "payment_date": (datetime.now().strftime("%Y-%m-%d")),
                                "retry_count": payment.retry_count,
                            },
                        )
                        continue
                    else:
                        logger.error(
                            f"❌ ECPay retry failed: {retry_result.get('message')}"
                        )

                except Exception as e:
                    logger.error(f"❌ ECPay retry API call failed: {e}")
                    payment.retry_count += 1
                    payment.last_retry_at = datetime.now()

                if payment.retry_count < payment.max_retries:
                    # Schedule next retry
                    retry_delays = [1, 3, 7]  # days
                    if payment.retry_count < len(retry_delays):
                        next_delay = retry_delays[payment.retry_count]
                        payment.next_retry_at = datetime.now() + timedelta(
                            days=next_delay
                        )
                        logger.info(f"📅 Next retry scheduled in {next_delay} days")
                    else:
                        payment.next_retry_at = None
                        logger.warning(
                            f"⚠️ Max retries reached for payment {payment.id}"
                        )
                else:
                    payment.next_retry_at = None
                    logger.warning(f"❌ Payment retry limit exceeded: {payment.id}")

            if payments_to_retry:
                self.db.commit()
                logger.info(f"✅ Processed {len(payments_to_retry)} payment retries")

            return True

        except Exception as e:
            logger.error(f"💥 Error retrying failed payments: {e}")
            self.db.rollback()
            return False
            return True

        except Exception as e:
            logger.error(f"Error cancelling authorization: {e}")
            self.db.rollback()
            return False

    def calculate_prorated_charge(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str,
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
        current_remaining_value = (
            int((subscription.amount_twd * remaining_days) / total_days)
            if total_days > 0
            else 0
        )

        # Get new plan pricing
        new_plan_pricing = self._get_plan_pricing(new_plan_id, new_billing_cycle)
        if not new_plan_pricing:
            raise ValueError(
                f"Invalid plan: {new_plan_id} with cycle: {new_billing_cycle}"
            )

        # Calculate new plan prorated cost
        new_plan_prorated_cost = (
            int((new_plan_pricing["amount_twd"] * remaining_days) / total_days)
            if total_days > 0
            else new_plan_pricing["amount_twd"]
        )

        # Net charge (additional amount needed)
        net_charge = max(0, new_plan_prorated_cost - current_remaining_value)

        return {
            "current_plan_remaining_value": current_remaining_value,
            "new_plan_prorated_cost": new_plan_prorated_cost,
            "net_charge": net_charge,
            "effective_date": datetime.now().isoformat(),
        }

    async def upgrade_subscription(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str,
    ) -> Dict[str, Any]:
        """Upgrade subscription plan with prorated billing."""

        try:
            # Calculate prorated charge
            proration = self.calculate_prorated_charge(
                subscription, new_plan_id, new_billing_cycle
            )

            # Get new plan details
            new_plan_pricing = self._get_plan_pricing(new_plan_id, new_billing_cycle)

            # Process net charge via ECPay if required
            if proration["net_charge"] > 0:
                logger.info(
                    f"💳 Processing prorated charge: {proration['net_charge']} cents"
                )

                try:
                    # Process the additional charge via ECPay
                    merchant_trade_no = (
                        f"UPGRADE_{subscription.id}_{int(datetime.now().timestamp())}"
                    )
                    payment_result = await self.ecpay_client.process_payment(
                        merchant_trade_no=merchant_trade_no,
                        amount=proration["net_charge"],
                        item_name=f"Plan upgrade to {new_plan_id}",
                    )

                    if payment_result.get("success"):
                        logger.info("✅ Prorated payment processed successfully")

                        # Create payment record
                        payment = SubscriptionPayment(
                            subscription_id=subscription.id,
                            merchant_trade_no=merchant_trade_no,
                            amount_twd=proration["net_charge"],
                            status=PaymentStatus.PAID.value,
                            payment_date=datetime.now(),
                            retry_count=0,
                            max_retries=3,
                        )
                        self.db.add(payment)

                    else:
                        logger.error(
                            f"❌ Prorated payment failed: {payment_result.get('message')}"
                        )
                        raise Exception("Payment processing failed")

                except Exception as e:
                    logger.error(f"❌ Failed to process prorated payment: {e}")
                    raise Exception(f"Payment processing failed: {str(e)}")

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
                "prorated_charge": proration["net_charge"],
            }

        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            self.db.rollback()
            raise

    def schedule_downgrade(
        self,
        subscription: SaasSubscription,
        new_plan_id: str,
        new_billing_cycle: str,
    ) -> Dict[str, Any]:
        """Schedule subscription downgrade for period end."""

        try:
            # Handle FREE plan downgrade specially (no pricing needed)
            if new_plan_id == "FREE":
                new_plan_pricing = {"amount_twd": 0, "plan_name": "免費方案"}
            else:
                # Get new plan details
                new_plan_pricing = self._get_plan_pricing(
                    new_plan_id, new_billing_cycle
                )
                if not new_plan_pricing:
                    raise ValueError(
                        f"Invalid plan: {new_plan_id} with cycle: {new_billing_cycle}"
                    )

            # For simplicity, we'll use a custom field or create a pending changes table
            # For now, we'll store the pending change in subscription metadata
            subscription.cancellation_reason = (
                f"DOWNGRADE_TO:{new_plan_id}:{new_billing_cycle}"
            )
            subscription.cancel_at_period_end = True

            self.db.commit()

            logger.info(
                f"Subscription {subscription.id} scheduled for downgrade to {new_plan_id}"
            )

            return {
                "effective_date": subscription.current_period_end.isoformat(),
                "new_plan": new_plan_pricing,
            }

        except Exception as e:
            logger.error(f"Error scheduling downgrade: {e}")
            self.db.rollback()
            raise

    async def cancel_subscription(
        self,
        subscription: SaasSubscription,
        immediate: bool = False,
        reason: str = None,
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
                    subscription.auth_record.auth_status = (
                        ECPayAuthStatus.CANCELLED.value
                    )

                # Call ECPay API to cancel authorization
                try:
                    cancel_result = await self.ecpay_client.cancel_credit_authorization(
                        auth_code=subscription.auth_record.auth_code,
                        merchant_trade_no=subscription.auth_record.merchant_trade_no,
                    )

                    if cancel_result.get("success"):
                        logger.info(
                            f"✅ ECPay authorization cancelled successfully for subscription {subscription.id}"
                        )
                    else:
                        logger.error(
                            f"❌ ECPay cancel failed: {cancel_result.get('message')}"
                        )

                except Exception as e:
                    logger.error(f"❌ ECPay API call failed during cancellation: {e}")

                effective_date = datetime.now()

                # Calculate refund if applicable
                if subscription.billing_cycle == "monthly":
                    days_in_cycle = 30
                elif subscription.billing_cycle == "yearly":
                    days_in_cycle = 365
                else:
                    days_in_cycle = 30  # default

                days_since_renewal = (
                    effective_date - subscription.current_period_start
                ).days
                refund_amount = self.ecpay_client.calculate_refund_amount(
                    original_amount=subscription.amount_twd,
                    days_used=days_since_renewal,
                    total_days=days_in_cycle,
                )

            else:
                # Period-end cancellation
                subscription.cancel_at_period_end = True
                subscription.cancellation_reason = reason or "Period-end cancellation"

                effective_date = subscription.current_period_end
                refund_amount = 0

            self.db.commit()

            logger.info(
                f"Subscription {subscription.id} cancelled ({'immediate' if immediate else 'period-end'})"
            )

            return {
                "effective_date": effective_date.isoformat(),
                "refund_amount": refund_amount,
            }

        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            self.db.rollback()
            raise

    async def send_payment_notification(
        self,
        user_id: str,
        notification_type: str,
        subscription: SaasSubscription = None,
        payment: SubscriptionPayment = None,
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
                "user_name": getattr(user, "name", user.email.split("@")[0]),
                "timestamp": datetime.now().isoformat(),
                "notification_type": notification_type,
            }

            if subscription:
                notification_data.update(
                    {
                        "plan_name": subscription.plan_name,
                        "billing_cycle": subscription.billing_cycle,
                        "amount": f"NT${subscription.amount_twd / 100:,.0f}",
                        "next_billing_date": (
                            subscription.current_period_end.isoformat()
                            if subscription.current_period_end
                            else None
                        ),
                    }
                )

            if payment:
                notification_data.update(
                    {
                        "payment_amount": f"NT${payment.amount / 100:,.0f}",
                        "payment_date": (
                            payment.processed_at.isoformat()
                            if payment.processed_at
                            else None
                        ),
                        "failure_reason": payment.failure_reason,
                    }
                )

            # Log notification (in production, this would send email/SMS)
            logger.info(f"📧 Notification: {notification_type} for user {user.email}")
            logger.info(f"📊 Notification data: {notification_data}")

            # Send actual notification via notification service
            try:
                if subscription.status == SubscriptionStatus.CANCELLED.value:
                    await self.notification_service.send_subscription_cancellation_notification(
                        user_email=user.email,
                        cancellation_details={
                            "plan_name": subscription.plan_name,
                            "effective_date": (
                                (subscription.cancelled_at or datetime.now()).strftime(
                                    "%Y-%m-%d"
                                )
                            ),
                            "refund_amount": (
                                0
                            ),  # TODO: Calculate based on subscription data
                            "reason": (
                                subscription.cancellation_reason or "User requested"
                            ),
                        },
                    )
                    logger.info(f"📧 Cancellation notification sent to {user.email}")
                else:
                    logger.info("📧 Notification skipped - subscription not cancelled")

            except Exception as e:
                logger.error(f"❌ Failed to send cancellation notification: {e}")

        except Exception as e:
            logger.error(
                f"Failed to send notification {notification_type} to user {user_id}: {e}"
            )

    async def _handle_payment_success_notifications(
        self, subscription: SaasSubscription, payment: SubscriptionPayment
    ):
        """Handle notifications for successful payments."""

        try:
            # Send payment success notification
            await self.send_payment_notification(
                subscription.user_id,
                "payment_success",
                subscription=subscription,
                payment=payment,
            )

            # Send subscription renewal notification
            await self.send_payment_notification(
                subscription.user_id,
                "subscription_renewed",
                subscription=subscription,
                payment=payment,
            )

            logger.info(
                f"✅ Payment success notifications sent for subscription {subscription.id}"
            )

        except Exception as e:
            logger.error(f"Failed to send payment success notifications: {e}")

    async def _handle_payment_failure_notifications(
        self, subscription: SaasSubscription, payment: SubscriptionPayment
    ):
        """Handle notifications for failed payments."""

        try:
            # Send payment failure notification
            await self.send_payment_notification(
                subscription.user_id,
                "payment_failed",
                subscription=subscription,
                payment=payment,
            )

            # Check if this triggers grace period
            if payment.retry_count >= 3:
                await self.send_payment_notification(
                    subscription.user_id,
                    "subscription_past_due",
                    subscription=subscription,
                    payment=payment,
                )

            # Send retry notification if applicable
            if payment.retry_count < 3:
                await self.send_payment_notification(
                    subscription.user_id,
                    "payment_retry_scheduled",
                    subscription=subscription,
                    payment=payment,
                )

            logger.info(
                f"❌ Payment failure notifications sent for subscription {subscription.id}"
            )

        except Exception as e:
            logger.error(f"Failed to send payment failure notifications: {e}")
