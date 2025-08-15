"""Transcript and role models."""

import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Float,
    Text,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class SpeakerRole(enum.Enum):
    """Speaker roles in coaching session."""

    COACH = "coach"
    CLIENT = "client"
    UNKNOWN = "unknown"


class TranscriptSegment(BaseModel):
    """Individual transcript segment from Speech-to-Text."""

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

    # Relationships
    session = relationship("Session", back_populates="segments")
    role_assignment = relationship(
        "SegmentRole", back_populates="segment", uselist=False
    )

    def __repr__(self):
        return f"<TranscriptSegment(speaker_id={self.speaker_id}, start={self.start_seconds}s)>"

    @property
    def duration_sec(self) -> float:
        """Get segment duration in seconds."""
        return self.end_seconds - self.start_seconds

    @property
    def formatted_timespan(self) -> str:
        """Get formatted time span (MM:SS - MM:SS)."""

        def format_time(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        return f"{format_time(self.start_seconds)} - {format_time(self.end_seconds)}"

    def get_role_label(self) -> str:
        """Get role label for this segment."""
        # This will be resolved through session.get_speaker_role(speaker_id)
        return f"Speaker {self.speaker_id}"


class SessionRole(BaseModel):
    """Speaker role assignment for a session (speaker-level)."""

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    speaker_id = Column(Integer, nullable=False)  # From STT diarization
    role = Column(Enum(SpeakerRole), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="roles")

    # Ensure unique speaker_id per session
    __table_args__ = (
        UniqueConstraint("session_id", "speaker_id", name="unique_session_speaker"),
    )

    def __repr__(self):
        return f"<SessionRole(speaker_id={self.speaker_id}, role={self.role.value})>"

    @classmethod
    def create_assignment(cls, session_id, speaker_id: int, role: SpeakerRole):
        """Create a new role assignment."""
        return cls(session_id=session_id, speaker_id=speaker_id, role=role)


class SegmentRole(BaseModel):
    """Individual segment role assignment (segment-level)."""

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

    role = Column(Enum(SpeakerRole), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="segment_roles")
    segment = relationship("TranscriptSegment", back_populates="role_assignment")

    # Ensure unique segment_id per session
    __table_args__ = (
        UniqueConstraint(
            "session_id", "segment_id", name="unique_session_segment_role"
        ),
    )

    def __repr__(self):
        return f"<SegmentRole(segment_id={self.segment_id}, role={self.role.value})>"

    @classmethod
    def create_assignment(cls, session_id, segment_id, role: SpeakerRole):
        """Create a new segment role assignment."""
        return cls(session_id=session_id, segment_id=segment_id, role=role)
