"""SQLAlchemy implementation of CoachingSessionRepoPort with domain model conversion.

This module provides the concrete implementation of coaching session repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from typing import Optional, List, Tuple
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc, asc

from ....core.repositories.ports import CoachingSessionRepoPort
from ....core.models.coaching_session import CoachingSession as DomainCoachingSession
from ....core.models.coaching_session import SessionSource as DomainSessionSource
from ....models.coaching_session import CoachingSession as CoachingSessionModel
from ....models.coaching_session import SessionSource as DatabaseSessionSource
from ....models.client import Client as ClientModel
from ....models.session import Session as TranscriptionSessionModel


class SQLAlchemyCoachingSessionRepository(CoachingSessionRepoPort):
    """SQLAlchemy implementation of CoachingSessionRepoPort with domain conversion."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def _to_domain(self, orm_session: CoachingSessionModel) -> DomainCoachingSession:
        """Convert ORM CoachingSession to domain CoachingSession model."""
        if not orm_session:
            return None

        # Convert database enum to domain enum value
        if isinstance(orm_session.source, DatabaseSessionSource):
            domain_source = DomainSessionSource(orm_session.source.value)
        elif isinstance(orm_session.source, str):
            domain_source = DomainSessionSource(orm_session.source)
        else:
            # Fallback to value extraction
            domain_source = DomainSessionSource(orm_session.source.value if hasattr(orm_session.source, 'value') else orm_session.source)

        return DomainCoachingSession(
            id=orm_session.id,
            user_id=orm_session.user_id,
            client_id=orm_session.client_id,
            session_date=orm_session.session_date,
            source=domain_source,
            duration_min=orm_session.duration_min,
            fee_currency=orm_session.fee_currency,
            fee_amount=orm_session.fee_amount,
            transcription_session_id=orm_session.transcription_session_id,
            notes=orm_session.notes,
            created_at=orm_session.created_at,
            updated_at=orm_session.updated_at,
        )

    def _create_orm_session(self, session: DomainCoachingSession) -> CoachingSessionModel:
        """Create ORM coaching session from domain coaching session."""
        # Convert domain enum to database enum value
        if isinstance(session.source, DomainSessionSource):
            database_source = DatabaseSessionSource(session.source.value)
        elif isinstance(session.source, str):
            database_source = DatabaseSessionSource(session.source)
        else:
            # Fallback to value extraction
            database_source = DatabaseSessionSource(session.source.value if hasattr(session.source, 'value') else session.source)

        orm_session = CoachingSessionModel(
            id=session.id,
            user_id=session.user_id,
            client_id=session.client_id,
            session_date=session.session_date,
            source=database_source,
            duration_min=session.duration_min,
            fee_currency=session.fee_currency,
            fee_amount=session.fee_amount,
            transcription_session_id=session.transcription_session_id,
            notes=session.notes,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        return orm_session

    def get_by_id(self, session_id: UUID) -> Optional[DomainCoachingSession]:
        """Get coaching session by ID.

        Args:
            session_id: UUID of the coaching session to retrieve

        Returns:
            CoachingSession domain entity or None if not found
        """
        try:
            orm_session = self.session.get(CoachingSessionModel, session_id)
            return self._to_domain(orm_session) if orm_session else None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving coaching session {session_id}") from e

    def get_by_coach_id(
        self,
        coach_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DomainCoachingSession]:
        """Get coaching sessions for a coach.

        Args:
            coach_id: UUID of the coach (user)
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of CoachingSession domain entities for the coach
        """
        try:
            orm_sessions = (
                self.session.query(CoachingSessionModel)
                .filter(CoachingSessionModel.user_id == coach_id)
                .order_by(desc(CoachingSessionModel.session_date))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._to_domain(orm_session) for orm_session in orm_sessions]
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving sessions for coach {coach_id}") from e

    def get_by_client_id(
        self,
        client_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DomainCoachingSession]:
        """Get coaching sessions for a client.

        Args:
            client_id: UUID of the client
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of CoachingSession domain entities for the client
        """
        try:
            orm_sessions = (
                self.session.query(CoachingSessionModel)
                .filter(CoachingSessionModel.client_id == client_id)
                .order_by(desc(CoachingSessionModel.session_date))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._to_domain(orm_session) for orm_session in orm_sessions]
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving sessions for client {client_id}") from e

    def save(self, session: DomainCoachingSession) -> DomainCoachingSession:
        """Save or update coaching session entity.

        Args:
            session: CoachingSession domain entity to save

        Returns:
            Saved CoachingSession domain entity with updated fields
        """
        try:
            if session.id:
                # Update existing session
                orm_session = self.session.get(CoachingSessionModel, session.id)
                if orm_session:
                    # Update existing session fields manually
                    orm_session.user_id = session.user_id
                    orm_session.client_id = session.client_id
                    orm_session.session_date = session.session_date
                    # Convert domain enum to database enum value
                    if isinstance(session.source, DomainSessionSource):
                        orm_session.source = DatabaseSessionSource(session.source.value)
                    elif isinstance(session.source, str):
                        orm_session.source = DatabaseSessionSource(session.source)
                    else:
                        # Fallback to value extraction
                        orm_session.source = DatabaseSessionSource(session.source.value if hasattr(session.source, 'value') else session.source)
                    orm_session.duration_min = session.duration_min
                    orm_session.fee_currency = session.fee_currency
                    orm_session.fee_amount = session.fee_amount
                    orm_session.transcription_session_id = session.transcription_session_id
                    orm_session.notes = session.notes
                    orm_session.updated_at = session.updated_at
                else:
                    # Session ID exists but not found in DB - create new
                    orm_session = self._create_orm_session(session)
                    self.session.add(orm_session)
            else:
                # Create new session
                orm_session = self._create_orm_session(session)
                self.session.add(orm_session)

            self.session.flush()  # Get the ID without committing
            return self._to_domain(orm_session)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving coaching session") from e

    def delete(self, session_id: UUID) -> bool:
        """Delete coaching session by ID.

        Args:
            session_id: UUID of the coaching session to delete

        Returns:
            True if session was deleted, False if not found
        """
        try:
            orm_session = self.session.get(CoachingSessionModel, session_id)
            if orm_session:
                self.session.delete(orm_session)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting coaching session {session_id}") from e

    def get_with_ownership_check(
        self, session_id: UUID, coach_id: UUID
    ) -> Optional[DomainCoachingSession]:
        """Get coaching session with ownership verification.

        Args:
            session_id: UUID of the coaching session to retrieve
            coach_id: UUID of the coach who should own the session

        Returns:
            CoachingSession domain entity or None if not found or not owned by coach
        """
        try:
            orm_session = (
                self.session.query(CoachingSessionModel)
                .filter(
                    and_(
                        CoachingSessionModel.id == session_id,
                        CoachingSessionModel.user_id == coach_id,
                    )
                )
                .first()
            )
            return self._to_domain(orm_session) if orm_session else None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving session {session_id} for coach {coach_id}") from e

    def get_paginated_with_filters(
        self,
        coach_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        client_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        sort: str = "-session_date",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[DomainCoachingSession], int]:
        """Get paginated coaching sessions with filtering and sorting.

        Args:
            coach_id: UUID of the coach
            from_date: Optional start date filter
            to_date: Optional end date filter
            client_id: Optional client filter
            currency: Optional currency filter
            sort: Sort field and direction (e.g., "session_date", "-session_date", "fee", "-fee")
            page: Page number (1-based)
            page_size: Number of sessions per page

        Returns:
            Tuple of (list of sessions, total count)
        """
        try:
            # Build base filter
            query_filter = CoachingSessionModel.user_id == coach_id

            # Apply filters
            if from_date:
                query_filter = and_(
                    query_filter, CoachingSessionModel.session_date >= from_date
                )
            if to_date:
                query_filter = and_(
                    query_filter, CoachingSessionModel.session_date <= to_date
                )
            if client_id:
                query_filter = and_(
                    query_filter, CoachingSessionModel.client_id == client_id
                )
            if currency:
                query_filter = and_(
                    query_filter, CoachingSessionModel.fee_currency == currency
                )

            # Build query with joins
            query = (
                self.session.query(CoachingSessionModel)
                .join(ClientModel, CoachingSessionModel.client_id == ClientModel.id)
                .outerjoin(
                    TranscriptionSessionModel,
                    CoachingSessionModel.transcription_session_id == TranscriptionSessionModel.id,
                )
                .filter(query_filter)
            )

            # Apply sorting
            if sort == "session_date":
                query = query.order_by(asc(CoachingSessionModel.session_date))
            elif sort == "-session_date":
                query = query.order_by(desc(CoachingSessionModel.session_date))
            elif sort == "fee":
                query = query.order_by(
                    asc(CoachingSessionModel.fee_currency), asc(CoachingSessionModel.fee_amount)
                )
            elif sort == "-fee":
                query = query.order_by(
                    desc(CoachingSessionModel.fee_currency),
                    desc(CoachingSessionModel.fee_amount),
                )

            # Get total count
            total = query.count()

            # Get paginated results
            offset = (page - 1) * page_size
            orm_sessions = query.offset(offset).limit(page_size).all()

            sessions = [self._to_domain(orm_session) for orm_session in orm_sessions]
            return sessions, total

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting paginated sessions for coach {coach_id}") from e

    def get_last_session_by_client(
        self, coach_id: UUID, client_id: UUID
    ) -> Optional[DomainCoachingSession]:
        """Get the most recent coaching session for a specific client.

        Args:
            coach_id: UUID of the coach
            client_id: UUID of the client

        Returns:
            Most recent CoachingSession domain entity or None if not found
        """
        try:
            orm_session = (
                self.session.query(CoachingSessionModel)
                .filter(
                    and_(
                        CoachingSessionModel.user_id == coach_id,
                        CoachingSessionModel.client_id == client_id,
                    )
                )
                .order_by(desc(CoachingSessionModel.session_date))
                .first()
            )
            return self._to_domain(orm_session) if orm_session else None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting last session for client {client_id}") from e

    def get_total_minutes_for_user(self, user_id: UUID) -> int:
        """Get total minutes from all coaching sessions for a user."""
        try:
            from sqlalchemy import func
            result = (
                self.session.query(
                    func.coalesce(func.sum(CoachingSessionModel.duration_min), 0)
                )
                .filter(CoachingSessionModel.user_id == user_id)
                .scalar()
            )
            return int(result or 0)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting total minutes for user {user_id}") from e

    def get_monthly_minutes_for_user(self, user_id: UUID, year: int, month: int) -> int:
        """Get total minutes for a user in a specific month."""
        try:
            from sqlalchemy import func, extract
            result = (
                self.session.query(
                    func.coalesce(func.sum(CoachingSessionModel.duration_min), 0)
                )
                .filter(
                    and_(
                        CoachingSessionModel.user_id == user_id,
                        extract("year", CoachingSessionModel.session_date) == year,
                        extract("month", CoachingSessionModel.session_date) == month,
                    )
                )
                .scalar()
            )
            return int(result or 0)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting monthly minutes for user {user_id}") from e

    def get_monthly_revenue_by_currency(
        self, user_id: UUID, year: int, month: int
    ) -> dict[str, int]:
        """Get revenue by currency for a user in a specific month."""
        try:
            from sqlalchemy import func, extract
            revenue_by_currency = {}
            revenue_results = (
                self.session.query(
                    CoachingSessionModel.fee_currency,
                    func.coalesce(func.sum(CoachingSessionModel.fee_amount), 0).label(
                        "total_amount"
                    ),
                )
                .filter(
                    and_(
                        CoachingSessionModel.user_id == user_id,
                        extract("year", CoachingSessionModel.session_date) == year,
                        extract("month", CoachingSessionModel.session_date) == month,
                    )
                )
                .group_by(CoachingSessionModel.fee_currency)
                .all()
            )

            for currency, amount in revenue_results:
                if currency:  # Skip None currencies
                    revenue_by_currency[currency] = int(amount or 0)

            return revenue_by_currency
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting monthly revenue for user {user_id}") from e

    def get_unique_clients_count_for_user(self, user_id: UUID) -> int:
        """Get count of unique clients for a user."""
        try:
            from sqlalchemy import func
            result = (
                self.session.query(
                    func.count(func.distinct(CoachingSessionModel.client_id))
                )
                .filter(CoachingSessionModel.user_id == user_id)
                .scalar()
            )
            return int(result or 0)
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting unique clients count for user {user_id}") from e


# Factory function for dependency injection
def create_coaching_session_repository(db_session: Session) -> CoachingSessionRepoPort:
    """Factory function to create CoachingSessionRepository with database session.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        CoachingSessionRepoPort implementation
    """
    return SQLAlchemyCoachingSessionRepository(db_session)