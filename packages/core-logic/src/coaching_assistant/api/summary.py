"""Dashboard summary API endpoints."""

from typing import Dict, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from pydantic import BaseModel

from ..core.database import get_db
from ..models import CoachingSession, Client, User, Session as TranscriptSession, SessionStatus
from ..api.auth import get_current_user_dependency

router = APIRouter()


class SummaryResponse(BaseModel):
    total_minutes: int
    current_month_minutes: int
    transcripts_converted_count: int
    current_month_revenue_by_currency: Dict[str, int]
    unique_clients_total: int


@router.get("/summary", response_model=SummaryResponse)
async def get_dashboard_summary(
    month: Optional[str] = Query(None, regex=r"^\d{4}-\d{2}$", description="Month in YYYY-MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get dashboard summary statistics."""
    # Default to current month if not specified
    if not month:
        now = datetime.now()
        month = f"{now.year:04d}-{now.month:02d}"
    
    year, month_num = map(int, month.split("-"))
    
    # Total minutes from all coaching sessions
    total_minutes_result = db.query(
        func.coalesce(func.sum(CoachingSession.duration_min), 0)
    ).filter(CoachingSession.coach_id == current_user.id).scalar()
    
    total_minutes = int(total_minutes_result or 0)
    
    # Current month minutes
    current_month_minutes_result = db.query(
        func.coalesce(func.sum(CoachingSession.duration_min), 0)
    ).filter(
        and_(
            CoachingSession.coach_id == current_user.id,
            extract('year', CoachingSession.session_date) == year,
            extract('month', CoachingSession.session_date) == month_num
        )
    ).scalar()
    
    current_month_minutes = int(current_month_minutes_result or 0)
    
    # Transcripts converted count (from transcript processing sessions)
    transcripts_converted_count = db.query(TranscriptSession).filter(
        and_(
            TranscriptSession.user_id == current_user.id,
            TranscriptSession.status == SessionStatus.COMPLETED
        )
    ).count()
    
    # Current month revenue by currency
    revenue_by_currency = {}
    revenue_results = db.query(
        CoachingSession.fee_currency,
        func.coalesce(func.sum(CoachingSession.fee_amount), 0).label('total_amount')
    ).filter(
        and_(
            CoachingSession.coach_id == current_user.id,
            extract('year', CoachingSession.session_date) == year,
            extract('month', CoachingSession.session_date) == month_num
        )
    ).group_by(CoachingSession.fee_currency).all()
    
    for currency, amount in revenue_results:
        revenue_by_currency[currency] = int(amount or 0)
    
    # Unique clients total (including anonymized ones)
    unique_clients_total = db.query(
        func.count(func.distinct(CoachingSession.client_id))
    ).filter(CoachingSession.coach_id == current_user.id).scalar()
    
    unique_clients_total = int(unique_clients_total or 0)
    
    return SummaryResponse(
        total_minutes=total_minutes,
        current_month_minutes=current_month_minutes,
        transcripts_converted_count=transcripts_converted_count,
        current_month_revenue_by_currency=revenue_by_currency,
        unique_clients_total=unique_clients_total
    )