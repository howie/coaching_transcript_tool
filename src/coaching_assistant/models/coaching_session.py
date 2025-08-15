"""Coaching session model."""

import enum
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, Date, CheckConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class SessionSource(enum.Enum):
    """Source of coaching session."""
    CLIENT = "CLIENT"
    FRIEND = "FRIEND"
    CLASSMATE = "CLASSMATE"
    SUBORDINATE = "SUBORDINATE"


class CoachingSession(BaseModel):
    """Coaching session model."""

    # Basic info
    user_id = Column(  # References the user (coach) who created this session
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_date = Column(Date, nullable=False)
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source = Column(Enum(SessionSource), nullable=False)

    # Duration and fee
    duration_min = Column(Integer, nullable=False)
    fee_currency = Column(String(3), nullable=False, default="TWD")
    fee_amount = Column(Integer, nullable=False, default=0)

    # File associations (optional)
    transcription_session_id = Column(UUID(as_uuid=True), nullable=True)  # References session.id for linked transcription

    # Notes
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint('duration_min > 0', name='duration_positive'),
        CheckConstraint('fee_amount >= 0', name='fee_non_negative'),
    )

    # Relationships
    user = relationship("User", back_populates="coaching_sessions")
    client = relationship("Client", back_populates="coaching_sessions")

    def __repr__(self):
        return (
            f"<CoachingSession(date={self.session_date}, "
            f"client_id={self.client_id}, duration={self.duration_min}min)>"
        )

    @property
    def fee_display(self) -> str:
        """Get formatted fee for display."""
        return f"{self.fee_currency} {self.fee_amount}"

    @property
    def duration_display(self) -> str:
        """Get formatted duration for display."""
        return f"{self.duration_min} 分鐘"
