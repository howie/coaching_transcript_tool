"""Coaching session domain model for Clean Architecture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class SessionSource(Enum):
    """Source of coaching session."""

    CLIENT = "CLIENT"
    FRIEND = "FRIEND"
    CLASSMATE = "CLASSMATE"
    SUBORDINATE = "SUBORDINATE"


@dataclass
class CoachingSession:
    """Domain model for coaching sessions."""

    # Identifiers
    id: Optional[UUID] = None
    user_id: UUID = None  # Coach user ID
    client_id: UUID = None

    # Basic info
    session_date: date = None
    source: SessionSource = None

    # Duration and fee
    duration_min: int = 0
    fee_currency: str = "TWD"
    fee_amount: int = 0

    # File associations
    transcription_session_id: Optional[UUID] = None

    # Notes
    notes: Optional[str] = None

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def fee_display(self) -> str:
        """Get formatted fee for display."""
        return f"{self.fee_currency} {self.fee_amount}"

    @property
    def duration_display(self) -> str:
        """Get formatted duration for display."""
        return f"{self.duration_min} 分鐘"

    def validate(self) -> bool:
        """Validate business rules."""
        return (
            self.duration_min > 0
            and self.fee_amount >= 0
            and self.user_id is not None
            and self.client_id is not None
            and self.session_date is not None
        )

    def __repr__(self):
        return (
            f"<CoachingSession(date={self.session_date}, "
            f"client_id={self.client_id}, duration={self.duration_min}min)>"
        )
