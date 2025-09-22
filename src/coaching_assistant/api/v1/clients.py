"""Client management API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...infrastructure.factories import ClientServiceFactory
from ...core.database import get_db
from ...core.models.user import User
from ...core.services.client_management_use_case import (
    ClientRetrievalUseCase,
    ClientCreationUseCase,
    ClientUpdateUseCase,
    ClientDeletionUseCase,
    ClientOptionsUseCase
)
from .auth import get_current_user_dependency

router = APIRouter()


# Dependency injection factory functions
def get_client_retrieval_use_case(db: Session = Depends(get_db)) -> ClientRetrievalUseCase:
    """Dependency injection for ClientRetrievalUseCase."""
    return ClientServiceFactory.create_client_retrieval_use_case(db)


def get_client_creation_use_case(db: Session = Depends(get_db)) -> ClientCreationUseCase:
    """Dependency injection for ClientCreationUseCase."""
    return ClientServiceFactory.create_client_creation_use_case(db)


def get_client_update_use_case(db: Session = Depends(get_db)) -> ClientUpdateUseCase:
    """Dependency injection for ClientUpdateUseCase."""
    return ClientServiceFactory.create_client_update_use_case(db)


def get_client_deletion_use_case(db: Session = Depends(get_db)) -> ClientDeletionUseCase:
    """Dependency injection for ClientDeletionUseCase."""
    return ClientServiceFactory.create_client_deletion_use_case(db)


def get_client_options_use_case() -> ClientOptionsUseCase:
    """Dependency injection for ClientOptionsUseCase."""
    return ClientServiceFactory.create_client_options_use_case()


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


# Helper function to convert domain model to response model
def _client_to_response(client) -> ClientResponse:
    """Convert domain Client to ClientResponse with temporary session/payment data.

    Args:
        client: Client domain entity

    Returns:
        ClientResponse with session_count and payment_total temporarily set to 0
    """
    return ClientResponse(
        id=client.id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        memo=client.memo,
        source=client.source,
        client_type=client.client_type,
        issue_types=client.issue_types,
        status=client.status,
        is_anonymized=client.is_anonymized,
        anonymized_at=client.anonymized_at.isoformat() if client.anonymized_at else None,
        session_count=0,  # TODO: Implement when CoachingSession repository is available
        total_payment_amount=0,  # TODO: Implement when CoachingSession repository is available
        total_payment_currency="TWD",
        created_at=client.created_at.isoformat(),
        updated_at=client.updated_at.isoformat(),
    )


@router.get("", response_model=ClientListResponse)
async def list_clients(
    query: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    client_retrieval: ClientRetrievalUseCase = Depends(get_client_retrieval_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """List clients for the current user."""
    try:
        clients, total, total_pages = client_retrieval.list_clients_paginated(
            coach_id=current_user.id,
            query=query,
            page=page,
            page_size=page_size
        )

        # Convert domain entities to response models
        client_responses = [_client_to_response(client) for client in clients]

        return ClientListResponse(
            items=client_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


# Statistics endpoints must be before /{client_id} to avoid path conflicts
@router.get("/statistics")
async def get_client_statistics(
    client_retrieval: ClientRetrievalUseCase = Depends(get_client_retrieval_use_case),
    current_user: User = Depends(get_current_user_dependency),
) -> dict:
    """Get client statistics for charts."""
    try:
        print(f"Statistics request from user: {current_user.id}")

        # Use the use case to get client statistics
        result = client_retrieval.get_client_statistics(current_user.id)

        print(f"Returning statistics: {result}")
        return result

    except ValueError as e:
        print(f"ValueError in get_client_statistics: {str(e)}")
        # Return empty distributions on validation errors
        return {
            "source_distribution": [],
            "type_distribution": [],
            "issue_distribution": [],
        }
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
    client_retrieval: ClientRetrievalUseCase = Depends(get_client_retrieval_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """Get a specific client."""
    try:
        client = client_retrieval.get_client_by_id(client_id, current_user.id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return _client_to_response(client)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    client_creation: ClientCreationUseCase = Depends(get_client_creation_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """Create a new client."""
    try:
        client = client_creation.create_client(
            coach_id=current_user.id,
            name=client_data.name,
            email=client_data.email,
            phone=client_data.phone,
            memo=client_data.memo,
            source=client_data.source,
            client_type=client_data.client_type,
            issue_types=client_data.issue_types,
            status=client_data.status or "first_session"
        )

        return _client_to_response(client)

    except ValueError as e:
        if "email already exists" in str(e):
            raise HTTPException(
                status_code=409,
                detail="A client with this email already exists",
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    client_update: ClientUpdateUseCase = Depends(get_client_update_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """Update a client."""
    try:
        # Extract only the set fields from the update data
        update_data = client_data.dict(exclude_unset=True)

        updated_client = client_update.update_client(
            client_id=client_id,
            coach_id=current_user.id,
            name=update_data.get("name"),
            email=update_data.get("email"),
            phone=update_data.get("phone"),
            memo=update_data.get("memo"),
            source=update_data.get("source"),
            client_type=update_data.get("client_type"),
            issue_types=update_data.get("issue_types"),
            status=update_data.get("status")
        )

        return _client_to_response(updated_client)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail="Client not found")
        elif "anonymized" in error_msg:
            raise HTTPException(status_code=403, detail="Cannot edit anonymized client")
        elif "email already exists" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="A client with this email already exists",
            )
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{client_id}")
async def delete_client(
    client_id: UUID,
    client_deletion: ClientDeletionUseCase = Depends(get_client_deletion_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """Delete a client (hard delete, only if no sessions)."""
    try:
        success = client_deletion.delete_client(client_id, current_user.id)

        if success:
            return {"message": "Client deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete client")

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail="Client not found")
        elif "existing sessions" in error_msg:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete client with existing sessions. Use anonymization instead.",
            )
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{client_id}/anonymize")
async def anonymize_client(
    client_id: UUID,
    client_deletion: ClientDeletionUseCase = Depends(get_client_deletion_use_case),
    current_user: User = Depends(get_current_user_dependency),
):
    """Anonymize a client for GDPR compliance."""
    try:
        message = client_deletion.anonymize_client(client_id, current_user.id)
        return {"message": message}

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail="Client not found")
        elif "already anonymized" in error_msg:
            raise HTTPException(
                status_code=409, detail="Client is already anonymized"
            )
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/options/sources")
async def get_client_sources(
    client_options: ClientOptionsUseCase = Depends(get_client_options_use_case),
):
    """Get available client source options."""
    return client_options.get_source_options()


@router.get("/options/types")
async def get_client_types(
    client_options: ClientOptionsUseCase = Depends(get_client_options_use_case),
):
    """Get available client type options."""
    return client_options.get_type_options()


@router.get("/options/statuses")
async def get_client_statuses(
    client_options: ClientOptionsUseCase = Depends(get_client_options_use_case),
):
    """Get available client status options."""
    return client_options.get_status_options()
