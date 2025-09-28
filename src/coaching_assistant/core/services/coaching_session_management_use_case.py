"""Coaching session management use cases for Clean Architecture.

This module contains the business logic for coaching session management operations,
following the Clean Architecture principles with dependency injection.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from ..models.coaching_session import CoachingSession, SessionSource
from ..repositories.ports import (
    ClientRepoPort,
    CoachingSessionRepoPort,
    SessionRepoPort,
    UserRepoPort,
)


class CoachingSessionRetrievalUseCase:
    """Use case for retrieving coaching session information."""

    def __init__(
        self,
        session_repo: CoachingSessionRepoPort,
        user_repo: UserRepoPort,
        client_repo: ClientRepoPort,
        transcription_session_repo: SessionRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            session_repo: Coaching session repository implementation
            user_repo: User repository implementation
            client_repo: Client repository implementation
            transcription_session_repo: Transcription session repository implementation
        """
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.client_repo = client_repo
        self.transcription_session_repo = transcription_session_repo

    def get_session_by_id(
        self, session_id: UUID, coach_id: UUID
    ) -> Optional[CoachingSession]:
        """Get a coaching session by ID with ownership verification.

        Args:
            session_id: UUID of the coaching session to retrieve
            coach_id: UUID of the coach requesting the session

        Returns:
            CoachingSession domain entity if found and owned by coach, None otherwise
        """
        return self.session_repo.get_with_ownership_check(session_id, coach_id)

    def list_sessions_paginated(
        self,
        coach_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        client_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        sort: str = "-session_date",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CoachingSession], int, int]:
        """List coaching sessions for a coach with pagination and optional filters.

        Args:
            coach_id: UUID of the coach
            from_date: Optional start date filter
            to_date: Optional end date filter
            client_id: Optional client filter
            currency: Optional currency filter
            sort: Sort field and direction
            page: Page number (1-based)
            page_size: Number of sessions per page

        Returns:
            Tuple of (sessions, total_count, total_pages)
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        sessions, total = self.session_repo.get_paginated_with_filters(
            coach_id,
            from_date,
            to_date,
            client_id,
            currency,
            sort,
            page,
            page_size,
        )

        total_pages = (total + page_size - 1) // page_size
        return sessions, total, total_pages

    def get_last_session_by_client(
        self, coach_id: UUID, client_id: UUID
    ) -> Optional[CoachingSession]:
        """Get the most recent coaching session for a specific client.

        Args:
            coach_id: UUID of the coach
            client_id: UUID of the client

        Returns:
            Most recent CoachingSession domain entity or None if not found

        Raises:
            ValueError: If coach or client not found
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        # Verify client exists and belongs to coach
        client = self.client_repo.get_by_id(client_id)
        if not client or client.user_id != coach_id:
            raise ValueError(
                f"Client with ID {client_id} not found or not owned by coach"
            )

        return self.session_repo.get_last_session_by_client(coach_id, client_id)

    def get_client_summary(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client summary data.

        Args:
            client_id: UUID of the client

        Returns:
            Dict with client data or None if not found
        """
        if not client_id:
            return None

        client = self.client_repo.get_by_id(client_id)
        if client:
            return {
                "id": client.id,
                "name": client.name,
                "is_anonymized": client.is_anonymized,
            }
        return None

    def get_transcription_session_summary(
        self, transcription_session_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get transcription session summary data.

        Args:
            transcription_session_id: UUID of the transcription session

        Returns:
            Dict with transcription session data or None if not found
        """
        if not transcription_session_id:
            return None

        session = self.transcription_session_repo.get_by_id(transcription_session_id)
        if session:
            return {
                "id": session.id,
                "status": session.status.value,
                "title": session.title,
                "segments_count": session.segments_count,
            }
        return None

    def get_session_with_response_data(
        self, session_id: UUID, coach_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get coaching session with all data needed for response.

        Args:
            session_id: UUID of the coaching session
            coach_id: UUID of the coach

        Returns:
            Dict with session and related data or None if not found
        """
        session = self.get_session_by_id(session_id, coach_id)
        if not session:
            return None

        # Get client data
        client_summary = self.get_client_summary(session.client_id)

        # Get transcription session data
        transcription_session_summary = None
        if session.transcription_session_id:
            transcription_session_summary = self.get_transcription_session_summary(
                session.transcription_session_id
            )

        return {
            "session": session,
            "client_summary": client_summary,
            "transcription_session_summary": transcription_session_summary,
        }

    def get_sessions_with_response_data(
        self,
        coach_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        client_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        sort: str = "-session_date",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Get paginated coaching sessions with all data needed for response.

        Args:
            coach_id: UUID of the coach
            from_date: Start date for filtering sessions
            to_date: End date for filtering sessions
            client_id: Optional client ID filter
            currency: Optional currency filter
            sort: Sort field and direction
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (sessions_with_data, total_count, total_pages)
        """
        sessions, total, total_pages = self.list_sessions_paginated(
            coach_id,
            from_date,
            to_date,
            client_id,
            currency,
            sort,
            page,
            page_size,
        )

        sessions_with_data = []
        for session in sessions:
            # Get client data
            client_summary = self.get_client_summary(session.client_id)

            # Get transcription session data
            transcription_session_summary = None
            if session.transcription_session_id:
                transcription_session_summary = self.get_transcription_session_summary(
                    session.transcription_session_id
                )

            sessions_with_data.append(
                {
                    "session": session,
                    "client_summary": client_summary,
                    "transcription_session_summary": (transcription_session_summary),
                }
            )

        return sessions_with_data, total, total_pages


class CoachingSessionCreationUseCase:
    """Use case for creating new coaching sessions."""

    def __init__(
        self,
        session_repo: CoachingSessionRepoPort,
        user_repo: UserRepoPort,
        client_repo: ClientRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            session_repo: Coaching session repository implementation
            user_repo: User repository implementation
            client_repo: Client repository implementation
        """
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.client_repo = client_repo

    def create_session(
        self,
        coach_id: UUID,
        session_date: date,
        client_id: UUID,
        source: SessionSource,
        duration_min: int,
        fee_currency: str,
        fee_amount: int,
        notes: Optional[str] = None,
    ) -> CoachingSession:
        """Create a new coaching session for a coach.

        Args:
            coach_id: UUID of the coach creating the session
            session_date: Date of the coaching session
            client_id: UUID of the client
            source: Source of the session (CLIENT, FRIEND, etc.)
            duration_min: Duration in minutes
            fee_currency: Currency code (e.g., TWD, USD)
            fee_amount: Fee amount in smallest currency unit
            notes: Optional notes

        Returns:
            Created CoachingSession domain entity

        Raises:
            ValueError: If coach doesn't exist, client doesn't exist, or validation fails
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        # Verify client exists and belongs to coach
        client = self.client_repo.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")
        if client.user_id != coach_id:
            raise ValueError(f"Client {client_id} does not belong to coach {coach_id}")

        # Create coaching session domain entity
        session = CoachingSession(
            user_id=coach_id,
            client_id=client_id,
            session_date=session_date,
            source=source,
            duration_min=duration_min,
            fee_currency=fee_currency.upper(),
            fee_amount=fee_amount,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Validate business rules
        if not session.validate():
            raise ValueError(
                "Invalid session data: duration must be positive, fee must be non-negative"
            )

        return self.session_repo.save(session)


class CoachingSessionUpdateUseCase:
    """Use case for updating existing coaching sessions."""

    def __init__(
        self,
        session_repo: CoachingSessionRepoPort,
        user_repo: UserRepoPort,
        client_repo: ClientRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            session_repo: Coaching session repository implementation
            user_repo: User repository implementation
            client_repo: Client repository implementation
        """
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.client_repo = client_repo

    def update_session(
        self,
        session_id: UUID,
        coach_id: UUID,
        session_date: Optional[date] = None,
        client_id: Optional[UUID] = None,
        source: Optional[SessionSource] = None,
        duration_min: Optional[int] = None,
        fee_currency: Optional[str] = None,
        fee_amount: Optional[int] = None,
        transcription_session_id: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> CoachingSession:
        """Update an existing coaching session.

        Args:
            session_id: UUID of the session to update
            coach_id: UUID of the coach updating the session
            session_date: Optional new session date
            client_id: Optional new client ID
            source: Optional new source
            duration_min: Optional new duration
            fee_currency: Optional new fee currency
            fee_amount: Optional new fee amount
            transcription_session_id: Optional transcription session ID
            notes: Optional new notes

        Returns:
            Updated CoachingSession domain entity

        Raises:
            ValueError: If session not found, not owned by coach, or validation fails
        """
        # Get existing session with ownership check
        session = self.session_repo.get_with_ownership_check(session_id, coach_id)
        if not session:
            raise ValueError("Coaching session not found")

        # Verify client belongs to coach if client_id is being updated
        if client_id and client_id != session.client_id:
            client = self.client_repo.get_by_id(client_id)
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
            if client.user_id != coach_id:
                raise ValueError(
                    f"Client {client_id} does not belong to coach {coach_id}"
                )

        # Update fields (only if provided)
        if session_date is not None:
            session.session_date = session_date
        if client_id is not None:
            session.client_id = client_id
        if source is not None:
            session.source = source
        if duration_min is not None:
            session.duration_min = duration_min
        if fee_currency is not None:
            session.fee_currency = fee_currency.upper()
        if fee_amount is not None:
            session.fee_amount = fee_amount
        if transcription_session_id is not None:
            session.transcription_session_id = transcription_session_id
        if notes is not None:
            session.notes = notes

        session.updated_at = datetime.utcnow()

        # Validate business rules
        if not session.validate():
            raise ValueError(
                "Invalid session data: duration must be positive, fee must be non-negative"
            )

        return self.session_repo.save(session)


class CoachingSessionDeletionUseCase:
    """Use case for deleting coaching sessions."""

    def __init__(
        self,
        session_repo: CoachingSessionRepoPort,
        user_repo: UserRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            session_repo: Coaching session repository implementation
            user_repo: User repository implementation
        """
        self.session_repo = session_repo
        self.user_repo = user_repo

    def delete_session(self, session_id: UUID, coach_id: UUID) -> bool:
        """Delete a coaching session (hard delete).

        Args:
            session_id: UUID of the session to delete
            coach_id: UUID of the coach deleting the session

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If session not found or not owned by coach
        """
        # Get existing session with ownership check
        session = self.session_repo.get_with_ownership_check(session_id, coach_id)
        if not session:
            raise ValueError("Coaching session not found")

        return self.session_repo.delete(session_id)


class CoachingSessionOptionsUseCase:
    """Use case for getting coaching session option lists."""

    def get_currency_options(self) -> List[Dict[str, str]]:
        """Get available currency options.

        Returns:
            List of currency options with value and label
        """
        return [
            {"value": "USD", "label": "USD - US Dollar"},
            {"value": "EUR", "label": "EUR - Euro"},
            {"value": "JPY", "label": "JPY - Japanese Yen"},
            {"value": "GBP", "label": "GBP - British Pound"},
            {"value": "AUD", "label": "AUD - Australian Dollar"},
            {"value": "CAD", "label": "CAD - Canadian Dollar"},
            {"value": "CHF", "label": "CHF - Swiss Franc"},
            {"value": "CNY", "label": "CNY - Chinese Yuan"},
            {"value": "SEK", "label": "SEK - Swedish Krona"},
            {"value": "NZD", "label": "NZD - New Zealand Dollar"},
            {"value": "MXN", "label": "MXN - Mexican Peso"},
            {"value": "SGD", "label": "SGD - Singapore Dollar"},
            {"value": "HKD", "label": "HKD - Hong Kong Dollar"},
            {"value": "NOK", "label": "NOK - Norwegian Krone"},
            {"value": "KRW", "label": "KRW - South Korean Won"},
            {"value": "TRY", "label": "TRY - Turkish Lira"},
            {"value": "RUB", "label": "RUB - Russian Ruble"},
            {"value": "INR", "label": "INR - Indian Rupee"},
            {"value": "BRL", "label": "BRL - Brazilian Real"},
            {"value": "ZAR", "label": "ZAR - South African Rand"},
            {"value": "TWD", "label": "TWD - Taiwan Dollar"},
        ]
