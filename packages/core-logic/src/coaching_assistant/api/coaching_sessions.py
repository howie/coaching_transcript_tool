"""Coaching sessions API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..models import CoachingSession, Client, User
from ..api.auth import get_current_user

router = APIRouter()


# Pydantic models for request/response
class CoachingSessionCreate(BaseModel):
    session_date: date
    client_id: UUID
    duration_min: int = Field(..., gt=0)
    fee_currency: str = Field(..., min_length=3, max_length=3)
    fee_amount: int = Field(..., ge=0)
    notes: Optional[str] = None


class CoachingSessionUpdate(BaseModel):
    session_date: Optional[date] = None
    client_id: Optional[UUID] = None
    duration_min: Optional[int] = Field(None, gt=0)
    fee_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    fee_amount: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class ClientSummary(BaseModel):
    id: UUID
    name: str
    is_anonymized: bool


class CoachingSessionResponse(BaseModel):
    id: UUID
    session_date: str
    client: ClientSummary
    duration_min: int
    fee_currency: str
    fee_amount: int
    fee_display: str
    duration_display: str
    transcript_timeseq_id: Optional[UUID]
    audio_timeseq_id: Optional[UUID]
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CoachingSessionListResponse(BaseModel):
    items: List[CoachingSessionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SessionSourceOption(BaseModel):
    value: str
    label: str


@router.get("", response_model=CoachingSessionListResponse)
async def list_coaching_sessions(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    client_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    sort: str = Query("-session_date", regex="^-?(session_date|fee)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List coaching sessions for the current user."""
    query_filter = and_(CoachingSession.coach_id == current_user.id)
    
    # Apply filters
    if from_date:
        query_filter = and_(query_filter, CoachingSession.session_date >= from_date)
    if to_date:
        query_filter = and_(query_filter, CoachingSession.session_date <= to_date)
    if client_id:
        query_filter = and_(query_filter, CoachingSession.client_id == client_id)
    if currency:
        query_filter = and_(query_filter, CoachingSession.fee_currency == currency)
    
    # Build query with joins
    query = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(query_filter)
    )
    
    # Apply sorting
    if sort == "session_date":
        query = query.order_by(asc(CoachingSession.session_date))
    elif sort == "-session_date":
        query = query.order_by(desc(CoachingSession.session_date))
    elif sort == "fee":
        query = query.order_by(asc(CoachingSession.fee_currency), asc(CoachingSession.fee_amount))
    elif sort == "-fee":
        query = query.order_by(desc(CoachingSession.fee_currency), desc(CoachingSession.fee_amount))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    sessions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    session_responses = []
    for session in sessions:
        client_summary = ClientSummary(
            id=session.client.id,
            name=session.client.name,
            is_anonymized=session.client.is_anonymized
        )
        
        session_dict = {
            "id": session.id,
            "session_date": session.session_date.isoformat(),
            "client": client_summary,
            "duration_min": session.duration_min,
            "fee_currency": session.fee_currency,
            "fee_amount": session.fee_amount,
            "fee_display": session.fee_display,
            "duration_display": session.duration_display,
            "transcript_timeseq_id": session.transcript_timeseq_id,
            "audio_timeseq_id": session.audio_timeseq_id,
            "notes": session.notes,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
        session_responses.append(CoachingSessionResponse(**session_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return CoachingSessionListResponse(
        items=session_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{session_id}", response_model=CoachingSessionResponse)
async def get_coaching_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific coaching session."""
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(
            and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
        ).first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.post("", response_model=CoachingSessionResponse)
async def create_coaching_session(
    session_data: CoachingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new coaching session."""
    # Verify client belongs to current user
    client = db.query(Client).filter(
        and_(Client.id == session_data.client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    session = CoachingSession(
        coach_id=current_user.id,
        session_date=session_data.session_date,
        client_id=session_data.client_id,
        duration_min=session_data.duration_min,
        fee_currency=session_data.fee_currency.upper(),
        fee_amount=session_data.fee_amount,
        notes=session_data.notes
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Reload to get client data
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(CoachingSession.id == session.id)
        .first()
    )
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.patch("/{session_id}", response_model=CoachingSessionResponse)
async def update_coaching_session(
    session_id: UUID,
    session_data: CoachingSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a coaching session."""
    session = db.query(CoachingSession).filter(
        and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    # Verify client belongs to current user if client_id is being updated
    if session_data.client_id and session_data.client_id != session.client_id:
        client = db.query(Client).filter(
            and_(Client.id == session_data.client_id, Client.coach_id == current_user.id)
        ).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    # Update fields
    update_data = session_data.dict(exclude_unset=True)
    if 'fee_currency' in update_data:
        update_data['fee_currency'] = update_data['fee_currency'].upper()
    
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    # Reload to get client data
    session = (
        db.query(CoachingSession)
        .join(Client, CoachingSession.client_id == Client.id)
        .filter(CoachingSession.id == session.id)
        .first()
    )
    
    client_summary = ClientSummary(
        id=session.client.id,
        name=session.client.name,
        is_anonymized=session.client.is_anonymized
    )
    
    session_dict = {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "client": client_summary,
        "duration_min": session.duration_min,
        "fee_currency": session.fee_currency,
        "fee_amount": session.fee_amount,
        "fee_display": session.fee_display,
        "duration_display": session.duration_display,
        "transcript_timeseq_id": session.transcript_timeseq_id,
        "audio_timeseq_id": session.audio_timeseq_id,
        "notes": session.notes,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
    
    return CoachingSessionResponse(**session_dict)


@router.delete("/{session_id}")
async def delete_coaching_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a coaching session (hard delete)."""
    session = db.query(CoachingSession).filter(
        and_(CoachingSession.id == session_id, CoachingSession.coach_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    
    db.delete(session)
    db.commit()
    
    return {"message": "Coaching session deleted successfully"}


@router.get("/options/currencies", response_model=List[str])
async def get_currencies():
    """Get available currency options."""
    return [
        "USD",  # US Dollar
        "EUR",  # Euro
        "JPY",  # Japanese Yen
        "GBP",  # British Pound
        "AUD",  # Australian Dollar
        "CAD",  # Canadian Dollar
        "CHF",  # Swiss Franc
        "CNY",  # Chinese Yuan
        "SEK",  # Swedish Krona
        "NZD",  # New Zealand Dollar
        "MXN",  # Mexican Peso
        "SGD",  # Singapore Dollar
        "HKD",  # Hong Kong Dollar
        "NOK",  # Norwegian Krone
        "KRW",  # South Korean Won
        "TRY",  # Turkish Lira
        "RUB",  # Russian Ruble
        "INR",  # Indian Rupee
        "BRL",  # Brazilian Real
        "ZAR",  # South African Rand
        "NTD",  # New Taiwan Dollar
        "TWD"   # Taiwan Dollar (alternative code)
    ]