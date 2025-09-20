"""TranscriptSegment, SessionRole, and SegmentRole ORM models with domain conversion."""

from sqlalchemy import Column, Integer, ForeignKey, Float, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional
import uuid

from .base import BaseModel
from ....core.models.transcript import (
    TranscriptSegment,
    SessionRole,
    SegmentRole,
    SpeakerRole,
)


class TranscriptSegmentModel(BaseModel):
    """ORM model for TranscriptSegment entity with SQLAlchemy mappings."""

    __tablename__ = "transcript_segment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Speaker identification (from STT diarization)
    speaker_id = Column(Integer, nullable=False)  # 1, 2, 3...

    # Timing
    start_seconds = Column(Float, nullable=False)
    end_seconds = Column(Float, nullable=False)

    # Content
    content = Column(Text, nullable=False)
    confidence = Column(Float)  # STT confidence score (0.0-1.0)

    # Speaker role assignment (handled via relationship to SegmentRoleModel)
    # speaker_role = Column(
    #     SQLEnum(SpeakerRole, values_callable=lambda x: [e.value for e in x]),
    #     nullable=False,
    #     default=SpeakerRole.UNKNOWN,
    # )

    # Relationships (commented out until Session model is properly set up)
    # session = relationship("SessionModel", back_populates="segments")
    # role_assignment = relationship(
    #     "SegmentRoleModel", back_populates="segment", uselist=False
    # )

    def to_domain(self) -> TranscriptSegment:
        """Convert ORM model to domain model."""
        return TranscriptSegment(
            id=self.id,
            session_id=self.session_id,
            speaker_id=self.speaker_id,
            start_seconds=self.start_seconds,
            end_seconds=self.end_seconds,
            content=self.content,
            confidence=self.confidence,
            speaker_role=SpeakerRole.UNKNOWN,  # Default value, role handled via separate table
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, segment: TranscriptSegment) -> "TranscriptSegmentModel":
        """Create ORM model from domain model."""
        return cls(
            id=segment.id,
            session_id=segment.session_id,
            speaker_id=segment.speaker_id,
            start_seconds=segment.start_seconds,
            end_seconds=segment.end_seconds,
            content=segment.content,
            confidence=segment.confidence,
            # speaker_role handled via separate SegmentRoleModel table
            created_at=segment.created_at,
            updated_at=segment.updated_at,
        )

    def update_from_domain(self, segment: TranscriptSegment) -> None:
        """Update ORM model from domain model."""
        self.speaker_id = segment.speaker_id
        self.start_seconds = segment.start_seconds
        self.end_seconds = segment.end_seconds
        self.content = segment.content
        self.confidence = segment.confidence
        # speaker_role handled via separate SegmentRoleModel table
        self.updated_at = segment.updated_at


class SessionRoleModel(BaseModel):
    """ORM model for SessionRole entity (speaker-level role assignment)."""

    __tablename__ = "session_role"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    speaker_id = Column(Integer, nullable=False)  # From STT diarization
    role = Column(
        SQLEnum(SpeakerRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Relationships (commented out until Session model is properly set up)
    # session = relationship("SessionModel", back_populates="roles")

    # Ensure unique speaker_id per session
    __table_args__ = (
        UniqueConstraint(
            "session_id", "speaker_id", name="unique_session_speaker"
        ),
    )

    def to_domain(self) -> SessionRole:
        """Convert ORM model to domain model."""
        return SessionRole(
            id=self.id,
            session_id=self.session_id,
            speaker_id=self.speaker_id,
            role=self.role,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, session_role: SessionRole) -> "SessionRoleModel":
        """Create ORM model from domain model."""
        return cls(
            id=session_role.id,
            session_id=session_role.session_id,
            speaker_id=session_role.speaker_id,
            role=session_role.role.value,
            created_at=session_role.created_at,
            updated_at=session_role.updated_at,
        )

    def update_from_domain(self, session_role: SessionRole) -> None:
        """Update ORM model from domain model."""
        self.speaker_id = session_role.speaker_id
        self.role = session_role.role.value
        self.updated_at = session_role.updated_at


class SegmentRoleModel(BaseModel):
    """ORM model for SegmentRole entity (segment-level role assignment)."""

    __tablename__ = "segment_role"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    segment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transcript_segment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        SQLEnum(SpeakerRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Relationships (commented out until models are properly set up)
    # session = relationship("SessionModel", back_populates="segment_roles")
    # segment = relationship(
    #     "TranscriptSegmentModel", back_populates="role_assignment"
    # )

    # Ensure unique segment_id per session
    __table_args__ = (
        UniqueConstraint(
            "session_id", "segment_id", name="unique_session_segment_role"
        ),
    )

    def to_domain(self) -> SegmentRole:
        """Convert ORM model to domain model."""
        return SegmentRole(
            id=self.id,
            session_id=self.session_id,
            segment_id=self.segment_id,
            role=self.role,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, segment_role: SegmentRole) -> "SegmentRoleModel":
        """Create ORM model from domain model."""
        return cls(
            id=segment_role.id,
            session_id=segment_role.session_id,
            segment_id=segment_role.segment_id,
            role=segment_role.role.value,
            created_at=segment_role.created_at,
            updated_at=segment_role.updated_at,
        )

    def update_from_domain(self, segment_role: SegmentRole) -> None:
        """Update ORM model from domain model."""
        self.segment_id = segment_role.segment_id
        self.role = segment_role.role.value
        self.updated_at = segment_role.updated_at