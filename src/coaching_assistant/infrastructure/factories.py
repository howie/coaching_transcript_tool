"""Dependency injection factories for Clean Architecture.

This module provides factory functions to create use cases with their
repository dependencies properly injected. This follows the Dependency
Injection pattern and keeps infrastructure concerns separate from
business logic.
"""

from sqlalchemy.orm import Session

from ..services.billing_analytics_service import BillingAnalyticsService
from ..core.services.usage_tracking_use_case import (
    CreateUsageLogUseCase,
    GetUserUsageUseCase,
    GetUsageHistoryUseCase,
    GetUserAnalyticsUseCase,
    GetAdminAnalyticsUseCase,
    GetSpecificUserUsageUseCase,
    GetMonthlyUsageReportUseCase,
)
from ..core.services.session_management_use_case import (
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
from ..core.services.plan_management_use_case import (
    PlanRetrievalUseCase,
    PlanValidationUseCase,
)
from ..core.services.subscription_management_use_case import (
    SubscriptionCreationUseCase,
    SubscriptionRetrievalUseCase,
    SubscriptionModificationUseCase,
)
from ..core.services.speaker_role_management_use_case import (
    SpeakerRoleAssignmentUseCase,
    SegmentRoleAssignmentUseCase,
    SpeakerRoleRetrievalUseCase,
)
from ..core.services.client_management_use_case import (
    ClientRetrievalUseCase,
    ClientCreationUseCase,
    ClientUpdateUseCase,
    ClientDeletionUseCase,
    ClientOptionsUseCase,
)
from ..core.services.coaching_session_management_use_case import (
    CoachingSessionRetrievalUseCase,
    CoachingSessionCreationUseCase,
    CoachingSessionUpdateUseCase,
    CoachingSessionDeletionUseCase,
    CoachingSessionOptionsUseCase,
)
from ..core.services.coach_profile_management_use_case import (
    CoachProfileManagementUseCase,
)
from ..core.services.transcript_upload_use_case import TranscriptUploadUseCase
from ..core.services.billing_analytics_use_case import (
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
from ..core.repositories.ports import (
    UserRepoPort,
    UsageLogRepoPort,
    SessionRepoPort,
    PlanConfigurationRepoPort,
    SubscriptionRepoPort,
    TranscriptRepoPort,
    SpeakerRoleRepoPort,
    SegmentRoleRepoPort,
    ClientRepoPort,
    CoachingSessionRepoPort,
    CoachProfileRepoPort,
)
from .db.repositories.user_repository import create_user_repository
from .db.repositories.usage_log_repository import create_usage_log_repository
from .db.repositories.usage_analytics_repository import create_usage_analytics_repository
from .db.repositories.session_repository import create_session_repository
from .db.repositories.plan_configuration_repository import create_plan_configuration_repository
from .db.repositories.subscription_repository import create_subscription_repository
from .db.repositories.transcript_repository import create_transcript_repository
from .db.repositories.speaker_role_repository import (
    create_speaker_role_repository,
    create_segment_role_repository,
)
from .db.repositories.client_repository import create_client_repository
from .db.repositories.coaching_session_repository import create_coaching_session_repository
from .db.repositories.coach_profile_repository import create_coach_profile_repository


class UsageTrackingServiceFactory:
    """Factory for usage tracking use cases."""

    @staticmethod
    def create_usage_log_use_case(db_session: Session) -> CreateUsageLogUseCase:
        """Create a CreateUsageLogUseCase with all dependencies injected.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Fully configured CreateUsageLogUseCase
        """
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)
        session_repo = create_session_repository(db_session)
        
        return CreateUsageLogUseCase(
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
            session_repo=session_repo,
        )

    @staticmethod
    def create_user_usage_use_case(db_session: Session) -> GetUserUsageUseCase:
        """Create a GetUserUsageUseCase with all dependencies injected.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            Fully configured GetUserUsageUseCase
        """
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)
        
        return GetUserUsageUseCase(
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
        )

    @staticmethod
    def create_usage_history_use_case(db_session: Session) -> GetUsageHistoryUseCase:
        """Create a GetUsageHistoryUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured GetUsageHistoryUseCase
        """
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)

        return GetUsageHistoryUseCase(
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
        )

    @staticmethod
    def create_user_analytics_use_case(db_session: Session) -> GetUserAnalyticsUseCase:
        """Create a GetUserAnalyticsUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured GetUserAnalyticsUseCase
        """
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)
        usage_analytics_repo = create_usage_analytics_repository(db_session)

        return GetUserAnalyticsUseCase(
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
            usage_analytics_repo=usage_analytics_repo,
        )

    @staticmethod
    def create_admin_analytics_use_case(db_session: Session) -> GetAdminAnalyticsUseCase:
        """Create a GetAdminAnalyticsUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured GetAdminAnalyticsUseCase
        """
        usage_analytics_repo = create_usage_analytics_repository(db_session)

        return GetAdminAnalyticsUseCase(
            usage_analytics_repo=usage_analytics_repo,
        )

    @staticmethod
    def create_specific_user_usage_use_case(db_session: Session) -> GetSpecificUserUsageUseCase:
        """Create a GetSpecificUserUsageUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured GetSpecificUserUsageUseCase
        """
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)

        return GetSpecificUserUsageUseCase(
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
        )

    @staticmethod
    def create_monthly_usage_report_use_case(db_session: Session) -> GetMonthlyUsageReportUseCase:
        """Create a GetMonthlyUsageReportUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured GetMonthlyUsageReportUseCase
        """
        usage_analytics_repo = create_usage_analytics_repository(db_session)

        return GetMonthlyUsageReportUseCase(
            usage_analytics_repo=usage_analytics_repo,
        )


class RepositoryFactory:
    """Factory for creating repository instances."""
    
    @staticmethod
    def create_user_repository(db_session: Session) -> UserRepoPort:
        """Create a user repository instance.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            UserRepoPort implementation
        """
        return create_user_repository(db_session)
    
    @staticmethod
    def create_usage_log_repository(db_session: Session) -> UsageLogRepoPort:
        """Create a usage log repository instance.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            UsageLogRepoPort implementation
        """
        return create_usage_log_repository(db_session)
    
    @staticmethod
    def create_session_repository(db_session: Session) -> SessionRepoPort:
        """Create a session repository instance.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            SessionRepoPort implementation
        """
        return create_session_repository(db_session)

    @staticmethod
    def create_plan_configuration_repository(db_session: Session) -> PlanConfigurationRepoPort:
        """Create a plan configuration repository instance.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            PlanConfigurationRepoPort implementation
        """
        return create_plan_configuration_repository(db_session)

    @staticmethod
    def create_subscription_repository(db_session: Session) -> SubscriptionRepoPort:
        """Create a subscription repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            SubscriptionRepoPort implementation
        """
        return create_subscription_repository(db_session)

    @staticmethod
    def create_transcript_repository(db_session: Session) -> TranscriptRepoPort:
        """Create a transcript repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            TranscriptRepoPort implementation
        """
        return create_transcript_repository(db_session)

    @staticmethod
    def create_client_repository(db_session: Session) -> ClientRepoPort:
        """Create a client repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            ClientRepoPort implementation
        """
        return create_client_repository(db_session)

    @staticmethod
    def create_coaching_session_repository(db_session: Session) -> CoachingSessionRepoPort:
        """Create a coaching session repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            CoachingSessionRepoPort implementation
        """
        return create_coaching_session_repository(db_session)

    @staticmethod
    def create_coach_profile_repository(db_session: Session) -> CoachProfileRepoPort:
        """Create a coach profile repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            CoachProfileRepoPort implementation
        """
        return create_coach_profile_repository(db_session)

    @staticmethod
    def create_usage_analytics_repository(db_session: Session) -> 'UsageAnalyticsRepoPort':
        """Create a usage analytics repository instance.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            UsageAnalyticsRepoPort implementation
        """
        return create_usage_analytics_repository(db_session)


class SessionServiceFactory:
    """Factory for session management use cases."""

    @staticmethod
    def create_session_creation_use_case(db_session: Session) -> SessionCreationUseCase:
        """Create a SessionCreationUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        plan_config_repo = create_plan_configuration_repository(db_session)
        
        return SessionCreationUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            plan_config_repo=plan_config_repo,
        )

    @staticmethod
    def create_session_retrieval_use_case(db_session: Session) -> SessionRetrievalUseCase:
        """Create a SessionRetrievalUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)
        
        return SessionRetrievalUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            transcript_repo=transcript_repo,
        )

    @staticmethod
    def create_session_status_update_use_case(db_session: Session) -> SessionStatusUpdateUseCase:
        """Create a SessionStatusUpdateUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)
        
        return SessionStatusUpdateUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            usage_log_repo=usage_log_repo,
        )

    @staticmethod
    def create_session_transcript_update_use_case(db_session: Session) -> SessionTranscriptUpdateUseCase:
        """Create a SessionTranscriptUpdateUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)

        return SessionTranscriptUpdateUseCase(
            session_repo=session_repo,
            transcript_repo=transcript_repo,
        )

    @staticmethod
    def create_session_upload_management_use_case(db_session: Session) -> SessionUploadManagementUseCase:
        """Create a SessionUploadManagementUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        plan_config_repo = create_plan_configuration_repository(db_session)

        return SessionUploadManagementUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            plan_config_repo=plan_config_repo,
        )

    @staticmethod
    def create_session_transcription_management_use_case(db_session: Session) -> SessionTranscriptionManagementUseCase:
        """Create a SessionTranscriptionManagementUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)

        return SessionTranscriptionManagementUseCase(
            session_repo=session_repo,
            transcript_repo=transcript_repo,
        )

    @staticmethod
    def create_session_export_use_case(db_session: Session) -> SessionExportUseCase:
        """Create a SessionExportUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)

        return SessionExportUseCase(
            session_repo=session_repo,
            transcript_repo=transcript_repo,
        )

    @staticmethod
    def create_session_status_retrieval_use_case(db_session: Session) -> SessionStatusRetrievalUseCase:
        """Create a SessionStatusRetrievalUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)

        return SessionStatusRetrievalUseCase(
            session_repo=session_repo,
        )

    @staticmethod
    def create_session_transcript_upload_use_case(db_session: Session) -> SessionTranscriptUploadUseCase:
        """Create a SessionTranscriptUploadUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)

        return SessionTranscriptUploadUseCase(
            session_repo=session_repo,
            transcript_repo=transcript_repo,
        )

    @staticmethod
    def create_speaker_role_retrieval_use_case(db_session: Session) -> SpeakerRoleRetrievalUseCase:
        """Create a SpeakerRoleRetrievalUseCase with all dependencies injected."""
        session_repo = create_session_repository(db_session)
        speaker_role_repo = create_speaker_role_repository(db_session)
        segment_role_repo = create_segment_role_repository(db_session)

        return SpeakerRoleRetrievalUseCase(
            session_repo=session_repo,
            speaker_role_repo=speaker_role_repo,
            segment_role_repo=segment_role_repo,
        )

    @staticmethod
    def create_speaker_role_repository(db_session: Session) -> SpeakerRoleRepoPort:
        """Create a speaker role repository instance."""
        return create_speaker_role_repository(db_session)

    @staticmethod
    def create_segment_role_repository(db_session: Session) -> SegmentRoleRepoPort:
        """Create a segment role repository instance."""
        return create_segment_role_repository(db_session)


class SpeakerRoleServiceFactory:
    """Factory for speaker role management use cases."""

    @staticmethod
    def create_speaker_role_assignment_use_case(db_session: Session) -> SpeakerRoleAssignmentUseCase:
        """Create a SpeakerRoleAssignmentUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured SpeakerRoleAssignmentUseCase
        """
        session_repo = create_session_repository(db_session)
        speaker_role_repo = create_speaker_role_repository(db_session)

        return SpeakerRoleAssignmentUseCase(
            session_repo=session_repo,
            speaker_role_repo=speaker_role_repo,
        )

    @staticmethod
    def create_segment_role_assignment_use_case(db_session: Session) -> SegmentRoleAssignmentUseCase:
        """Create a SegmentRoleAssignmentUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured SegmentRoleAssignmentUseCase
        """
        session_repo = create_session_repository(db_session)
        segment_role_repo = create_segment_role_repository(db_session)

        return SegmentRoleAssignmentUseCase(
            session_repo=session_repo,
            segment_role_repo=segment_role_repo,
        )

    @staticmethod
    def create_speaker_role_retrieval_use_case(db_session: Session) -> SpeakerRoleRetrievalUseCase:
        """Create a SpeakerRoleRetrievalUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured SpeakerRoleRetrievalUseCase
        """
        session_repo = create_session_repository(db_session)
        speaker_role_repo = create_speaker_role_repository(db_session)
        segment_role_repo = create_segment_role_repository(db_session)

        return SpeakerRoleRetrievalUseCase(
            session_repo=session_repo,
            speaker_role_repo=speaker_role_repo,
            segment_role_repo=segment_role_repo,
        )


class PlanServiceFactory:
    """Factory for plan management use cases."""

    @staticmethod
    def create_plan_retrieval_use_case(db_session: Session) -> PlanRetrievalUseCase:
        """Create a PlanRetrievalUseCase with all dependencies injected."""
        plan_config_repo = create_plan_configuration_repository(db_session)
        user_repo = create_user_repository(db_session)
        subscription_repo = create_subscription_repository(db_session)
        
        return PlanRetrievalUseCase(
            plan_config_repo=plan_config_repo,
            user_repo=user_repo,
            subscription_repo=subscription_repo,
        )

    @staticmethod
    def create_plan_validation_use_case(db_session: Session) -> PlanValidationUseCase:
        """Create a PlanValidationUseCase with all dependencies injected."""
        plan_config_repo = create_plan_configuration_repository(db_session)
        user_repo = create_user_repository(db_session)
        session_repo = create_session_repository(db_session)
        usage_log_repo = create_usage_log_repository(db_session)
        
        return PlanValidationUseCase(
            plan_config_repo=plan_config_repo,
            user_repo=user_repo,
            session_repo=session_repo,
            usage_log_repo=usage_log_repo,
        )


class SubscriptionServiceFactory:
    """Factory for subscription management use cases."""

    @staticmethod
    def create_subscription_creation_use_case(db_session: Session) -> SubscriptionCreationUseCase:
        """Create a SubscriptionCreationUseCase with all dependencies injected."""
        subscription_repo = create_subscription_repository(db_session)
        user_repo = create_user_repository(db_session)
        plan_config_repo = create_plan_configuration_repository(db_session)
        
        return SubscriptionCreationUseCase(
            subscription_repo=subscription_repo,
            user_repo=user_repo,
            plan_config_repo=plan_config_repo,
        )

    @staticmethod
    def create_subscription_retrieval_use_case(db_session: Session) -> SubscriptionRetrievalUseCase:
        """Create a SubscriptionRetrievalUseCase with all dependencies injected."""
        subscription_repo = create_subscription_repository(db_session)
        user_repo = create_user_repository(db_session)
        
        return SubscriptionRetrievalUseCase(
            subscription_repo=subscription_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_subscription_modification_use_case(db_session: Session) -> SubscriptionModificationUseCase:
        """Create a SubscriptionModificationUseCase with all dependencies injected."""
        subscription_repo = create_subscription_repository(db_session)
        user_repo = create_user_repository(db_session)
        plan_config_repo = create_plan_configuration_repository(db_session)
        
        return SubscriptionModificationUseCase(
            subscription_repo=subscription_repo,
            user_repo=user_repo,
            plan_config_repo=plan_config_repo,
        )


class ClientServiceFactory:
    """Factory for client management use cases."""

    @staticmethod
    def create_client_retrieval_use_case(db_session: Session) -> ClientRetrievalUseCase:
        """Create a ClientRetrievalUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured ClientRetrievalUseCase
        """
        client_repo = create_client_repository(db_session)
        user_repo = create_user_repository(db_session)

        return ClientRetrievalUseCase(
            client_repo=client_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_client_creation_use_case(db_session: Session) -> ClientCreationUseCase:
        """Create a ClientCreationUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured ClientCreationUseCase
        """
        client_repo = create_client_repository(db_session)
        user_repo = create_user_repository(db_session)

        return ClientCreationUseCase(
            client_repo=client_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_client_update_use_case(db_session: Session) -> ClientUpdateUseCase:
        """Create a ClientUpdateUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured ClientUpdateUseCase
        """
        client_repo = create_client_repository(db_session)
        user_repo = create_user_repository(db_session)

        return ClientUpdateUseCase(
            client_repo=client_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_client_deletion_use_case(db_session: Session) -> ClientDeletionUseCase:
        """Create a ClientDeletionUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured ClientDeletionUseCase
        """
        client_repo = create_client_repository(db_session)
        user_repo = create_user_repository(db_session)

        return ClientDeletionUseCase(
            client_repo=client_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_client_options_use_case() -> ClientOptionsUseCase:
        """Create a ClientOptionsUseCase (no dependencies needed).

        Returns:
            ClientOptionsUseCase instance
        """
        return ClientOptionsUseCase()


class CoachingSessionServiceFactory:
    """Factory for coaching session management use cases."""

    @staticmethod
    def create_coaching_session_retrieval_use_case(db_session: Session) -> CoachingSessionRetrievalUseCase:
        """Create a CoachingSessionRetrievalUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured CoachingSessionRetrievalUseCase
        """
        session_repo = create_coaching_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        client_repo = create_client_repository(db_session)
        transcription_session_repo = create_session_repository(db_session)

        return CoachingSessionRetrievalUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            client_repo=client_repo,
            transcription_session_repo=transcription_session_repo,
        )

    @staticmethod
    def create_coaching_session_creation_use_case(db_session: Session) -> CoachingSessionCreationUseCase:
        """Create a CoachingSessionCreationUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured CoachingSessionCreationUseCase
        """
        session_repo = create_coaching_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        client_repo = create_client_repository(db_session)

        return CoachingSessionCreationUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            client_repo=client_repo,
        )

    @staticmethod
    def create_coaching_session_update_use_case(db_session: Session) -> CoachingSessionUpdateUseCase:
        """Create a CoachingSessionUpdateUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured CoachingSessionUpdateUseCase
        """
        session_repo = create_coaching_session_repository(db_session)
        user_repo = create_user_repository(db_session)
        client_repo = create_client_repository(db_session)

        return CoachingSessionUpdateUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
            client_repo=client_repo,
        )

    @staticmethod
    def create_coaching_session_deletion_use_case(db_session: Session) -> CoachingSessionDeletionUseCase:
        """Create a CoachingSessionDeletionUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured CoachingSessionDeletionUseCase
        """
        session_repo = create_coaching_session_repository(db_session)
        user_repo = create_user_repository(db_session)

        return CoachingSessionDeletionUseCase(
            session_repo=session_repo,
            user_repo=user_repo,
        )

    @staticmethod
    def create_coaching_session_options_use_case() -> CoachingSessionOptionsUseCase:
        """Create a CoachingSessionOptionsUseCase (no dependencies needed).

        Returns:
            CoachingSessionOptionsUseCase instance
        """
        return CoachingSessionOptionsUseCase()


class TranscriptServiceFactory:
    """Factory for transcript-related use cases."""

    @staticmethod
    def create_transcript_upload_use_case(db_session: Session) -> TranscriptUploadUseCase:
        """Create a TranscriptUploadUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured TranscriptUploadUseCase
        """
        coaching_session_repo = create_coaching_session_repository(db_session)
        session_repo = create_session_repository(db_session)
        transcript_repo = create_transcript_repository(db_session)
        speaker_role_repo = create_speaker_role_repository(db_session)

        return TranscriptUploadUseCase(
            coaching_session_repo=coaching_session_repo,
            session_repo=session_repo,
            transcript_repo=transcript_repo,
            speaker_role_repo=speaker_role_repo,
        )


# Legacy compatibility functions have been removed as part of WP6-Cleanup-3
# All API endpoints now use factory pattern directly


# ECPay and Notification Service Factories for WP6-Cleanup-2

def create_ecpay_service(db_session: Session = None) -> "ECPaySubscriptionService":
    """Create ECPay service with proper dependency injection.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        ECPaySubscriptionService instance with HTTP client and notification service
    """
    from ..core.services.ecpay_service import ECPaySubscriptionService
    from ..core.config import Settings
    from .http.ecpay_client import ECPayAPIClient
    from .http.notification_service import EmailNotificationService

    if db_session is None:
        from .db.session import get_db_session
        db_session = next(get_db_session())

    settings = Settings()
    # Create ECPay HTTP client
    ecpay_client = ECPayAPIClient(
        merchant_id=settings.ECPAY_MERCHANT_ID,
        hash_key=settings.ECPAY_HASH_KEY,
        hash_iv=settings.ECPAY_HASH_IV,
        environment=settings.ECPAY_ENVIRONMENT
    )

    # Create notification service
    notification_service = EmailNotificationService()

    return ECPaySubscriptionService(
        db=db_session,
        settings=settings,
        ecpay_client=ecpay_client,
        notification_service=notification_service
    )


def create_notification_service() -> "NotificationService":
    """Create notification service for email sending.

    Returns:
        NotificationService instance
    """
    from .http.notification_service import EmailNotificationService

    # In production, this would use actual SMTP settings
    # For now, using the mock implementation
    return EmailNotificationService()


def create_ecpay_client() -> "ECPayAPIClient":
    """Create ECPay HTTP client.

    Returns:
        ECPayAPIClient instance
    """
    from .http.ecpay_client import ECPayAPIClient
    from ..core.config import Settings

    settings = Settings()

    return ECPayAPIClient(
        merchant_id=settings.ECPAY_MERCHANT_ID,
        hash_key=settings.ECPAY_HASH_KEY,
        hash_iv=settings.ECPAY_HASH_IV,
        environment=settings.ECPAY_ENVIRONMENT
    )


class BillingAnalyticsServiceFactory:
    """Factory for billing analytics use cases."""

    @staticmethod
    def create_billing_analytics_overview_use_case(db_session: Session) -> BillingAnalyticsOverviewUseCase:
        """Create a BillingAnalyticsOverviewUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsOverviewUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsOverviewUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_revenue_use_case(db_session: Session) -> BillingAnalyticsRevenueUseCase:
        """Create a BillingAnalyticsRevenueUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsRevenueUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsRevenueUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_segmentation_use_case(db_session: Session) -> BillingAnalyticsSegmentationUseCase:
        """Create a BillingAnalyticsSegmentationUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsSegmentationUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsSegmentationUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_user_detail_use_case(db_session: Session) -> BillingAnalyticsUserDetailUseCase:
        """Create a BillingAnalyticsUserDetailUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsUserDetailUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsUserDetailUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_cohort_use_case(db_session: Session) -> BillingAnalyticsCohortUseCase:
        """Create a BillingAnalyticsCohortUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsCohortUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsCohortUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_churn_use_case(db_session: Session) -> BillingAnalyticsChurnUseCase:
        """Create a BillingAnalyticsChurnUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsChurnUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsChurnUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_plan_performance_use_case(db_session: Session) -> BillingAnalyticsPlanPerformanceUseCase:
        """Create a BillingAnalyticsPlanPerformanceUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsPlanPerformanceUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsPlanPerformanceUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_export_use_case(db_session: Session) -> BillingAnalyticsExportUseCase:
        """Create a BillingAnalyticsExportUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsExportUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsExportUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_refresh_use_case(db_session: Session) -> BillingAnalyticsRefreshUseCase:
        """Create a BillingAnalyticsRefreshUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsRefreshUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsRefreshUseCase(billing_service)

    @staticmethod
    def create_billing_analytics_health_score_use_case(db_session: Session) -> BillingAnalyticsHealthScoreUseCase:
        """Create a BillingAnalyticsHealthScoreUseCase.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured BillingAnalyticsHealthScoreUseCase
        """
        billing_service = BillingAnalyticsService(db_session)
        return BillingAnalyticsHealthScoreUseCase(billing_service)


class CoachProfileServiceFactory:
    """Factory for coach profile management use cases."""

    @staticmethod
    def create_coach_profile_management_use_case(db_session: Session) -> CoachProfileManagementUseCase:
        """Create a CoachProfileManagementUseCase with all dependencies injected.

        Args:
            db_session: SQLAlchemy database session

        Returns:
            Fully configured CoachProfileManagementUseCase
        """
        coach_profile_repo = create_coach_profile_repository(db_session)
        user_repo = create_user_repository(db_session)

        return CoachProfileManagementUseCase(
            coach_profile_repo=coach_profile_repo,
            user_repo=user_repo,
        )