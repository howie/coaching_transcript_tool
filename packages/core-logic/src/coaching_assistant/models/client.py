"""Client model for coaching sessions."""

from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Client(BaseModel):
    """Client model for coaching sessions."""
    
    # Basic info
    coach_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    memo = Column(Text, nullable=True)
    
    # Client details
    source = Column(String(50), nullable=True)  # referral, organic, friend, social_media
    client_type = Column(String(50), nullable=True)  # paid, pro_bono, free_practice, other
    issue_types = Column(Text, nullable=True)  # Comma-separated list of issue types
    client_status = Column(String(50), nullable=False, default='first_session')  # completed, in_progress, paused, first_session
    
    # GDPR / Anonymization
    is_anonymized = Column(Boolean, nullable=False, default=False)
    anonymized_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    coach = relationship("User", back_populates="clients")
    coaching_sessions = relationship(
        "CoachingSession", 
        back_populates="client", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Client(name={self.name}, coach_id={self.coach_id})>"
    
    @property
    def session_count(self) -> int:
        """Get number of coaching sessions for this client."""
        return self.coaching_sessions.count()
    
    def can_be_deleted(self) -> bool:
        """Check if client can be deleted (no associated sessions)."""
        return self.session_count == 0
    
    def anonymize(self, anonymous_number: int):
        """Anonymize client data for GDPR compliance."""
        self.name = f"已刪除客戶 {anonymous_number}"
        self.email = None
        self.phone = None
        self.memo = None
        self.is_anonymized = True
        from datetime import datetime
        self.anonymized_at = datetime.utcnow()