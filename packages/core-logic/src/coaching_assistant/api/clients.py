"""Client management API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..models import Client, CoachingSession, User
from ..api.auth import get_current_user_dependency

router = APIRouter()


# Pydantic models for request/response
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    memo: Optional[str] = None
    source: Optional[str] = None
    client_type: Optional[str] = None
    issue_types: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    memo: Optional[str] = None
    source: Optional[str] = None
    client_type: Optional[str] = None
    issue_types: Optional[str] = None


class ClientResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    memo: Optional[str]
    source: Optional[str]
    client_type: Optional[str]
    issue_types: Optional[str]
    is_anonymized: bool
    anonymized_at: Optional[str]
    session_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ClientListResponse(BaseModel):
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=ClientListResponse)
async def list_clients(
    query: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """List clients for the current user."""
    query_filter = and_(Client.coach_id == current_user.id)
    
    if query:
        search_filter = or_(
            Client.name.ilike(f"%{query}%"),
            Client.email.ilike(f"%{query}%")
        )
        query_filter = and_(query_filter, search_filter)
    
    # Get total count
    total = db.query(Client).filter(query_filter).count()
    
    # Get paginated results
    clients = (
        db.query(Client)
        .filter(query_filter)
        .order_by(Client.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    # Add session count for each client
    client_responses = []
    for client in clients:
        session_count = db.query(CoachingSession).filter(
            CoachingSession.client_id == client.id
        ).count()
        
        client_dict = {
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "memo": client.memo,
            "source": client.source,
            "client_type": client.client_type,
            "issue_types": client.issue_types,
            "is_anonymized": client.is_anonymized,
            "anonymized_at": client.anonymized_at.isoformat() if client.anonymized_at else None,
            "session_count": session_count,
            "created_at": client.created_at.isoformat(),
            "updated_at": client.updated_at.isoformat(),
        }
        client_responses.append(ClientResponse(**client_dict))
    
    total_pages = (total + page_size - 1) // page_size
    
    return ClientListResponse(
        items=client_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific client."""
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    session_count = db.query(CoachingSession).filter(
        CoachingSession.client_id == client.id
    ).count()
    
    client_dict = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "memo": client.memo,
        "source": client.source,
        "client_type": client.client_type,
        "issue_types": client.issue_types,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": client.anonymized_at.isoformat() if client.anonymized_at else None,
        "session_count": session_count,
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }
    
    return ClientResponse(**client_dict)


@router.post("", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new client."""
    # Check for duplicate email if provided
    if client_data.email:
        existing = db.query(Client).filter(
            and_(
                Client.coach_id == current_user.id,
                func.lower(Client.email) == client_data.email.lower(),
                Client.email.isnot(None)
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409, 
                detail="A client with this email already exists"
            )
    
    client = Client(
        coach_id=current_user.id,
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        memo=client_data.memo,
        source=client_data.source,
        client_type=client_data.client_type,
        issue_types=client_data.issue_types
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    client_dict = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "memo": client.memo,
        "source": client.source,
        "client_type": client.client_type,
        "issue_types": client.issue_types,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": client.anonymized_at.isoformat() if client.anonymized_at else None,
        "session_count": 0,
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }
    
    return ClientResponse(**client_dict)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update a client."""
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.is_anonymized:
        raise HTTPException(
            status_code=403, 
            detail="Cannot edit anonymized client"
        )
    
    # Check for duplicate email if email is being updated
    if client_data.email and client_data.email != client.email:
        existing = db.query(Client).filter(
            and_(
                Client.coach_id == current_user.id,
                func.lower(Client.email) == client_data.email.lower(),
                Client.email.isnot(None),
                Client.id != client_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409, 
                detail="A client with this email already exists"
            )
    
    # Update fields
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    session_count = db.query(CoachingSession).filter(
        CoachingSession.client_id == client.id
    ).count()
    
    client_dict = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "memo": client.memo,
        "source": client.source,
        "client_type": client.client_type,
        "issue_types": client.issue_types,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": client.anonymized_at.isoformat() if client.anonymized_at else None,
        "session_count": session_count,
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }
    
    return ClientResponse(**client_dict)


@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Delete a client (hard delete, only if no sessions)."""
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if client has any coaching sessions
    session_count = db.query(CoachingSession).filter(
        CoachingSession.client_id == client.id
    ).count()
    
    if session_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete client with existing sessions. Use anonymization instead."
        )
    
    db.delete(client)
    db.commit()
    
    return {"message": "Client deleted successfully"}


@router.post("/{client_id}/anonymize")
async def anonymize_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Anonymize a client for GDPR compliance."""
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.coach_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if client.is_anonymized:
        raise HTTPException(
            status_code=409, 
            detail="Client is already anonymized"
        )
    
    # Get next anonymous number for this coach
    anonymous_count = db.query(Client).filter(
        and_(Client.coach_id == current_user.id, Client.is_anonymized == True)
    ).count()
    
    next_number = anonymous_count + 1
    
    # Anonymize the client
    client.anonymize(next_number)
    
    db.commit()
    db.refresh(client)
    
    return {"message": f"Client anonymized as '{client.name}'"}


@router.get("/options/sources")
async def get_client_sources():
    """Get available client source options."""
    return [
        {"value": "referral", "label": "別人推薦"},
        {"value": "organic", "label": "自來客"},
        {"value": "friend", "label": "朋友"},
        {"value": "social_media", "label": "社群媒體"}
    ]


@router.get("/options/types")
async def get_client_types():
    """Get available client type options."""
    return [
        {"value": "paid", "label": "付費客戶"},
        {"value": "pro_bono", "label": "公益客戶"},
        {"value": "free_practice", "label": "免費練習"},
        {"value": "other", "label": "其他"}
    ]