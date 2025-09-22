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
    TranscriptServiceFactory,
    ClientServiceFactory,
    CoachingSessionServiceFactory,
    BillingAnalyticsServiceFactory,
    create_session_repository,
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
from ...core.services.transcript_upload_use_case import TranscriptUploadUseCase
from ...core.services.client_management_use_case import (
    ClientRetrievalUseCase,
    ClientCreationUseCase,
    ClientUpdateUseCase,
    ClientDeletionUseCase,
    ClientOptionsUseCase,
)
from ...core.services.coaching_session_management_use_case import (
    CoachingSessionRetrievalUseCase,
    CoachingSessionCreationUseCase,
    CoachingSessionUpdateUseCase,
    CoachingSessionDeletionUseCase,
    CoachingSessionOptionsUseCase,
)
from ...core.services.dashboard_summary_use_case import DashboardSummaryUseCase
from ...core.services.billing_analytics_use_case import (
    BillingAnalyticsOverviewUseCase,
    BillingAnalyticsRevenueUseCase,
    BillingAnalyticsSegmentationUseCase,
    BillingAnalyticsUserDetailUseCase,
    BillingAnalyticsCohortUseCase,
    BillingAnalyticsChurnUseCase,
    BillingAnalyticsPlanPerformanceUseCase,
    BillingAnalyticsExportUseCase,
    BillingAnalyticsRefreshUseCase,
    BillingAnalyticsHealthScoreUseCase,
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
    session_repo = create_session_repository(db)
    return SpeakerRoleAssignmentUseCase(session_repo)


def get_segment_role_assignment_use_case(
    db: Session = Depends(get_db),
) -> SegmentRoleAssignmentUseCase:
    """Dependency to get SegmentRoleAssignmentUseCase with repository injection."""
    from ...infrastructure.factories import SpeakerRoleServiceFactory
    return SpeakerRoleServiceFactory.create_segment_role_assignment_use_case(db)


def get_speaker_role_retrieval_use_case(
    db: Session = Depends(get_db),
) -> SpeakerRoleRetrievalUseCase:
    """Dependency to get SpeakerRoleRetrievalUseCase with repository injection."""
    return SessionServiceFactory.create_speaker_role_retrieval_use_case(db)


def get_transcript_upload_use_case(
    db: Session = Depends(get_db),
) -> TranscriptUploadUseCase:
    """Dependency to get TranscriptUploadUseCase with repository injection."""
    return TranscriptServiceFactory.create_transcript_upload_use_case(db)


# Client Management Dependencies
def get_client_retrieval_use_case(
    db: Session = Depends(get_db)
) -> ClientRetrievalUseCase:
    """Dependency to inject ClientRetrievalUseCase."""
    return ClientServiceFactory.create_client_retrieval_use_case(db)


def get_client_creation_use_case(
    db: Session = Depends(get_db)
) -> ClientCreationUseCase:
    """Dependency to inject ClientCreationUseCase."""
    return ClientServiceFactory.create_client_creation_use_case(db)


def get_client_update_use_case(
    db: Session = Depends(get_db)
) -> ClientUpdateUseCase:
    """Dependency to inject ClientUpdateUseCase."""
    return ClientServiceFactory.create_client_update_use_case(db)


def get_client_deletion_use_case(
    db: Session = Depends(get_db)
) -> ClientDeletionUseCase:
    """Dependency to inject ClientDeletionUseCase."""
    return ClientServiceFactory.create_client_deletion_use_case(db)


def get_client_options_use_case() -> ClientOptionsUseCase:
    """Dependency to inject ClientOptionsUseCase."""
    return ClientServiceFactory.create_client_options_use_case()


# Coaching Session Management Dependencies
def get_coaching_session_retrieval_use_case(
    db: Session = Depends(get_db)
) -> CoachingSessionRetrievalUseCase:
    """Dependency to inject CoachingSessionRetrievalUseCase."""
    return CoachingSessionServiceFactory.create_coaching_session_retrieval_use_case(db)


def get_coaching_session_creation_use_case(
    db: Session = Depends(get_db)
) -> CoachingSessionCreationUseCase:
    """Dependency to inject CoachingSessionCreationUseCase."""
    return CoachingSessionServiceFactory.create_coaching_session_creation_use_case(db)


def get_coaching_session_update_use_case(
    db: Session = Depends(get_db)
) -> CoachingSessionUpdateUseCase:
    """Dependency to inject CoachingSessionUpdateUseCase."""
    return CoachingSessionServiceFactory.create_coaching_session_update_use_case(db)


def get_coaching_session_deletion_use_case(
    db: Session = Depends(get_db)
) -> CoachingSessionDeletionUseCase:
    """Dependency to inject CoachingSessionDeletionUseCase."""
    return CoachingSessionServiceFactory.create_coaching_session_deletion_use_case(db)


def get_coaching_session_options_use_case() -> CoachingSessionOptionsUseCase:
    """Dependency to inject CoachingSessionOptionsUseCase."""
    return CoachingSessionServiceFactory.create_coaching_session_options_use_case()


# Dashboard Summary Dependencies
def get_dashboard_summary_use_case(
    db: Session = Depends(get_db)
) -> DashboardSummaryUseCase:
    """Dependency to inject DashboardSummaryUseCase."""
    from ...infrastructure.db.repositories.coaching_session_repository import SQLAlchemyCoachingSessionRepository
    from ...infrastructure.db.repositories.session_repository import SQLAlchemySessionRepository

    coaching_session_repo = SQLAlchemyCoachingSessionRepository(db)
    session_repo = SQLAlchemySessionRepository(db)

    return DashboardSummaryUseCase(
        coaching_session_repo=coaching_session_repo,
        session_repo=session_repo,
    )


# Billing Analytics Dependencies
def get_billing_analytics_overview_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsOverviewUseCase:
    """Dependency to inject BillingAnalyticsOverviewUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_overview_use_case(db)


def get_billing_analytics_revenue_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsRevenueUseCase:
    """Dependency to inject BillingAnalyticsRevenueUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_revenue_use_case(db)


def get_billing_analytics_segmentation_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsSegmentationUseCase:
    """Dependency to inject BillingAnalyticsSegmentationUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_segmentation_use_case(db)


def get_billing_analytics_user_detail_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsUserDetailUseCase:
    """Dependency to inject BillingAnalyticsUserDetailUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_user_detail_use_case(db)


def get_billing_analytics_cohort_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsCohortUseCase:
    """Dependency to inject BillingAnalyticsCohortUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_cohort_use_case(db)


def get_billing_analytics_churn_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsChurnUseCase:
    """Dependency to inject BillingAnalyticsChurnUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_churn_use_case(db)


def get_billing_analytics_plan_performance_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsPlanPerformanceUseCase:
    """Dependency to inject BillingAnalyticsPlanPerformanceUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_plan_performance_use_case(db)


def get_billing_analytics_export_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsExportUseCase:
    """Dependency to inject BillingAnalyticsExportUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_export_use_case(db)


def get_billing_analytics_refresh_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsRefreshUseCase:
    """Dependency to inject BillingAnalyticsRefreshUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_refresh_use_case(db)


def get_billing_analytics_health_score_use_case(
    db: Session = Depends(get_db)
) -> BillingAnalyticsHealthScoreUseCase:
    """Dependency to inject BillingAnalyticsHealthScoreUseCase."""
    return BillingAnalyticsServiceFactory.create_billing_analytics_health_score_use_case(db)
