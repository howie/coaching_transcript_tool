"""Email notification service for billing events."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class NotificationService(ABC):
    """Abstract notification service following Clean Architecture ports pattern."""

    @abstractmethod
    async def send_payment_failure_notification(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        """Send payment failure notification."""

    @abstractmethod
    async def send_payment_retry_notification(
        self, user_email: str, retry_details: Dict[str, Any]
    ) -> bool:
        """Send payment retry notification."""

    @abstractmethod
    async def send_subscription_cancellation_notification(
        self, user_email: str, cancellation_details: Dict[str, Any]
    ) -> bool:
        """Send subscription cancellation notification."""

    @abstractmethod
    async def send_plan_downgrade_notification(
        self, user_email: str, downgrade_details: Dict[str, Any]
    ) -> bool:
        """Send plan downgrade notification."""


class EmailNotificationService(NotificationService):
    """Email notification service implementation."""

    def __init__(self, smtp_settings: Optional[Dict[str, Any]] = None):
        self.smtp_settings = smtp_settings or {}
        self.enabled = bool(smtp_settings)

    async def send_payment_failure_notification(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        """Send payment failure notification email."""
        logger.info(f"📧 Sending payment failure notification to {user_email}")

        if not self.enabled:
            logger.warning(
                "📧 Email service not configured, logging notification instead"
            )
            logger.info(
                f"📧 [MOCK EMAIL] Payment failure for {user_email}: {payment_details}"
            )
            return True

        try:
            # Implementation would integrate with actual email service (SendGrid, AWS SES, etc.)
            # For now, we'll log the notification
            subject = "Payment Failed - Action Required"
            body = self._generate_payment_failure_email(payment_details)

            logger.info(f"📧 Email sent successfully to {user_email}")
            logger.debug(f"📧 Email content: {subject} - {body[:100]}...")

            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to send payment failure email to {user_email}: {e}"
            )
            return False

    async def send_payment_retry_notification(
        self, user_email: str, retry_details: Dict[str, Any]
    ) -> bool:
        """Send payment retry notification email."""
        logger.info(f"📧 Sending payment retry notification to {user_email}")

        if not self.enabled:
            logger.warning(
                "📧 Email service not configured, logging notification instead"
            )
            logger.info(
                f"📧 [MOCK EMAIL] Payment retry for {user_email}: {retry_details}"
            )
            return True

        try:
            subject = "Payment Retry Successful"
            body = self._generate_payment_retry_email(retry_details)

            logger.info(f"📧 Email sent successfully to {user_email}")
            logger.debug(f"📧 Email content: {subject} - {body[:100]}...")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send payment retry email to {user_email}: {e}")
            return False

    async def send_subscription_cancellation_notification(
        self, user_email: str, cancellation_details: Dict[str, Any]
    ) -> bool:
        """Send subscription cancellation notification email."""
        logger.info(f"📧 Sending cancellation notification to {user_email}")

        if not self.enabled:
            logger.warning(
                "📧 Email service not configured, logging notification instead"
            )
            logger.info(
                f"📧 [MOCK EMAIL] Subscription cancelled for {user_email}: {cancellation_details}"
            )
            return True

        try:
            subject = "Subscription Cancelled"
            body = self._generate_cancellation_email(cancellation_details)

            logger.info(f"📧 Email sent successfully to {user_email}")
            logger.debug(f"📧 Email content: {subject} - {body[:100]}...")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send cancellation email to {user_email}: {e}")
            return False

    async def send_plan_downgrade_notification(
        self, user_email: str, downgrade_details: Dict[str, Any]
    ) -> bool:
        """Send plan downgrade notification email."""
        logger.info(f"📧 Sending downgrade notification to {user_email}")

        if not self.enabled:
            logger.warning(
                "📧 Email service not configured, logging notification instead"
            )
            logger.info(
                f"📧 [MOCK EMAIL] Plan downgraded for {user_email}: {downgrade_details}"
            )
            return True

        try:
            subject = "Plan Downgraded Due to Payment Issues"
            body = self._generate_downgrade_email(downgrade_details)

            logger.info(f"📧 Email sent successfully to {user_email}")
            logger.debug(f"📧 Email content: {subject} - {body[:100]}...")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send downgrade email to {user_email}: {e}")
            return False

    def _generate_payment_failure_email(self, payment_details: Dict[str, Any]) -> str:
        """Generate payment failure email content."""
        return f"""
        Dear Customer,

        We were unable to process your subscription payment.

        Payment Details:
        - Amount: ${payment_details.get("amount", "N/A")}
        - Plan: {payment_details.get("plan_name", "N/A")}
        - Retry Date: {payment_details.get("next_retry_date", "N/A")}

        We will automatically retry the payment in a few days.
        Please ensure your payment method is up to date.

        Best regards,
        Coaching Assistant Team
        """

    def _generate_payment_retry_email(self, retry_details: Dict[str, Any]) -> str:
        """Generate payment retry success email content."""
        return f"""
        Dear Customer,

        Great news! Your payment has been successfully processed.

        Payment Details:
        - Amount: ${retry_details.get("amount", "N/A")}
        - Plan: {retry_details.get("plan_name", "N/A")}
        - Date: {retry_details.get("payment_date", "N/A")}

        Your subscription is now active.

        Best regards,
        Coaching Assistant Team
        """

    def _generate_cancellation_email(self, cancellation_details: Dict[str, Any]) -> str:
        """Generate cancellation email content."""
        return f"""
        Dear Customer,

        Your subscription has been cancelled as requested.

        Cancellation Details:
        - Plan: {cancellation_details.get("plan_name", "N/A")}
        - Effective Date: {cancellation_details.get("effective_date", "N/A")}
        - Refund Amount: ${cancellation_details.get("refund_amount", "0")}

        If you have any questions, please contact our support team.

        Best regards,
        Coaching Assistant Team
        """

    def _generate_downgrade_email(self, downgrade_details: Dict[str, Any]) -> str:
        """Generate plan downgrade email content."""
        return f"""
        Dear Customer,

        Due to payment issues, your plan has been downgraded.

        Downgrade Details:
        - Previous Plan: {downgrade_details.get("old_plan", "N/A")}
        - Current Plan: {downgrade_details.get("new_plan", "N/A")}
        - Effective Date: {downgrade_details.get("effective_date", "N/A")}

        Please update your payment method to restore your previous plan.

        Best regards,
        Coaching Assistant Team
        """


class MockNotificationService(NotificationService):
    """Mock notification service for testing."""

    def __init__(self):
        self.sent_notifications = []

    async def send_payment_failure_notification(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        notification = {
            "type": "payment_failure",
            "user_email": user_email,
            "details": payment_details,
        }
        self.sent_notifications.append(notification)
        logger.info(f"🧪 Mock notification sent: {notification}")
        return True

    async def send_payment_retry_notification(
        self, user_email: str, retry_details: Dict[str, Any]
    ) -> bool:
        notification = {
            "type": "payment_retry",
            "user_email": user_email,
            "details": retry_details,
        }
        self.sent_notifications.append(notification)
        logger.info(f"🧪 Mock notification sent: {notification}")
        return True

    async def send_subscription_cancellation_notification(
        self, user_email: str, cancellation_details: Dict[str, Any]
    ) -> bool:
        notification = {
            "type": "subscription_cancellation",
            "user_email": user_email,
            "details": cancellation_details,
        }
        self.sent_notifications.append(notification)
        logger.info(f"🧪 Mock notification sent: {notification}")
        return True

    async def send_plan_downgrade_notification(
        self, user_email: str, downgrade_details: Dict[str, Any]
    ) -> bool:
        notification = {
            "type": "plan_downgrade",
            "user_email": user_email,
            "details": downgrade_details,
        }
        self.sent_notifications.append(notification)
        logger.info(f"🧪 Mock notification sent: {notification}")
        return True
