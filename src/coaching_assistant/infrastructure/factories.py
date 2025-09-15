"""Dependency injection factories for Clean Architecture.

This module provides factory functions to create use cases with their
repository dependencies properly injected. This follows the Dependency
Injection pattern and keeps infrastructure concerns separate from
business logic.
"""

from sqlalchemy.orm import Session

from ..core.services.usage_tracking_use_case import (
    CreateUsageLogUseCase,
    GetUserUsageUseCase,
)
from ..core.services.session_management_use_case import (
    SessionCreationUseCase,
    SessionRetrievalUseCase,
    SessionStatusUpdateUseCase,
    SessionTranscriptUpdateUseCase,
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
from ..core.repositories.ports import (
    UserRepoPort,
    UsageLogRepoPort,
    SessionRepoPort,
    PlanConfigurationRepoPort,
    SubscriptionRepoPort,
    TranscriptRepoPort,
)
from .db.repositories.user_repository import create_user_repository
from .db.repositories.usage_log_repository import create_usage_log_repository
from .db.repositories.session_repository import create_session_repository
from .db.repositories.plan_configuration_repository import create_plan_configuration_repository
from .db.repositories.subscription_repository import create_subscription_repository
from .db.repositories.transcript_repository import create_transcript_repository


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


# Convenience functions for backward compatibility during migration
def get_usage_tracking_service(db_session: Session) -> CreateUsageLogUseCase:
    """Get usage tracking service (legacy compatibility function).
    
    This function provides backward compatibility during the migration
    from the old UsageTrackingService to the new use case architecture.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        CreateUsageLogUseCase instance
    """
    return UsageTrackingServiceFactory.create_usage_log_use_case(db_session)