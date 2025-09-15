"""Subscription repository implementation using SQLAlchemy."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ....core.repositories.ports import SubscriptionRepoPort
from ....models.ecpay_subscription import (
    SaasSubscription,
    SubscriptionPayment,
    ECPayCreditAuthorization,
    SubscriptionStatus,
)


class SubscriptionRepository(SubscriptionRepoPort):
    """SQLAlchemy implementation of SubscriptionRepoPort."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_subscription_by_user_id(self, user_id: UUID) -> Optional[SaasSubscription]:
        """Get active subscription for user."""
        return (
            self.db_session.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == user_id,
                SaasSubscription.status.in_(
                    [
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.PAST_DUE.value,
                        SubscriptionStatus.UNPAID.value,
                        SubscriptionStatus.TRIALING.value,
                    ]
                ),
            )
            .first()
        )

    def save_subscription(self, subscription: SaasSubscription) -> SaasSubscription:
        """Save or update subscription."""
        self.db_session.add(subscription)
        self.db_session.commit()
        self.db_session.refresh(subscription)
        return subscription

    def get_credit_authorization_by_user_id(
        self, user_id: UUID
    ) -> Optional[ECPayCreditAuthorization]:
        """Get credit authorization for user."""
        return (
            self.db_session.query(ECPayCreditAuthorization)
            .filter(ECPayCreditAuthorization.user_id == user_id)
            .order_by(ECPayCreditAuthorization.created_at.desc())
            .first()
        )

    def save_credit_authorization(
        self, auth: ECPayCreditAuthorization
    ) -> ECPayCreditAuthorization:
        """Save or update credit authorization."""
        self.db_session.add(auth)
        self.db_session.commit()
        self.db_session.refresh(auth)
        return auth

    def save_payment(self, payment: SubscriptionPayment) -> SubscriptionPayment:
        """Save subscription payment record."""
        self.db_session.add(payment)
        self.db_session.commit()
        self.db_session.refresh(payment)
        return payment

    def get_payments_for_subscription(
        self, subscription_id: UUID
    ) -> List[SubscriptionPayment]:
        """Get all payments for a subscription."""
        return (
            self.db_session.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(SubscriptionPayment.created_at.desc())
            .all()
        )

    def update_subscription_status(
        self, subscription_id: UUID, status: SubscriptionStatus
    ) -> SaasSubscription:
        """Update subscription status."""
        subscription = (
            self.db_session.query(SaasSubscription)
            .filter(SaasSubscription.id == subscription_id)
            .first()
        )
        
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        # Persist enum value as string
        subscription.status = status.value if hasattr(status, "value") else status
        self.db_session.commit()
        self.db_session.refresh(subscription)
        return subscription


def create_subscription_repository(db_session: Session) -> SubscriptionRepoPort:
    """Factory function to create SubscriptionRepository instance."""
    return SubscriptionRepository(db_session)
