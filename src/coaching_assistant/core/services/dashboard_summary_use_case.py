"""Dashboard summary use case for user statistics."""

from datetime import datetime
from typing import Dict
from uuid import UUID

from ..repositories.ports import (
    CoachingSessionRepoPort,
    SessionRepoPort,
)


class DashboardSummaryRequest:
    """Request for dashboard summary."""

    def __init__(self, user_id: UUID, month: str = None):
        self.user_id = user_id
        self.month = month


class DashboardSummaryResponse:
    """Response for dashboard summary."""

    def __init__(
        self,
        total_minutes: int,
        current_month_minutes: int,
        transcripts_converted_count: int,
        current_month_revenue_by_currency: Dict[str, int],
        unique_clients_total: int,
    ):
        self.total_minutes = total_minutes
        self.current_month_minutes = current_month_minutes
        self.transcripts_converted_count = transcripts_converted_count
        self.current_month_revenue_by_currency = current_month_revenue_by_currency
        self.unique_clients_total = unique_clients_total


class DashboardSummaryUseCase:
    """Use case for retrieving dashboard summary statistics."""

    def __init__(
        self,
        coaching_session_repo: CoachingSessionRepoPort,
        session_repo: SessionRepoPort,
    ):
        self.coaching_session_repo = coaching_session_repo
        self.session_repo = session_repo

    def execute(self, request: DashboardSummaryRequest) -> DashboardSummaryResponse:
        """Execute dashboard summary retrieval."""
        # Default to current month if not specified
        if not request.month:
            now = datetime.now()
            month = f"{now.year:04d}-{now.month:02d}"
        else:
            month = request.month

        year, month_num = map(int, month.split("-"))

        # Get total minutes from all coaching sessions
        total_minutes = self.coaching_session_repo.get_total_minutes_for_user(
            request.user_id
        )

        # Get current month minutes
        current_month_minutes = self.coaching_session_repo.get_monthly_minutes_for_user(
            request.user_id, year, month_num
        )

        # Get transcripts converted count
        transcripts_converted_count = self.session_repo.get_completed_count_for_user(
            request.user_id
        )

        # Get current month revenue by currency
        current_month_revenue_by_currency = self.coaching_session_repo.get_monthly_revenue_by_currency(
            request.user_id, year, month_num
        )

        # Get unique clients total
        unique_clients_total = self.coaching_session_repo.get_unique_clients_count_for_user(
            request.user_id
        )

        return DashboardSummaryResponse(
            total_minutes=total_minutes,
            current_month_minutes=current_month_minutes,
            transcripts_converted_count=transcripts_converted_count,
            current_month_revenue_by_currency=current_month_revenue_by_currency,
            unique_clients_total=unique_clients_total,
        )