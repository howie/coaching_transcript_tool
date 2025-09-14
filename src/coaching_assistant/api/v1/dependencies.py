"""FastAPI dependencies for Clean Architecture dependency injection.

This module provides dependency injection for use cases following Clean Architecture principles.
All use cases are created through factories that inject the appropriate repository implementations.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...infrastructure.factories import UsageTrackingServiceFactory
from ...core.services.usage_tracking_use_case import CreateUsageLogUseCase, GetUserUsageUseCase


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


# TODO: Add more dependency injection functions as we migrate other endpoints:
# def get_session_management_use_case(db: Session = Depends(get_db)) -> SessionManagementUseCase:
#     """Dependency to inject SessionManagementUseCase."""
#     return SessionServiceFactory.create_session_management_use_case(db)
#
# def get_plan_validation_use_case(db: Session = Depends(get_db)) -> PlanValidationUseCase:
#     """Dependency to inject PlanValidationUseCase."""
#     return PlanServiceFactory.create_plan_validation_use_case(db)
#
# def get_subscription_management_use_case(db: Session = Depends(get_db)) -> SubscriptionManagementUseCase:
#     """Dependency to inject SubscriptionManagementUseCase."""
#     return SubscriptionServiceFactory.create_subscription_management_use_case(db)