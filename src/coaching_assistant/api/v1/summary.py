"""Dashboard summary API endpoints."""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ...core.models.user import User
from ...core.services.dashboard_summary_use_case import (
    DashboardSummaryRequest,
    DashboardSummaryUseCase,
)
from .auth import get_current_user_dependency
from .dependencies import get_dashboard_summary_use_case

router = APIRouter()


class SummaryResponse(BaseModel):
    total_minutes: int
    current_month_minutes: int
    transcripts_converted_count: int
    current_month_revenue_by_currency: Dict[str, int]
    unique_clients_total: int


@router.get("/summary", response_model=SummaryResponse)
async def get_dashboard_summary(
    month: Optional[str] = Query(
        None, pattern=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format"
    ),
    current_user: User = Depends(get_current_user_dependency),
    use_case: DashboardSummaryUseCase = Depends(get_dashboard_summary_use_case),
):
    """Get dashboard summary statistics."""
    request = DashboardSummaryRequest(user_id=current_user.id, month=month)
    response = use_case.execute(request)

    return SummaryResponse(
        total_minutes=response.total_minutes,
        current_month_minutes=response.current_month_minutes,
        transcripts_converted_count=response.transcripts_converted_count,
        current_month_revenue_by_currency=response.current_month_revenue_by_currency,
        unique_clients_total=response.unique_clients_total,
    )
