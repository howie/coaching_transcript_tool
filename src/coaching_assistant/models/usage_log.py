"""Usage log model for tracking individual transcription events."""

import enum
from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DECIMAL,
    Text,
    DateTime,
    Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from .base import BaseModel


class TranscriptionType(enum.Enum):
    """Type of transcription for billing classification."""
    
    ORIGINAL = "original"
    RETRY_FAILED = "retry_failed"  # Free retry after failure
    RETRY_SUCCESS = "retry_success"  # Paid re-transcription
    EXPORT = "export"  # Export-related processing
    MANUAL = "manual"  # Manual transcription entry


class UsageLog(BaseModel):
    """Usage log for individual transcription events."""
    
    __tablename__ = "usage_logs"
    
    # User and session references
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("client.id", ondelete="SET NULL"), nullable=True)
    
    # Usage details
    duration_minutes = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    cost_usd = Column(DECIMAL(10, 6), nullable=True)
    stt_provider = Column(String(50), nullable=False)
    
    # Billing classification
    transcription_type = Column(
        Enum(TranscriptionType),
        default=TranscriptionType.ORIGINAL,
        nullable=False
    )
    is_billable = Column(Boolean, default=True, nullable=False)
    billing_reason = Column(String(100), nullable=True)
    parent_log_id = Column(UUID(as_uuid=True), ForeignKey("usage_logs.id"), nullable=True)
    
    # Plan context (snapshot for historical accuracy)
    user_plan = Column(String(20), nullable=False)
    plan_limits = Column(JSON, default={}, nullable=False)
    
    # Timestamps
    transcription_started_at = Column(DateTime(timezone=True), nullable=True)
    transcription_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session context
    language = Column(String(20), nullable=True)
    enable_diarization = Column(Boolean, nullable=True)
    original_filename = Column(String(255), nullable=True)
    audio_file_size_mb = Column(DECIMAL(8, 2), nullable=True)
    
    # Provider metadata
    provider_metadata = Column(JSON, default={}, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    session = relationship("Session", back_populates="usage_logs")
    client = relationship("Client", back_populates="usage_logs")
    parent_log = relationship("UsageLog", remote_side="UsageLog.id", backref="child_logs")
    
    def __repr__(self):
        return (
            f"<UsageLog(id={self.id}, user_id={self.user_id}, "
            f"session_id={self.session_id}, duration_minutes={self.duration_minutes}, "
            f"is_billable={self.is_billable})>"
        )
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration_minutes / 60.0
    
    @property
    def cost_cents(self) -> int:
        """Get cost in cents."""
        if self.cost_usd:
            return int(float(self.cost_usd) * 100)
        return 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_id": str(self.session_id),
            "client_id": str(self.client_id) if self.client_id else None,
            "duration_minutes": self.duration_minutes,
            "duration_seconds": self.duration_seconds,
            "cost_usd": float(self.cost_usd) if self.cost_usd else 0.0,
            "stt_provider": self.stt_provider,
            "transcription_type": self.transcription_type.value,
            "is_billable": self.is_billable,
            "billing_reason": self.billing_reason,
            "user_plan": self.user_plan,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "transcription_completed_at": (
                self.transcription_completed_at.isoformat()
                if self.transcription_completed_at else None
            )
        }