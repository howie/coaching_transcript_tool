"""SQLAlchemy implementation of SessionRepoPort.

This module provides the concrete implementation of session repository
operations using SQLAlchemy ORM.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, and_

from ....core.repositories.ports import SessionRepoPort
from ....models.session import Session as SessionModel, SessionStatus


class SQLAlchemySessionRepository(SessionRepoPort):
    """SQLAlchemy implementation of the SessionRepoPort interface."""

    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_id(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session by ID.
        
        Args:
            session_id: UUID of the session to retrieve
            
        Returns:
            Session entity or None if not found
        """
        try:
            return self.session.get(SessionModel, session_id)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving session {session_id}") from e

    def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionModel]:
        """Get sessions by user ID with optional filtering.
        
        Args:
            user_id: UUID of the user
            status: Optional session status filter
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session entities
        """
        try:
            query = (
                self.session.query(SessionModel)
                .filter(SessionModel.user_id == user_id)
            )
            
            if status is not None:
                query = query.filter(SessionModel.status == status)
            
            return (
                query
                .order_by(desc(SessionModel.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving sessions for user {user_id}") from e

    def save(self, session_model: SessionModel) -> SessionModel:
        """Save or update session entity.
        
        Args:
            session_model: Session entity to save
            
        Returns:
            Saved session entity
        """
        try:
            if session_model.id is None or not self._is_attached(session_model):
                self.session.add(session_model)
            
            self.session.commit()
            self.session.refresh(session_model)
            return session_model
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving session") from e

    def update_status(self, session_id: UUID, status: SessionStatus) -> SessionModel:
        """Update session status.
        
        Args:
            session_id: UUID of session to update
            status: New status to set
            
        Returns:
            Updated session entity
            
        Raises:
            ValueError: If session not found
            RuntimeError: If database error occurs
        """
        try:
            session_model = self.session.get(SessionModel, session_id)
            if session_model is None:
                raise ValueError(f"Session {session_id} not found")
            
            session_model.status = status
            session_model.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.session.refresh(session_model)
            return session_model
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error updating session status for {session_id}") from e

    def get_sessions_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SessionModel]:
        """Get sessions within date range for user.
        
        Args:
            user_id: UUID of the user
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of session entities within the date range
        """
        try:
            return (
                self.session.query(SessionModel)
                .filter(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.created_at >= start_date,
                        SessionModel.created_at <= end_date
                    )
                )
                .order_by(SessionModel.created_at)
                .all()
            )
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving sessions by date range for user {user_id}") from e

    def count_user_sessions(self, user_id: UUID, since: Optional[datetime] = None) -> int:
        """Count user sessions, optionally since a date.
        
        Args:
            user_id: UUID of the user
            since: Optional date to count from
            
        Returns:
            Count of user sessions
        """
        try:
            query = (
                self.session.query(SessionModel)
                .filter(SessionModel.user_id == user_id)
            )
            
            if since is not None:
                query = query.filter(SessionModel.created_at >= since)
            
            return query.count()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error counting sessions for user {user_id}") from e

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
            query = (
                self.session.query(func.sum(SessionModel.duration_seconds))
                .filter(
                    and_(
                        SessionModel.user_id == user_id,
                        SessionModel.duration_seconds.isnot(None)
                    )
                )
            )
            
            if since is not None:
                query = query.filter(SessionModel.created_at >= since)
            
            total_seconds = query.scalar() or 0
            return int(total_seconds / 60)  # Convert to minutes
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error calculating total duration for user {user_id}") from e

    def _is_attached(self, session_model: SessionModel) -> bool:
        """Check if session entity is attached to current session.
        
        Args:
            session_model: Session entity to check
            
        Returns:
            True if attached to session
        """
        return session_model in self.session


def create_session_repository(session: Session) -> SessionRepoPort:
    """Factory function to create a session repository.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        SessionRepoPort implementation
    """
    return SQLAlchemySessionRepository(session)