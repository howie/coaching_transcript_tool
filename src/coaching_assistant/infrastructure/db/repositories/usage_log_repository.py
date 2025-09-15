"""SQLAlchemy implementation of UsageLogRepoPort with domain model conversion.

This module provides the concrete implementation of usage log repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_

from ....core.repositories.ports import UsageLogRepoPort
from ....core.models.usage_log import UsageLog, TranscriptionType
from ..models.usage_log_model import UsageLogModel


class SQLAlchemyUsageLogRepository(UsageLogRepoPort):
    """SQLAlchemy implementation of the UsageLogRepoPort interface with domain conversion."""

    def __init__(self, session: DBSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def save(self, usage_log: UsageLog) -> UsageLog:
        """Save usage log entry.

        Args:
            usage_log: UsageLog domain entity to save

        Returns:
            Saved UsageLog domain entity with updated fields
        """
        try:
            if usage_log.id:
                # Update existing usage log
                orm_usage_log = self.session.get(UsageLogModel, usage_log.id)
                if orm_usage_log:
                    orm_usage_log.update_from_domain(usage_log)
                else:
                    # Usage log ID exists but not found in DB - create new
                    orm_usage_log = UsageLogModel.from_domain(usage_log)
                    self.session.add(orm_usage_log)
            else:
                # Create new usage log
                orm_usage_log = UsageLogModel.from_domain(usage_log)
                self.session.add(orm_usage_log)

            self.session.flush()  # Get the ID without committing
            return orm_usage_log.to_domain()

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving usage log") from e

    def get_by_session_id(self, session_id: UUID) -> List[UsageLog]:
        """Get all usage logs for a session.

        Args:
            session_id: UUID of the session

        Returns:
            List of UsageLog domain entities for the session
        """
        try:
            orm_usage_logs = (
                self.session.query(UsageLogModel)
                .filter(UsageLogModel.session_id == session_id)
                .order_by(UsageLogModel.created_at)
                .all()
            )
            return [orm_usage_log.to_domain() for orm_usage_log in orm_usage_logs]
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
            List of UsageLog domain entities
        """
        try:
            query = self.session.query(UsageLogModel).filter(UsageLogModel.user_id == user_id)

            if start_date is not None:
                query = query.filter(UsageLogModel.created_at >= start_date)

            if end_date is not None:
                query = query.filter(UsageLogModel.created_at <= end_date)

            orm_usage_logs = query.order_by(UsageLogModel.created_at).all()
            return [orm_usage_log.to_domain() for orm_usage_log in orm_usage_logs]
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
            Total cost as Decimal (in primary currency)
        """
        try:
            query = (
                self.session.query(func.sum(UsageLogModel.cost_cents))
                .filter(
                    and_(
                        UsageLogModel.user_id == user_id,
                        UsageLogModel.billable == True  # noqa: E712
                    )
                )
            )

            if start_date is not None:
                query = query.filter(UsageLogModel.created_at >= start_date)

            if end_date is not None:
                query = query.filter(UsageLogModel.created_at <= end_date)

            result_cents = query.scalar() or 0
            # Convert cents to main currency unit
            return Decimal(str(result_cents / 100))
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
                self.session.query(UsageLogModel)
                .filter(
                    and_(
                        UsageLogModel.user_id == user_id,
                        UsageLogModel.created_at >= period_start,
                        UsageLogModel.created_at <= period_end
                    )
                )
            )

            # Total sessions
            total_sessions = base_query.count()

            # Total duration in minutes
            total_duration = (
                base_query
                .with_entities(func.sum(UsageLogModel.duration_minutes))
                .scalar()
            ) or 0

            # Total cost (convert from cents to main currency)
            total_cost_cents = (
                base_query
                .filter(UsageLogModel.billable == True)  # noqa: E712
                .with_entities(func.sum(UsageLogModel.cost_cents))
                .scalar()
            ) or 0
            total_cost = float(total_cost_cents / 100)

            # Breakdown by transcription type
            type_breakdown = {}
            for transcription_type in TranscriptionType:
                count = (
                    base_query
                    .filter(UsageLogModel.transcription_type == transcription_type)
                    .count()
                )
                type_breakdown[transcription_type.value] = count

            # Breakdown by STT provider
            provider_breakdown = (
                base_query
                .with_entities(
                    UsageLogModel.stt_provider,
                    func.count(UsageLogModel.id).label('count')
                )
                .group_by(UsageLogModel.stt_provider)
                .all()
            )
            provider_dict = {
                provider: count for provider, count in provider_breakdown
            }

            return {
                'total_sessions': total_sessions,
                'total_duration_minutes': total_duration,
                'total_cost_usd': total_cost,  # Legacy field name for compatibility
                'transcription_type_breakdown': type_breakdown,
                'stt_provider_breakdown': provider_dict,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
            }
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting usage summary for user {user_id}") from e


def create_usage_log_repository(session: DBSession) -> UsageLogRepoPort:
    """Factory function to create a usage log repository.

    Args:
        session: SQLAlchemy session

    Returns:
        UsageLogRepoPort implementation
    """
    return SQLAlchemyUsageLogRepository(session)