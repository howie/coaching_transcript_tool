"""Subscription repository implementation using SQLAlchemy with Clean Architecture."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ....core.models.subscription import (
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)
from ....core.repositories.ports import SubscriptionRepoPort
from ..models.subscription_model import (
    ECPayCreditAuthorizationModel,
    SaasSubscriptionModel,
    SubscriptionPaymentModel,
)

logger = logging.getLogger(__name__)


class SubscriptionRepository(SubscriptionRepoPort):
    """SQLAlchemy implementation of SubscriptionRepoPort."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_subscription_by_user_id(self, user_id: UUID) -> Optional[SaasSubscription]:
        """Get active subscription for user."""
        try:
            # Validate session state before query
            if not self.db_session.is_active:
                logger.warning(
                    f"Database session is not active for subscription query, user {user_id}"
                )
                return None

            orm_subscription = (
                self.db_session.query(SaasSubscriptionModel)
                .filter(
                    SaasSubscriptionModel.user_id == user_id,
                    SaasSubscriptionModel.status.in_(
                        [
                            SubscriptionStatus.ACTIVE,
                            SubscriptionStatus.PAST_DUE,
                            SubscriptionStatus.UNPAID,
                            SubscriptionStatus.TRIALING,
                        ]
                    ),
                )
                .first()
            )

            return orm_subscription.to_domain() if orm_subscription else None
        except SQLAlchemyError as e:
            logger.error(
                f"Database error in get_subscription_by_user_id for user {user_id}: {e}"
            )
            self.db_session.rollback()
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in get_subscription_by_user_id for user {user_id}: {e}"
            )
            self.db_session.rollback()
            raise

    def save_subscription(self, subscription: SaasSubscription) -> SaasSubscription:
        """Save or update subscription."""
        existing = None
        if subscription.id:
            existing = self.db_session.get(SaasSubscriptionModel, subscription.id)

        if existing:
            existing.update_from_domain(subscription)
            self.db_session.flush()
            return existing.to_domain()

        orm_subscription = SaasSubscriptionModel.from_domain(subscription)
        self.db_session.add(orm_subscription)
        self.db_session.flush()  # Ensure ID is generated without committing
        return orm_subscription.to_domain()

    def get_credit_authorization_by_user_id(
        self, user_id: UUID
    ) -> Optional[ECPayCreditAuthorization]:
        """Get credit authorization for user."""
        try:
            # Validate session state before query
            if not self.db_session.is_active:
                logger.warning(
                    f"Database session is not active for authorization query, user {user_id}"
                )
                return None

            orm_auth = (
                self.db_session.query(ECPayCreditAuthorizationModel)
                .filter(ECPayCreditAuthorizationModel.user_id == user_id)
                .order_by(ECPayCreditAuthorizationModel.created_at.desc())
                .first()
            )

            return orm_auth.to_domain() if orm_auth else None
        except SQLAlchemyError as e:
            logger.error(
                f"Database error in get_credit_authorization_by_user_id for user {user_id}: {e}"
            )
            self.db_session.rollback()
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in get_credit_authorization_by_user_id for user {user_id}: {e}"
            )
            self.db_session.rollback()
            raise

    def save_credit_authorization(
        self, auth: ECPayCreditAuthorization
    ) -> ECPayCreditAuthorization:
        """Save or update credit authorization."""
        orm_auth = ECPayCreditAuthorizationModel.from_domain(auth)
        self.db_session.add(orm_auth)
        self.db_session.flush()  # Ensure ID is generated without committing
        return orm_auth.to_domain()

    def save_payment(self, payment: SubscriptionPayment) -> SubscriptionPayment:
        """Save subscription payment record."""
        orm_payment = SubscriptionPaymentModel.from_domain(payment)
        self.db_session.add(orm_payment)
        self.db_session.flush()  # Ensure ID is generated without committing
        return orm_payment.to_domain()

    def get_payments_for_subscription(
        self, subscription_id: UUID
    ) -> List[SubscriptionPayment]:
        """Get all payments for a subscription."""
        orm_payments = (
            self.db_session.query(SubscriptionPaymentModel)
            .filter(SubscriptionPaymentModel.subscription_id == subscription_id)
            .order_by(SubscriptionPaymentModel.created_at.desc())
            .all()
        )
        return [payment.to_domain() for payment in orm_payments]

    def update_subscription_status(
        self, subscription_id: UUID, status: SubscriptionStatus
    ) -> SaasSubscription:
        """Update subscription status."""
        orm_subscription = (
            self.db_session.query(SaasSubscriptionModel)
            .filter(SaasSubscriptionModel.id == subscription_id)
            .first()
        )

        if not orm_subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")

        # Update the enum directly
        orm_subscription.status = status
        self.db_session.flush()  # Ensure changes are flushed without committing
        return orm_subscription.to_domain()


def create_subscription_repository(
    db_session: Session,
) -> SubscriptionRepoPort:
    """Factory function to create SubscriptionRepository instance."""
    return SubscriptionRepository(db_session)
