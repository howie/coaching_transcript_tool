"""SQLAlchemy implementation of UsageHistoryRepoPort with domain model conversion.

This module provides the concrete implementation of usage history repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DBSession

from ....core.models.usage_history import UsageHistory
from ....core.repositories.ports import UsageHistoryRepoPort
from ....models.usage_history import UsageHistory as UsageHistoryModel


class SQLAlchemyUsageHistoryRepository(UsageHistoryRepoPort):
    """SQLAlchemy implementation of the UsageHistoryRepoPort interface with domain conversion."""

    def __init__(self, session: DBSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def save(self, usage_history: UsageHistory) -> UsageHistory:
        """Save usage history snapshot.

        Args:
            usage_history: UsageHistory domain entity to save

        Returns:
            Saved UsageHistory domain entity with updated fields
        """
        try:
            if usage_history.id:
                # Update existing usage history
                orm_usage_history = self.session.get(
                    UsageHistoryModel, usage_history.id
                )
                if orm_usage_history:
                    self._update_orm_from_domain(orm_usage_history, usage_history)
                else:
                    # Usage history ID exists but not found in DB - create new
                    orm_usage_history = self._create_orm_from_domain(usage_history)
                    self.session.add(orm_usage_history)
            else:
                # Create new usage history
                orm_usage_history = self._create_orm_from_domain(usage_history)
                self.session.add(orm_usage_history)

            self.session.flush()  # Get the ID without committing
            return self._convert_orm_to_domain(orm_usage_history)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError("Database error saving usage history") from e

    def get_by_user_and_period(
        self,
        user_id: UUID,
        period_type: str,
        period_start: datetime,
    ) -> Optional[UsageHistory]:
        """Get usage history for specific period.

        Args:
            user_id: UUID of the user
            period_type: Type of period (hourly, daily, monthly)
            period_start: Start of the period

        Returns:
            UsageHistory domain entity if found, None otherwise
        """
        try:
            orm_usage_history = (
                self.session.query(UsageHistoryModel)
                .filter(
                    UsageHistoryModel.user_id == user_id,
                    UsageHistoryModel.period_type == period_type,
                    UsageHistoryModel.period_start == period_start,
                )
                .first()
            )

            if orm_usage_history:
                return self._convert_orm_to_domain(orm_usage_history)
            return None

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving usage history for user {user_id} "
                f"period {period_type} start {period_start}"
            ) from e

    def get_trends_for_user(
        self,
        user_id: UUID,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[UsageHistory]:
        """Get usage trends for user across time periods.

        Args:
            user_id: UUID of the user
            period_type: Type of period (hourly, daily, monthly)
            start_date: Start date for trend analysis
            end_date: End date for trend analysis

        Returns:
            List of UsageHistory domain entities ordered by period_start
        """
        try:
            orm_usage_histories = (
                self.session.query(UsageHistoryModel)
                .filter(
                    UsageHistoryModel.user_id == user_id,
                    UsageHistoryModel.period_type == period_type,
                    UsageHistoryModel.period_start >= start_date,
                    UsageHistoryModel.period_start <= end_date,
                )
                .order_by(UsageHistoryModel.period_start)
                .all()
            )

            return [self._convert_orm_to_domain(orm) for orm in orm_usage_histories]

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving usage trends for user {user_id} "
                f"from {start_date} to {end_date}"
            ) from e

    def _create_orm_from_domain(self, usage_history: UsageHistory) -> UsageHistoryModel:
        """Create ORM entity from domain entity.

        Args:
            usage_history: Domain entity

        Returns:
            ORM entity
        """
        return UsageHistoryModel(
            id=usage_history.id,
            user_id=usage_history.user_id,
            recorded_at=usage_history.recorded_at,
            period_type=usage_history.period_type,
            period_start=usage_history.period_start,
            period_end=usage_history.period_end,
            sessions_created=usage_history.sessions_created,
            audio_minutes_processed=usage_history.audio_minutes_processed,
            transcriptions_completed=usage_history.transcriptions_completed,
            exports_generated=usage_history.exports_generated,
            storage_used_mb=usage_history.storage_used_mb,
            unique_clients=usage_history.unique_clients,
            api_calls_made=usage_history.api_calls_made,
            concurrent_sessions_peak=usage_history.concurrent_sessions_peak,
            plan_name=usage_history.plan_name,
            plan_limits=usage_history.plan_limits,
            total_cost_usd=usage_history.total_cost_usd,
            billable_transcriptions=usage_history.billable_transcriptions,
            free_retries=usage_history.free_retries,
            google_stt_minutes=usage_history.google_stt_minutes,
            assemblyai_minutes=usage_history.assemblyai_minutes,
            exports_by_format=usage_history.exports_by_format,
            avg_processing_time_seconds=usage_history.avg_processing_time_seconds,
            failed_transcriptions=usage_history.failed_transcriptions,
            created_at=usage_history.created_at,
            updated_at=usage_history.updated_at,
        )

    def _update_orm_from_domain(
        self, orm_entity: UsageHistoryModel, domain_entity: UsageHistory
    ) -> None:
        """Update ORM entity from domain entity.

        Args:
            orm_entity: ORM entity to update
            domain_entity: Domain entity with new data
        """
        orm_entity.user_id = domain_entity.user_id
        orm_entity.recorded_at = domain_entity.recorded_at
        orm_entity.period_type = domain_entity.period_type
        orm_entity.period_start = domain_entity.period_start
        orm_entity.period_end = domain_entity.period_end
        orm_entity.sessions_created = domain_entity.sessions_created
        orm_entity.audio_minutes_processed = domain_entity.audio_minutes_processed
        orm_entity.transcriptions_completed = domain_entity.transcriptions_completed
        orm_entity.exports_generated = domain_entity.exports_generated
        orm_entity.storage_used_mb = domain_entity.storage_used_mb
        orm_entity.unique_clients = domain_entity.unique_clients
        orm_entity.api_calls_made = domain_entity.api_calls_made
        orm_entity.concurrent_sessions_peak = domain_entity.concurrent_sessions_peak
        orm_entity.plan_name = domain_entity.plan_name
        orm_entity.plan_limits = domain_entity.plan_limits
        orm_entity.total_cost_usd = domain_entity.total_cost_usd
        orm_entity.billable_transcriptions = domain_entity.billable_transcriptions
        orm_entity.free_retries = domain_entity.free_retries
        orm_entity.google_stt_minutes = domain_entity.google_stt_minutes
        orm_entity.assemblyai_minutes = domain_entity.assemblyai_minutes
        orm_entity.exports_by_format = domain_entity.exports_by_format
        orm_entity.avg_processing_time_seconds = (
            domain_entity.avg_processing_time_seconds
        )
        orm_entity.failed_transcriptions = domain_entity.failed_transcriptions
        orm_entity.updated_at = domain_entity.updated_at

    def _convert_orm_to_domain(self, orm_entity: UsageHistoryModel) -> UsageHistory:
        """Convert ORM entity to domain entity.

        Args:
            orm_entity: ORM entity

        Returns:
            Domain entity
        """
        return UsageHistory(
            id=orm_entity.id,
            user_id=orm_entity.user_id,
            recorded_at=orm_entity.recorded_at,
            period_type=orm_entity.period_type,
            period_start=orm_entity.period_start,
            period_end=orm_entity.period_end,
            sessions_created=orm_entity.sessions_created,
            audio_minutes_processed=Decimal(str(orm_entity.audio_minutes_processed)),
            transcriptions_completed=orm_entity.transcriptions_completed,
            exports_generated=orm_entity.exports_generated,
            storage_used_mb=Decimal(str(orm_entity.storage_used_mb)),
            unique_clients=orm_entity.unique_clients,
            api_calls_made=orm_entity.api_calls_made,
            concurrent_sessions_peak=orm_entity.concurrent_sessions_peak,
            plan_name=orm_entity.plan_name,
            plan_limits=orm_entity.plan_limits or {},
            total_cost_usd=Decimal(str(orm_entity.total_cost_usd)),
            billable_transcriptions=orm_entity.billable_transcriptions,
            free_retries=orm_entity.free_retries,
            google_stt_minutes=Decimal(str(orm_entity.google_stt_minutes)),
            assemblyai_minutes=Decimal(str(orm_entity.assemblyai_minutes)),
            exports_by_format=orm_entity.exports_by_format or {},
            avg_processing_time_seconds=Decimal(
                str(orm_entity.avg_processing_time_seconds)
            ),
            failed_transcriptions=orm_entity.failed_transcriptions,
            created_at=orm_entity.created_at,
            updated_at=orm_entity.updated_at,
        )


def create_usage_history_repository(
    session: DBSession,
) -> UsageHistoryRepoPort:
    """Factory function to create a UsageHistoryRepository instance.

    Args:
        session: SQLAlchemy database session

    Returns:
        UsageHistoryRepoPort implementation
    """
    return SQLAlchemyUsageHistoryRepository(session)
