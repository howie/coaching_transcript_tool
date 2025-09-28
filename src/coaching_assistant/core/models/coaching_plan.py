"""Coaching plan domain model for Clean Architecture."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class CoachingPlanType(Enum):
    """Types of coaching plans."""

    SINGLE_SESSION = "single_session"
    PACKAGE = "package"
    GROUP = "group"
    WORKSHOP = "workshop"
    CUSTOM = "custom"


@dataclass
class CoachingPlan:
    """Domain model for coaching plans."""

    # Identifiers
    id: Optional[UUID] = None
    coach_profile_id: UUID = None

    # Plan details
    plan_type: str = "single_session"  # Using string for flexibility
    title: str = ""
    description: Optional[str] = None

    # Pricing
    duration_minutes: Optional[int] = None
    number_of_sessions: int = 1
    price: float = 0.0
    currency: str = "NTD"

    # Availability
    is_active: bool = True
    max_participants: int = 1

    # Additional settings
    booking_notice_hours: int = 24
    cancellation_notice_hours: int = 24

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def price_per_session(self) -> float:
        """Calculate price per session."""
        if self.number_of_sessions and self.number_of_sessions > 0:
            return self.price / self.number_of_sessions
        return self.price

    @property
    def total_duration_minutes(self) -> int:
        """Calculate total duration for package."""
        if (
            self.duration_minutes
            and self.number_of_sessions
            and self.number_of_sessions > 0
        ):
            return self.duration_minutes * self.number_of_sessions
        elif self.number_of_sessions == 0:
            return 0  # No sessions = no total duration
        return self.duration_minutes or 0

    def __repr__(self):
        return f"<CoachingPlan(title={self.title}, type={self.plan_type}, price={self.price})>"
