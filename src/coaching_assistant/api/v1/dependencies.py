"""FastAPI dependencies for Clean Architecture dependency injection.

This module provides dependency injection for use cases following Clean Architecture principles.
All use cases are created through factories that inject the appropriate repository implementations.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from .auth import get_current_user_dependency
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
    SessionUploadManagementUseCase,
    SessionTranscriptionManagementUseCase,
    SessionExportUseCase,
    SessionStatusRetrievalUseCase,
    SessionTranscriptUploadUseCase,
)
from ...core.services.speaker_role_management_use_case import (
    SpeakerRoleAssignmentUseCase,
    SegmentRoleAssignmentUseCase,
    SpeakerRoleRetrievalUseCase,
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


def get_session_upload_management_use_case(
    db: Session = Depends(get_db)
) -> SessionUploadManagementUseCase:
    """Dependency to inject SessionUploadManagementUseCase."""
    return SessionServiceFactory.create_session_upload_management_use_case(db)


def get_session_transcription_management_use_case(
    db: Session = Depends(get_db)
) -> SessionTranscriptionManagementUseCase:
    """Dependency to inject SessionTranscriptionManagementUseCase."""
    return SessionServiceFactory.create_session_transcription_management_use_case(db)


def get_session_export_use_case(
    db: Session = Depends(get_db)
) -> SessionExportUseCase:
    """Dependency to inject SessionExportUseCase."""
    return SessionServiceFactory.create_session_export_use_case(db)


def get_session_status_retrieval_use_case(
    db: Session = Depends(get_db)
) -> SessionStatusRetrievalUseCase:
    """Dependency to inject SessionStatusRetrievalUseCase."""
    return SessionServiceFactory.create_session_status_retrieval_use_case(db)


def get_session_transcript_upload_use_case(
    db: Session = Depends(get_db)
) -> SessionTranscriptUploadUseCase:
    """Dependency to inject SessionTranscriptUploadUseCase."""
    return SessionServiceFactory.create_session_transcript_upload_use_case(db)


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


# Admin Permission Dependencies
async def require_super_admin(
    current_user = Depends(get_current_user_dependency),
) -> None:
    """Dependency to ensure the current user has super admin permissions."""
    from ...core.models.user import UserRole
    if not current_user or current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required"
        )


async def require_admin(
    current_user = Depends(get_current_user_dependency),
) -> None:
    """Dependency to ensure the current user has admin permissions."""
    from ...core.models.user import UserRole
    if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )


async def require_staff(
    current_user = Depends(get_current_user_dependency),
) -> None:
    """Dependency to ensure the current user has staff permissions or higher."""
    from ...core.models.user import UserRole
    if not current_user or current_user.role not in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Staff access required"
        )


async def get_current_user_with_permissions(
    current_user = Depends(get_current_user_dependency),
):
    """Dependency to get current user with permission context."""
    return current_user


# Speaker Role Management Use Case Dependencies
def get_speaker_role_assignment_use_case(
    db: Session = Depends(get_db),
) -> SpeakerRoleAssignmentUseCase:
    """Dependency to get SpeakerRoleAssignmentUseCase with repository injection."""
    session_repo = SessionServiceFactory.create_session_repository(db)
    return SpeakerRoleAssignmentUseCase(session_repo)


def get_segment_role_assignment_use_case(
    db: Session = Depends(get_db),
) -> SegmentRoleAssignmentUseCase:
    """Dependency to get SegmentRoleAssignmentUseCase with repository injection."""
    session_repo = SessionServiceFactory.create_session_repository(db)
    return SegmentRoleAssignmentUseCase(session_repo)


def get_speaker_role_retrieval_use_case(
    db: Session = Depends(get_db),
) -> SpeakerRoleRetrievalUseCase:
    """Dependency to get SpeakerRoleRetrievalUseCase with repository injection."""
    return SessionServiceFactory.create_speaker_role_retrieval_use_case(db)