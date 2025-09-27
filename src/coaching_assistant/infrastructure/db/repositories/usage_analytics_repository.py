"""SQLAlchemy implementation of UsageAnalyticsRepoPort with domain model conversion.

This module provides the concrete implementation of usage analytics repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, desc

from ....core.repositories.ports import UsageAnalyticsRepoPort
from ....core.models.usage_analytics import UsageAnalytics as UsageAnalyticsDomain
from ....models.usage_analytics import UsageAnalytics as UsageAnalyticsORM


class SQLAlchemyUsageAnalyticsRepository(UsageAnalyticsRepoPort):
    """SQLAlchemy implementation of the UsageAnalyticsRepoPort interface with domain conversion."""

    def __init__(self, session: DBSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_or_create_monthly(
        self, user_id: UUID, year: int, month: int
    ) -> UsageAnalyticsDomain:
        """Get or create monthly analytics record.

        Args:
            user_id: UUID of the user
            year: Year for analytics
            month: Month for analytics (1-12)

        Returns:
            UsageAnalytics domain entity
        """
        try:
            month_year = f"{year:04d}-{month:02d}"

            # Try to get existing record
            orm_analytics = (
                self.session.query(UsageAnalyticsORM)
                .filter(
                    and_(
                        UsageAnalyticsORM.user_id == user_id,
                        UsageAnalyticsORM.month_year == month_year
                    )
                )
                .first()
            )

            if orm_analytics:
                return self._orm_to_domain(orm_analytics)

            # Create new record
            orm_analytics = UsageAnalyticsORM(
                user_id=user_id,
                month_year=month_year,
                primary_plan="FREE",  # Default, should be updated
                period_start=datetime(year, month, 1),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(orm_analytics)
            self.session.flush()  # Get the ID without committing

            return self._orm_to_domain(orm_analytics)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error creating/retrieving monthly analytics") from e

    def update(self, analytics: UsageAnalyticsDomain) -> UsageAnalyticsDomain:
        """Update analytics record.

        Args:
            analytics: UsageAnalytics domain entity to update

        Returns:
            Updated UsageAnalytics domain entity
        """
        try:
            if not analytics.id:
                raise ValueError("Analytics record must have an ID to update")

            orm_analytics = self.session.get(UsageAnalyticsORM, analytics.id)
            if not orm_analytics:
                raise ValueError(f"Analytics record not found: {analytics.id}")

            # Update all fields from domain model
            orm_analytics.primary_plan = analytics.primary_plan
            orm_analytics.plan_changed_during_month = analytics.plan_changed_during_month
            orm_analytics.sessions_created = analytics.sessions_created
            orm_analytics.transcriptions_completed = analytics.transcriptions_completed
            orm_analytics.total_minutes_processed = analytics.total_minutes_processed
            orm_analytics.total_cost_usd = analytics.total_cost_usd
            orm_analytics.original_transcriptions = analytics.original_transcriptions
            orm_analytics.free_retries = analytics.free_retries
            orm_analytics.paid_retranscriptions = analytics.paid_retranscriptions
            orm_analytics.google_stt_minutes = analytics.google_stt_minutes
            orm_analytics.assemblyai_minutes = analytics.assemblyai_minutes
            orm_analytics.exports_by_format = analytics.exports_by_format
            orm_analytics.total_exports = analytics.total_exports
            orm_analytics.period_start = analytics.period_start
            orm_analytics.period_end = analytics.period_end
            orm_analytics.updated_at = datetime.utcnow()

            self.session.flush()
            return self._orm_to_domain(orm_analytics)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error updating analytics") from e

    def get_by_user(self, user_id: UUID) -> List[UsageAnalyticsDomain]:
        """Get all analytics records for a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of UsageAnalytics domain entities
        """
        try:
            orm_analytics_list = (
                self.session.query(UsageAnalyticsORM)
                .filter(UsageAnalyticsORM.user_id == user_id)
                .order_by(desc(UsageAnalyticsORM.month_year))
                .all()
            )

            return [self._orm_to_domain(orm_analytics) for orm_analytics in orm_analytics_list]

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving analytics for user {user_id}") from e

    def get_by_month_year(self, month_year: str) -> List[UsageAnalyticsDomain]:
        """Get all analytics records for a specific month.

        Args:
            month_year: Month in YYYY-MM format

        Returns:
            List of UsageAnalytics domain entities for all users in that month
        """
        try:
            orm_analytics_list = (
                self.session.query(UsageAnalyticsORM)
                .filter(UsageAnalyticsORM.month_year == month_year)
                .all()
            )

            return [self._orm_to_domain(orm_analytics) for orm_analytics in orm_analytics_list]

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving analytics for month {month_year}") from e

    def get_admin_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics for admin users.

        Returns:
            Dictionary containing admin analytics data
        """
        try:
            # Get the latest 90 days of analytics data
            total_users = (
                self.session.query(func.count(func.distinct(UsageAnalyticsORM.user_id)))
                .scalar()
            ) or 0

            total_transcriptions = (
                self.session.query(func.sum(UsageAnalyticsORM.transcriptions_completed))
                .scalar()
            ) or 0

            total_minutes = (
                self.session.query(func.sum(UsageAnalyticsORM.total_minutes_processed))
                .scalar()
            ) or Decimal('0')

            total_cost = (
                self.session.query(func.sum(UsageAnalyticsORM.total_cost_usd))
                .scalar()
            ) or Decimal('0')

            # Plan breakdown
            plan_breakdown = {}
            plan_stats = (
                self.session.query(
                    UsageAnalyticsORM.primary_plan,
                    func.count(func.distinct(UsageAnalyticsORM.user_id)).label('users'),
                    func.sum(UsageAnalyticsORM.transcriptions_completed).label('transcriptions'),
                    func.sum(UsageAnalyticsORM.total_minutes_processed).label('minutes'),
                    func.sum(UsageAnalyticsORM.total_cost_usd).label('cost')
                )
                .group_by(UsageAnalyticsORM.primary_plan)
                .all()
            )

            for plan, users, transcriptions, minutes, cost in plan_stats:
                plan_breakdown[plan] = {
                    "users": users or 0,
                    "transcriptions": transcriptions or 0,
                    "minutes": float(minutes or 0),
                    "cost": float(cost or 0)
                }

            # Provider breakdown
            total_google_minutes = (
                self.session.query(func.sum(UsageAnalyticsORM.google_stt_minutes))
                .scalar()
            ) or Decimal('0')

            total_assemblyai_minutes = (
                self.session.query(func.sum(UsageAnalyticsORM.assemblyai_minutes))
                .scalar()
            ) or Decimal('0')

            total_provider_minutes = total_google_minutes + total_assemblyai_minutes

            provider_breakdown = {
                "google": {
                    "minutes": float(total_google_minutes),
                    "percentage": (
                        float(total_google_minutes / total_provider_minutes * 100)
                        if total_provider_minutes > 0
                        else 0
                    )
                },
                "assemblyai": {
                    "minutes": float(total_assemblyai_minutes),
                    "percentage": (
                        float(total_assemblyai_minutes / total_provider_minutes * 100)
                        if total_provider_minutes > 0
                        else 0
                    )
                }
            }

            return {
                "total_users": total_users,
                "total_transcriptions": total_transcriptions,
                "total_minutes_processed": float(total_minutes),
                "total_hours_processed": float(total_minutes) / 60.0,
                "total_cost_usd": float(total_cost),
                "plan_breakdown": plan_breakdown,
                "provider_breakdown": provider_breakdown,
                "generated_at": datetime.utcnow().isoformat()
            }

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving admin analytics") from e

    def _orm_to_domain(self, orm_analytics: UsageAnalyticsORM) -> UsageAnalyticsDomain:
        """Convert ORM model to domain entity.

        Args:
            orm_analytics: SQLAlchemy ORM model

        Returns:
            Domain entity
        """
        return UsageAnalyticsDomain(
            id=orm_analytics.id,
            user_id=orm_analytics.user_id,
            month_year=orm_analytics.month_year,
            primary_plan=orm_analytics.primary_plan,
            plan_changed_during_month=orm_analytics.plan_changed_during_month,
            sessions_created=orm_analytics.sessions_created,
            transcriptions_completed=orm_analytics.transcriptions_completed,
            total_minutes_processed=orm_analytics.total_minutes_processed,
            total_cost_usd=orm_analytics.total_cost_usd,
            original_transcriptions=orm_analytics.original_transcriptions,
            free_retries=orm_analytics.free_retries,
            paid_retranscriptions=orm_analytics.paid_retranscriptions,
            google_stt_minutes=orm_analytics.google_stt_minutes,
            assemblyai_minutes=orm_analytics.assemblyai_minutes,
            exports_by_format=orm_analytics.exports_by_format or {},
            total_exports=orm_analytics.total_exports,
            period_start=orm_analytics.period_start,
            period_end=orm_analytics.period_end,
            created_at=orm_analytics.created_at,
            updated_at=orm_analytics.updated_at,
        )


def create_usage_analytics_repository(session: DBSession) -> UsageAnalyticsRepoPort:
    """Factory function to create a usage analytics repository.

    Args:
        session: SQLAlchemy session

    Returns:
        UsageAnalyticsRepoPort implementation
    """
    return SQLAlchemyUsageAnalyticsRepository(session)