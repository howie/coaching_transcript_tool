"""Client domain model for Clean Architecture."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Client:
    """Domain model for coaching clients."""

    # Identifiers
    id: Optional[UUID] = None
    user_id: UUID = None

    # Basic info
    name: str = None
    email: Optional[str] = None
    phone: Optional[str] = None
    memo: Optional[str] = None

    # Client details
    source: Optional[str] = None  # referral, organic, friend, social_media
    client_type: Optional[str] = None  # paid, pro_bono, free_practice, other
    issue_types: Optional[str] = None  # Comma-separated list
    status: str = "first_session"  # completed, in_progress, paused, first_session

    # GDPR / Anonymization
    is_anonymized: bool = False
    anonymized_at: Optional[datetime] = None

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def can_be_deleted(self) -> bool:
        """Check if client can be deleted (business logic)."""
        # This would be implemented with repository to check sessions
        return True  # Placeholder - actual logic in use case

    def anonymize(self, anonymous_number: int) -> None:
        """Anonymize client data for GDPR compliance."""
        self.name = f"已刪除客戶 {anonymous_number}"
        self.email = None
        self.phone = None
        self.memo = None
        self.is_anonymized = True
        self.anonymized_at = datetime.utcnow()

    def __repr__(self):
        return f"<Client(name={self.name}, user_id={self.user_id})>"