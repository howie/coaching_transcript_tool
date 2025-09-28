"""SQLAlchemy implementation of SessionRepoPort with domain model conversion.

This module provides the concrete implementation of session repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DBSession

from ....core.config import settings
from ....core.models.session import Session, SessionStatus
from ....core.repositories.ports import SessionRepoPort

# TEMPORARY FIX: Use legacy model until database migration is complete
# from ..models.session_model import SessionModel
from ....models.session import Session as SessionModel


class SQLAlchemySessionRepository(SessionRepoPort):
    """SQLAlchemy implementation of the SessionRepoPort interface with domain conversion."""

    def __init__(self, session: DBSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID.

        Args:
            session_id: UUID of the session to retrieve

        Returns:
            Session domain entity or None if not found
        """
        try:
            orm_session = self.session.get(SessionModel, session_id)
            return self._legacy_to_domain(orm_session) if orm_session else None
        except SQLAlchemyError as e:
            # Log error in production
            raise RuntimeError(f"Database error retrieving session {session_id}") from e

    def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Session]:
        """Get sessions by user ID with optional filtering.

        Args:
            user_id: UUID of the user
            status: Optional session status filter
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of Session domain entities
        """
        try:
            query = self.session.query(SessionModel).filter(
                SessionModel.user_id == user_id
            )

            if status is not None:
                query = query.filter(SessionModel.status == status)

            orm_sessions = (
                query.order_by(desc(SessionModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._legacy_to_domain(orm_session) for orm_session in orm_sessions]
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving sessions for user {user_id}"
            ) from e

    def save(self, session: Session) -> Session:
        """Save or update session entity.

        Args:
            session: Session domain entity to save

        Returns:
            Saved Session domain entity with updated fields
        """
        try:
            if session.id:
                # Update existing session
                orm_session = self.session.get(SessionModel, session.id)
                if orm_session:
                    orm_session.update_from_domain(session)
                else:
                    # Session ID exists but not found in DB - create new
                    orm_session = SessionModel.from_domain(session)
                    self.session.add(orm_session)
            else:
                # Create new session
                orm_session = SessionModel.from_domain(session)
                self.session.add(orm_session)

            self.session.commit()  # Commit the transaction to make it visible to other requests
            return self._legacy_to_domain(orm_session)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving session {session.title}") from e

    def update_status(self, session_id: UUID, status: SessionStatus) -> Session:
        """Update session status.

        Args:
            session_id: UUID of session to update
            status: New status to set

        Returns:
            Updated Session domain entity

        Raises:
            ValueError: If session not found
            RuntimeError: If database error occurs
        """
        try:
            orm_session = self.session.get(SessionModel, session_id)
            if orm_session is None:
                raise ValueError(f"Session {session_id} not found")

            # Use domain model for business rule validation if needed
            domain_session = self._legacy_to_domain(orm_session)
            domain_session.status = status
            domain_session.updated_at = datetime.utcnow()

            # Update ORM model with validated domain data
            orm_session.update_from_domain(domain_session)
            self.session.commit()
            return self._legacy_to_domain(orm_session)
        except ValueError:
            # Re-raise business rule violations
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(
                f"Database error updating session status for {session_id}"
            ) from e

    def get_sessions_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Session]:
        """Get sessions within date range for user.

        Args:
            user_id: UUID of the user
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of Session domain entities within the date range
        """
        try:
            orm_sessions = (
                self.session.query(SessionModel)
                .filter(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.created_at >= start_date,
                        SessionModel.created_at <= end_date,
                    )
                )
                .order_by(SessionModel.created_at)
                .all()
            )
            return [self._legacy_to_domain(orm_session) for orm_session in orm_sessions]
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving sessions by date range for user {user_id}"
            ) from e

    def count_user_sessions(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Count user sessions, optionally since a date.

        Args:
            user_id: UUID of the user
            since: Optional date to count from

        Returns:
            Count of user sessions
        """
        try:
            query = self.session.query(SessionModel).filter(
                SessionModel.user_id == user_id
            )

            if since is not None:
                query = query.filter(SessionModel.created_at >= since)

            return query.count()
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error counting sessions for user {user_id}"
            ) from e

    def get_total_duration_minutes(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Get total duration in minutes for user sessions.

        Args:
            user_id: UUID of the user
            since: Optional date to count from

        Returns:
            Total duration in minutes
        """
        try:
            query = self.session.query(func.sum(SessionModel.duration_seconds)).filter(
                and_(
                    SessionModel.user_id == user_id,
                    SessionModel.duration_seconds.isnot(None),
                )
            )

            if since is not None:
                query = query.filter(SessionModel.created_at >= since)

            total_seconds = query.scalar() or 0
            return int(total_seconds / 60)  # Convert to minutes
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error calculating total duration for user {user_id}"
            ) from e

    def _legacy_to_domain(self, orm_session: SessionModel) -> Session:
        """Convert legacy ORM model to domain model.

        TEMPORARY: This method handles conversion from legacy Session ORM model
        to domain Session model until database migration is complete.
        """

        domain_session = Session(
            id=UUID(str(orm_session.id)) if orm_session.id else None,
            user_id=(UUID(str(orm_session.user_id)) if orm_session.user_id else None),
            title=orm_session.title or "",
            language=orm_session.language or "auto",
            audio_filename=orm_session.audio_filename,
            duration_seconds=orm_session.duration_seconds,
            status=(
                SessionStatus(orm_session.status.value)
                if orm_session.status
                else SessionStatus.UPLOADING
            ),
            error_message=orm_session.error_message,
            progress_percentage=0,  # Not in legacy model, default to 0
            gcs_audio_path=orm_session.gcs_audio_path,
            gcs_transcript_path=None,  # Not in legacy model
            stt_provider=(
                (orm_session.stt_provider or "").strip().lower()
                or settings.STT_PROVIDER
            ),
            transcription_job_id=orm_session.transcription_job_id,
            assemblyai_transcript_id=None,  # Not in legacy model
            transcript_text=None,  # Legacy model stores in segments
            speaker_count=None,  # Not in legacy model
            confidence_score=None,  # Not in legacy model
            segments_count=int(getattr(orm_session, "segments_count", 0) or 0),
            created_at=orm_session.created_at,
            updated_at=orm_session.updated_at,
            transcription_started_at=None,  # Not in legacy model
            transcription_completed_at=None,  # Not in legacy model
        )

        # TEMPORARY: Add legacy fields for backward compatibility
        domain_session.stt_cost_usd = orm_session.stt_cost_usd
        domain_session.provider_metadata = getattr(orm_session, "provider_metadata", {})

        return domain_session

    def get_completed_count_for_user(self, user_id: UUID) -> int:
        """Get count of completed sessions for a user."""
        try:
            from ....models.session import SessionStatus as LegacySessionStatus

            result = (
                self.session.query(SessionModel)
                .filter(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.status == LegacySessionStatus.COMPLETED,
                    )
                )
                .count()
            )
            return int(result or 0)
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error getting completed sessions count for user {user_id}"
            ) from e


def create_session_repository(session: DBSession) -> SessionRepoPort:
    """Factory function to create a session repository.

    Args:
        session: SQLAlchemy session

    Returns:
        SessionRepoPort implementation
    """
    return SQLAlchemySessionRepository(session)
