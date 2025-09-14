"""SQLAlchemy implementation of UsageLogRepoPort.

This module provides the concrete implementation of usage log repository
operations using SQLAlchemy ORM.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_

from ....core.repositories.ports import UsageLogRepoPort
from ....models.usage_log import UsageLog, TranscriptionType


class SQLAlchemyUsageLogRepository(UsageLogRepoPort):
    """SQLAlchemy implementation of the UsageLogRepoPort interface."""

    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def save(self, usage_log: UsageLog) -> UsageLog:
        """Save usage log entry.
        
        Args:
            usage_log: UsageLog entity to save
            
        Returns:
            Saved usage log entity
        """
        try:
            if usage_log.id is None or not self._is_attached(usage_log):
                self.session.add(usage_log)
            
            self.session.commit()
            self.session.refresh(usage_log)
            return usage_log
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving usage log") from e

    def get_by_session_id(self, session_id: UUID) -> List[UsageLog]:
        """Get all usage logs for a session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            List of usage log entities for the session
        """
        try:
            return (
                self.session.query(UsageLog)
                .filter(UsageLog.session_id == session_id)
                .order_by(UsageLog.created_at)
                .all()
            )
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving usage logs for session {session_id}") from e

    def get_by_user_id(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UsageLog]:
        """Get usage logs for user within optional date range.
        
        Args:
            user_id: UUID of the user
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of usage log entities
        """
        try:
            query = self.session.query(UsageLog).filter(UsageLog.user_id == user_id)
            
            if start_date is not None:
                query = query.filter(UsageLog.created_at >= start_date)
            
            if end_date is not None:
                query = query.filter(UsageLog.created_at <= end_date)
            
            return query.order_by(UsageLog.created_at).all()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving usage logs for user {user_id}") from e

    def get_total_cost_for_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Decimal:
        """Calculate total cost for user within date range.
        
        Args:
            user_id: UUID of the user
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Total cost as Decimal
        """
        try:
            query = (
                self.session.query(func.sum(UsageLog.cost_usd))
                .filter(
                    and_(
                        UsageLog.user_id == user_id,
                        UsageLog.is_billable == True  # noqa: E712
                    )
                )
            )
            
            if start_date is not None:
                query = query.filter(UsageLog.created_at >= start_date)
            
            if end_date is not None:
                query = query.filter(UsageLog.created_at <= end_date)
            
            result = query.scalar()
            return result or Decimal('0.00')
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error calculating total cost for user {user_id}") from e

    def get_usage_summary(
        self, user_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Get aggregated usage summary for user in time period.
        
        Args:
            user_id: UUID of the user
            period_start: Start of the period
            period_end: End of the period
            
        Returns:
            Dictionary containing usage summary data
        """
        try:
            # Get basic counts and totals
            base_query = (
                self.session.query(UsageLog)
                .filter(
                    and_(
                        UsageLog.user_id == user_id,
                        UsageLog.created_at >= period_start,
                        UsageLog.created_at <= period_end
                    )
                )
            )
            
            # Total sessions
            total_sessions = base_query.count()
            
            # Total duration in minutes
            total_duration = (
                base_query
                .with_entities(func.sum(UsageLog.duration_minutes))
                .scalar()
            ) or 0
            
            # Total cost
            total_cost = (
                base_query
                .filter(UsageLog.is_billable == True)  # noqa: E712
                .with_entities(func.sum(UsageLog.cost_usd))
                .scalar()
            ) or Decimal('0.00')
            
            # Breakdown by transcription type
            type_breakdown = {}
            for transcription_type in TranscriptionType:
                count = (
                    base_query
                    .filter(UsageLog.transcription_type == transcription_type)
                    .count()
                )
                type_breakdown[transcription_type.value] = count
            
            # Breakdown by STT provider
            provider_breakdown = (
                base_query
                .with_entities(
                    UsageLog.stt_provider,
                    func.count(UsageLog.id).label('count')
                )
                .group_by(UsageLog.stt_provider)
                .all()
            )
            provider_dict = {
                provider: count for provider, count in provider_breakdown
            }
            
            return {
                'total_sessions': total_sessions,
                'total_duration_minutes': total_duration,
                'total_cost_usd': float(total_cost),
                'transcription_type_breakdown': type_breakdown,
                'stt_provider_breakdown': provider_dict,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
            }
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting usage summary for user {user_id}") from e

    def _is_attached(self, usage_log: UsageLog) -> bool:
        """Check if usage log entity is attached to current session.
        
        Args:
            usage_log: UsageLog entity to check
            
        Returns:
            True if attached to session
        """
        return usage_log in self.session


def create_usage_log_repository(session: Session) -> UsageLogRepoPort:
    """Factory function to create a usage log repository.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        UsageLogRepoPort implementation
    """
    return SQLAlchemyUsageLogRepository(session)