"""FastAPI dependencies for Clean Architecture dependency injection.

This module provides dependency injection for use cases following Clean Architecture principles.
All use cases are created through factories that inject the appropriate repository implementations.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...infrastructure.factories import (
    UsageTrackingServiceFactory,
    SessionServiceFactory,
    PlanServiceFactory,
    SubscriptionServiceFactory,
)
from ...core.services.usage_tracking_use_case import CreateUsageLogUseCase, GetUserUsageUseCase
from ...core.services.session_management_use_case import (
    SessionCreationUseCase,
    SessionRetrievalUseCase,
    SessionStatusUpdateUseCase,
    SessionTranscriptUpdateUseCase,
)
from ...core.services.plan_management_use_case import (
    PlanRetrievalUseCase,
    PlanValidationUseCase,
)
from ...core.services.subscription_management_use_case import (
    SubscriptionCreationUseCase,
    SubscriptionRetrievalUseCase,
    SubscriptionModificationUseCase,
)


def get_usage_log_use_case(
    db: Session = Depends(get_db)
) -> CreateUsageLogUseCase:
    """Dependency to inject CreateUsageLogUseCase with proper repositories."""
    return UsageTrackingServiceFactory.create_usage_log_use_case(db)


def get_user_usage_use_case(
    db: Session = Depends(get_db)
) -> GetUserUsageUseCase:
    """Dependency to inject GetUserUsageUseCase with proper repositories."""
    return UsageTrackingServiceFactory.create_user_usage_use_case(db)


# Session Management Dependencies
def get_session_creation_use_case(
    db: Session = Depends(get_db)
) -> SessionCreationUseCase:
    """Dependency to inject SessionCreationUseCase."""
    return SessionServiceFactory.create_session_creation_use_case(db)


def get_session_retrieval_use_case(
    db: Session = Depends(get_db)
) -> SessionRetrievalUseCase:
    """Dependency to inject SessionRetrievalUseCase."""
    return SessionServiceFactory.create_session_retrieval_use_case(db)


def get_session_status_update_use_case(
    db: Session = Depends(get_db)
) -> SessionStatusUpdateUseCase:
    """Dependency to inject SessionStatusUpdateUseCase."""
    return SessionServiceFactory.create_session_status_update_use_case(db)


def get_session_transcript_update_use_case(
    db: Session = Depends(get_db)
) -> SessionTranscriptUpdateUseCase:
    """Dependency to inject SessionTranscriptUpdateUseCase."""
    return SessionServiceFactory.create_session_transcript_update_use_case(db)


# Plan Management Dependencies
def get_plan_retrieval_use_case(
    db: Session = Depends(get_db)
) -> PlanRetrievalUseCase:
    """Dependency to inject PlanRetrievalUseCase."""
    return PlanServiceFactory.create_plan_retrieval_use_case(db)


def get_plan_validation_use_case(
    db: Session = Depends(get_db)
) -> PlanValidationUseCase:
    """Dependency to inject PlanValidationUseCase."""
    return PlanServiceFactory.create_plan_validation_use_case(db)


# Subscription Management Dependencies
def get_subscription_creation_use_case(
    db: Session = Depends(get_db)
) -> SubscriptionCreationUseCase:
    """Dependency to inject SubscriptionCreationUseCase."""
    return SubscriptionServiceFactory.create_subscription_creation_use_case(db)


def get_subscription_retrieval_use_case(
    db: Session = Depends(get_db)
) -> SubscriptionRetrievalUseCase:
    """Dependency to inject SubscriptionRetrievalUseCase."""
    return SubscriptionServiceFactory.create_subscription_retrieval_use_case(db)


def get_subscription_modification_use_case(
    db: Session = Depends(get_db)
) -> SubscriptionModificationUseCase:
    """Dependency to inject SubscriptionModificationUseCase."""
    return SubscriptionServiceFactory.create_subscription_modification_use_case(db)