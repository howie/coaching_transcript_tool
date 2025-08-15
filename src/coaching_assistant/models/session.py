"""Session model and related enums."""

import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class SessionStatus(enum.Enum):
    """Session processing status."""

    UPLOADING = "uploading"  # User is uploading audio file
    PENDING = "pending"  # Audio uploaded, waiting for processing
    PROCESSING = "processing"  # STT processing in progress
    COMPLETED = "completed"  # Processing completed successfully
    FAILED = "failed"  # Processing failed
    CANCELLED = "cancelled"  # User cancelled the session


class Session(BaseModel):
    """Coaching session model."""

    # Basic info
    title = Column(String(255), nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Audio file info
    audio_filename = Column(String(255))
    duration_seconds = Column(Integer)  # Actual duration from STT
    language = Column(
        String(20), default="auto"
    )  # Language code (cmn-Hant-TW, cmn-Hans-CN, en-US, auto)

    # Processing status
    status = Column(
        Enum(SessionStatus), default=SessionStatus.UPLOADING, nullable=False
    )

    # Google Cloud Storage
    gcs_audio_path = Column(String(512))  # gs://bucket/path/to/audio.mp3

    # Google Speech-to-Text
    transcription_job_id = Column(String(255))  # STT operation ID

    # Processing metadata
    error_message = Column(Text)  # Error details if failed
    stt_cost_usd = Column(String(10))  # Cost tracking for analytics

    # STT Provider tracking
    stt_provider = Column(
        String(50), default="google", nullable=False
    )  # 'google' or 'assemblyai'
    provider_metadata = Column(
        JSON, default={}, nullable=False
    )  # Provider-specific metadata

    # Relationships
    user = relationship("User", back_populates="sessions")
    segments = relationship(
        "TranscriptSegment",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="TranscriptSegment.start_seconds",
    )
    roles = relationship(
        "SessionRole", back_populates="session", cascade="all, delete-orphan"
    )
    segment_roles = relationship(
        "SegmentRole", back_populates="session", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "ProcessingStatus",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ProcessingStatus.created_at",
    )
    usage_logs = relationship(
        "UsageLog",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Session(title={self.title}, status={self.status.value})>"

    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return (self.duration_seconds or 0) / 60.0

    @property
    def is_processing_complete(self) -> bool:
        """Check if processing is complete (success or failure)."""
        return self.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        ]

    @property
    def segments_count(self) -> int:
        """Get number of transcript segments."""
        return self.segments.count()

    def get_speaker_role(self, speaker_id: int) -> str:
        """Get role for a specific speaker ID."""
        for role in self.roles:
            if role.speaker_id == speaker_id:
                return role.role.value
        return f"Speaker {speaker_id}"

    def update_status(self, new_status: SessionStatus, error_message: str = None):
        """Update session status with optional error message."""
        self.status = new_status
        if error_message:
            self.error_message = error_message

    def mark_completed(self, duration_seconds: int, cost_usd: str = None):
        """Mark session as completed with duration and cost."""
        self.status = SessionStatus.COMPLETED
        self.duration_seconds = duration_seconds
        if cost_usd:
            self.stt_cost_usd = cost_usd

    def mark_failed(self, error_message: str):
        """Mark session as failed with error message."""
        self.status = SessionStatus.FAILED
        self.error_message = error_message
