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
from ..core.repositories.ports import (
    UserRepoPort,
    UsageLogRepoPort,
    SessionRepoPort,
)
from .db.repositories.user_repository import create_user_repository
from .db.repositories.usage_log_repository import create_usage_log_repository
from .db.repositories.session_repository import create_session_repository


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