"""Transcript domain model with validation logic."""

import enum
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID


class SpeakerRole(enum.Enum):
    """Speaker roles in coaching session."""

    COACH = "COACH"
    CLIENT = "CLIENT"
    UNKNOWN = "UNKNOWN"


@dataclass
class TranscriptSegment:
    """Pure domain model for TranscriptSegment entity with validation logic."""

    # Core identity
    id: Optional[UUID] = None
    session_id: Optional[UUID] = None

    # Speaker identification (from STT diarization)
    speaker_id: int = 1  # 1, 2, 3...

    # Timing
    start_seconds: float = 0.0
    end_seconds: float = 0.0

    # Content
    content: str = ""
    confidence: Optional[float] = None  # STT confidence score (0.0-1.0)

    # Speaker role assignment
    speaker_role: SpeakerRole = SpeakerRole.UNKNOWN

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate segment data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the transcript segment data."""
        if self.start_seconds < 0:
            raise ValueError("start_seconds must be non-negative")

        if self.end_seconds < 0:
            raise ValueError("end_seconds must be non-negative")

        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")

        if self.speaker_id < 1:
            raise ValueError("speaker_id must be positive")

        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not self.content.strip():
            raise ValueError("content cannot be empty")

    def get_duration_seconds(self) -> float:
        """Get duration of this segment in seconds."""
        return self.end_seconds - self.start_seconds

    def get_word_count(self) -> int:
        """Get word count for this segment."""
        return len(self.content.split())

    def get_confidence_percentage(self) -> Optional[int]:
        """Get confidence as percentage (0-100)."""
        if self.confidence is None:
            return None
        return int(self.confidence * 100)

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if this segment has high confidence."""
        if self.confidence is None:
            return False
        return self.confidence >= threshold

    def is_coach_speaking(self) -> bool:
        """Check if the coach is speaking in this segment."""
        return self.speaker_role == SpeakerRole.COACH

    def is_client_speaking(self) -> bool:
        """Check if the client is speaking in this segment."""
        return self.speaker_role == SpeakerRole.CLIENT

    def assign_speaker_role(self, role: SpeakerRole) -> None:
        """Assign speaker role to this segment."""
        if not isinstance(role, SpeakerRole):
            raise ValueError("role must be a SpeakerRole enum value")
        self.speaker_role = role

    def format_timestamp(self) -> str:
        """Format timestamp as MM:SS or HH:MM:SS."""
        start_minutes = int(self.start_seconds // 60)
        start_seconds = int(self.start_seconds % 60)

        end_minutes = int(self.end_seconds // 60)
        end_seconds = int(self.end_seconds % 60)

        if start_minutes >= 60:
            start_hours = start_minutes // 60
            start_minutes = start_minutes % 60
            end_hours = end_minutes // 60
            end_minutes = end_minutes % 60
            return f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d} → {end_hours:02d}:{end_minutes:02d}:{end_seconds:02d}"
        else:
            return f"{start_minutes:02d}:{start_seconds:02d} → {end_minutes:02d}:{end_seconds:02d}"

    def __str__(self) -> str:
        """String representation of the segment."""
        role_indicator = ""
        if self.speaker_role == SpeakerRole.COACH:
            role_indicator = "[教練] "
        elif self.speaker_role == SpeakerRole.CLIENT:
            role_indicator = "[客戶] "

        return f"{self.format_timestamp()} {role_indicator}{self.content}"


@dataclass
class SessionRole:
    """Pure domain model for SessionRole entity (speaker-level role assignment)."""

    # Core identity
    id: Optional[UUID] = None
    session_id: Optional[UUID] = None

    # Speaker role assignment
    speaker_id: int = 1  # From STT diarization
    role: SpeakerRole = SpeakerRole.UNKNOWN

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.id is None:
            from uuid import uuid4

            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)

    def validate(self) -> None:
        """Validate the session role data."""
        if self.speaker_id < 1:
            raise ValueError("speaker_id must be positive")

        if not isinstance(self.role, SpeakerRole):
            raise ValueError("role must be a SpeakerRole enum value")

        if self.session_id is None:
            raise ValueError("session_id cannot be None")

    def assign_role(self, new_role: SpeakerRole) -> None:
        """Business rule: Assign new role to speaker."""
        if not isinstance(new_role, SpeakerRole):
            raise ValueError("role must be a SpeakerRole enum value")

        self.role = new_role
        self.updated_at = datetime.now(UTC)

    def is_coach_role(self) -> bool:
        """Check if this is assigned to coach role."""
        return self.role == SpeakerRole.COACH

    def is_client_role(self) -> bool:
        """Check if this is assigned to client role."""
        return self.role == SpeakerRole.CLIENT


@dataclass
class SegmentRole:
    """Pure domain model for SegmentRole entity (segment-level role assignment)."""

    # Core identity
    id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    segment_id: Optional[UUID] = None

    # Role assignment
    role: SpeakerRole = SpeakerRole.UNKNOWN

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.id is None:
            from uuid import uuid4

            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)

    def validate(self) -> None:
        """Validate the segment role data."""
        if not isinstance(self.role, SpeakerRole):
            raise ValueError("role must be a SpeakerRole enum value")

        if self.session_id is None:
            raise ValueError("session_id cannot be None")

        if self.segment_id is None:
            raise ValueError("segment_id cannot be None")

    def assign_role(self, new_role: SpeakerRole) -> None:
        """Business rule: Assign new role to segment."""
        if not isinstance(new_role, SpeakerRole):
            raise ValueError("role must be a SpeakerRole enum value")

        self.role = new_role
        self.updated_at = datetime.now(UTC)

    def is_coach_speaking(self) -> bool:
        """Check if this segment is coach speaking."""
        return self.role == SpeakerRole.COACH

    def is_client_speaking(self) -> bool:
        """Check if this segment is client speaking."""
        return self.role == SpeakerRole.CLIENT
