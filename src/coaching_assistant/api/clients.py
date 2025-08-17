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
    status: Optional[str] = Field(default="first_session")


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    memo: Optional[str] = None
    source: Optional[str] = None
    client_type: Optional[str] = None
    issue_types: Optional[str] = None
    status: Optional[str] = None


class ClientResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    memo: Optional[str]
    source: Optional[str]
    client_type: Optional[str]
    issue_types: Optional[str]
    status: str
    is_anonymized: bool
    anonymized_at: Optional[str]
    session_count: int
    total_payment_amount: int
    total_payment_currency: str
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
    current_user: User = Depends(get_current_user_dependency),
):
    """List clients for the current user."""
    query_filter = and_(Client.user_id == current_user.id)

    if query:
        search_filter = or_(
            Client.name.ilike(f"%{query}%"), Client.email.ilike(f"%{query}%")
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

    # Add session count and payment totals for each client
    client_responses = []
    for client in clients:
        session_count = (
            db.query(CoachingSession)
            .filter(CoachingSession.client_id == client.id)
            .count()
        )

        # Calculate payment totals (assuming TWD as primary currency for now)
        payment_total = (
            db.query(func.sum(CoachingSession.fee_amount))
            .filter(
                CoachingSession.client_id == client.id,
                CoachingSession.fee_currency == "TWD",
            )
            .scalar()
            or 0
        )

        client_dict = {
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "memo": client.memo,
            "source": client.source,
            "client_type": client.client_type,
            "issue_types": client.issue_types,
            "status": client.status,
            "is_anonymized": client.is_anonymized,
            "anonymized_at": (
                client.anonymized_at.isoformat() if client.anonymized_at else None
            ),
            "session_count": session_count,
            "total_payment_amount": payment_total,
            "total_payment_currency": "TWD",
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
        total_pages=total_pages,
    )


# Statistics endpoints must be before /{client_id} to avoid path conflicts
@router.get("/statistics")
async def get_client_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
) -> dict:
    """Get client statistics for charts."""
    try:
        print(f"Statistics request from user: {current_user.id}")

        # Get all clients for the coach
        clients = db.query(Client).filter(Client.user_id == current_user.id).all()
        print(f"Found {len(clients)} clients")

        # Initialize empty distributions
        source_distribution = []
        type_distribution = []
        issue_distribution = []

        if clients:
            # Translation mappings for display names
            source_labels = {
                "referral": "別人推薦",
                "organic": "自然搜尋",
                "friend": "朋友介紹",
                "social_media": "社群媒體",
                "advertisement": "廣告",
                "website": "官方網站",
            }

            type_labels = {
                "paid": "付費客戶",
                "pro_bono": "公益服務",
                "free_practice": "免費練習",
                "other": "其他",
            }

            # Source statistics
            source_counts = {}
            for client in clients:
                source_key = client.source or "unknown"
                source_name = source_labels.get(source_key, source_key or "未知")
                source_counts[source_name] = source_counts.get(source_name, 0) + 1

            source_distribution = [
                {"name": name, "value": count} for name, count in source_counts.items()
            ]

            # Type statistics
            type_counts = {}
            for client in clients:
                type_key = client.client_type or "unknown"
                type_name = type_labels.get(type_key, type_key or "未知")
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            type_distribution = [
                {"name": name, "value": count} for name, count in type_counts.items()
            ]

            # Issue type statistics
            issue_counts = {}
            for client in clients:
                if client.issue_types:
                    issues = [issue.strip() for issue in client.issue_types.split(",")]
                    for issue in issues:
                        if issue:
                            issue_counts[issue] = issue_counts.get(issue, 0) + 1
                else:
                    issue_counts["未知"] = issue_counts.get("未知", 0) + 1

            issue_distribution = [
                {"name": name, "value": count} for name, count in issue_counts.items()
            ]

        result = {
            "source_distribution": source_distribution,
            "type_distribution": type_distribution,
            "issue_distribution": issue_distribution,
        }

        print(f"Returning statistics: {result}")
        return result

    except Exception as e:
        print(f"Error in get_client_statistics: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "source_distribution": [],
            "type_distribution": [],
            "issue_distribution": [],
        }


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Get a specific client."""
    client = (
        db.query(Client)
        .filter(and_(Client.id == client_id, Client.user_id == current_user.id))
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    session_count = (
        db.query(CoachingSession).filter(CoachingSession.client_id == client.id).count()
    )

    # Calculate payment totals (assuming NTD as primary currency for now)
    payment_total = (
        db.query(func.sum(CoachingSession.fee_amount))
        .filter(
            CoachingSession.client_id == client.id,
            CoachingSession.fee_currency == "NTD",
        )
        .scalar()
        or 0
    )

    client_dict = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "memo": client.memo,
        "source": client.source,
        "client_type": client.client_type,
        "issue_types": client.issue_types,
        "status": client.status,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": (
            client.anonymized_at.isoformat() if client.anonymized_at else None
        ),
        "session_count": session_count,
        "total_payment_amount": payment_total,
        "total_payment_currency": "TWD",
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }

    return ClientResponse(**client_dict)


@router.post("", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Create a new client."""
    # Check for duplicate email if provided
    if client_data.email:
        existing = (
            db.query(Client)
            .filter(
                and_(
                    Client.user_id == current_user.id,
                    func.lower(Client.email) == client_data.email.lower(),
                    Client.email.isnot(None),
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409, detail="A client with this email already exists"
            )

    client = Client(
        user_id=current_user.id,
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        memo=client_data.memo,
        source=client_data.source,
        client_type=client_data.client_type,
        issue_types=client_data.issue_types,
        status=client_data.status or "first_session",
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
        "status": client.status,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": (
            client.anonymized_at.isoformat() if client.anonymized_at else None
        ),
        "session_count": 0,
        "total_payment_amount": 0,
        "total_payment_currency": "TWD",
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }

    return ClientResponse(**client_dict)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Update a client."""
    client = (
        db.query(Client)
        .filter(and_(Client.id == client_id, Client.user_id == current_user.id))
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.is_anonymized:
        raise HTTPException(status_code=403, detail="Cannot edit anonymized client")

    # Check for duplicate email if email is being updated
    if client_data.email and client_data.email != client.email:
        existing = (
            db.query(Client)
            .filter(
                and_(
                    Client.user_id == current_user.id,
                    func.lower(Client.email) == client_data.email.lower(),
                    Client.email.isnot(None),
                    Client.id != client_id,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409, detail="A client with this email already exists"
            )

    # Update fields
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    session_count = (
        db.query(CoachingSession).filter(CoachingSession.client_id == client.id).count()
    )

    # Calculate payment totals (assuming NTD as primary currency for now)
    payment_total = (
        db.query(func.sum(CoachingSession.fee_amount))
        .filter(
            CoachingSession.client_id == client.id,
            CoachingSession.fee_currency == "NTD",
        )
        .scalar()
        or 0
    )

    client_dict = {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "memo": client.memo,
        "source": client.source,
        "client_type": client.client_type,
        "issue_types": client.issue_types,
        "status": client.status,
        "is_anonymized": client.is_anonymized,
        "anonymized_at": (
            client.anonymized_at.isoformat() if client.anonymized_at else None
        ),
        "session_count": session_count,
        "total_payment_amount": payment_total,
        "total_payment_currency": "TWD",
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }

    return ClientResponse(**client_dict)


@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Delete a client (hard delete, only if no sessions)."""
    client = (
        db.query(Client)
        .filter(and_(Client.id == client_id, Client.user_id == current_user.id))
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check if client has any coaching sessions
    session_count = (
        db.query(CoachingSession).filter(CoachingSession.client_id == client.id).count()
    )

    if session_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete client with existing sessions. Use anonymization instead.",
        )

    db.delete(client)
    db.commit()

    return {"message": "Client deleted successfully"}


@router.post("/{client_id}/anonymize")
async def anonymize_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Anonymize a client for GDPR compliance."""
    client = (
        db.query(Client)
        .filter(and_(Client.id == client_id, Client.user_id == current_user.id))
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.is_anonymized:
        raise HTTPException(status_code=409, detail="Client is already anonymized")

    # Get next anonymous number for this coach
    anonymous_count = (
        db.query(Client)
        .filter(and_(Client.user_id == current_user.id, Client.is_anonymized == True))
        .count()
    )

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
        {"value": "referral", "labelKey": "clients.sourceReferral"},
        {"value": "organic", "labelKey": "clients.sourceOrganic"},
        {"value": "friend", "labelKey": "clients.sourceFriend"},
        {"value": "social_media", "labelKey": "clients.sourceSocialMedia"},
    ]


@router.get("/options/types")
async def get_client_types():
    """Get available client type options."""
    return [
        {"value": "paid", "labelKey": "clients.typePaid"},
        {"value": "pro_bono", "labelKey": "clients.typeProBono"},
        {"value": "free_practice", "labelKey": "clients.typeFreePractice"},
        {"value": "other", "labelKey": "clients.typeOther"},
    ]


@router.get("/options/statuses")
async def get_client_statuses():
    """Get available client status options."""
    return [
        {"value": "first_session", "label": "首次會談"},
        {"value": "in_progress", "label": "進行中"},
        {"value": "paused", "label": "暫停"},
        {"value": "completed", "label": "結案"},
    ]
