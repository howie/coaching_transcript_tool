"""SessionModel ORM with domain model conversion."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ....core.config import settings
from ....core.models.session import Session, SessionStatus
from .base import BaseModel


class SessionModel(BaseModel):
    """ORM model for Session entity with SQLAlchemy mappings."""

    __tablename__ = "session"

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
    error_message = Column(Text)
    progress_percentage = Column(Integer, default=0)

    # Cloud storage paths
    gcs_audio_path = Column(String(512))  # gs://bucket/path/to/audio.mp3
    gcs_transcript_path = Column(String(512))  # gs://bucket/path/to/transcript.json

    # STT provider info
    stt_provider = Column(String(50), default="google")
    transcription_job_id = Column(String(255))  # STT operation ID
    assemblyai_transcript_id = Column(String(255))  # AssemblyAI transcript ID

    # Results
    transcript_text = Column(Text)
    speaker_count = Column(Integer)
    confidence_score = Column(Float)

    # Processing timestamps
    transcription_started_at = Column(DateTime)
    transcription_completed_at = Column(DateTime)

    # Legacy fields (maintain compatibility)
    wav_path = Column(String(512))  # Legacy audio path
    initial_transcript = Column(Text)  # Legacy transcript field
    final_transcript = Column(Text)  # Legacy final transcript
    processing_status = Column(String(50))  # Legacy status field

    # Processing metadata
    processing_metadata = Column(JSON)  # Store processing details as JSON

    # ORM relationships (using string references to avoid circular imports)
    user = relationship("UserModel", back_populates="sessions")
    usage_logs = relationship(
        "UsageLogModel", back_populates="session", cascade="all, delete-orphan"
    )
    # Legacy relationships - will be migrated later
    # transcript_segments = relationship("TranscriptSegment", back_populates="session", cascade="all, delete-orphan")

    def to_domain(self) -> Session:
        """Convert ORM model to domain model."""
        return Session(
            id=PyUUID(str(self.id)) if self.id else None,
            user_id=PyUUID(str(self.user_id)) if self.user_id else None,
            title=self.title or "",
            language=self.language or "auto",
            audio_filename=self.audio_filename,
            duration_seconds=self.duration_seconds,
            status=self.status or SessionStatus.UPLOADING,
            error_message=self.error_message,
            progress_percentage=self.progress_percentage or 0,
            gcs_audio_path=self.gcs_audio_path,
            gcs_transcript_path=self.gcs_transcript_path,
            stt_provider=(
                (self.stt_provider or "").strip().lower() or settings.STT_PROVIDER
            ),
            transcription_job_id=self.transcription_job_id,
            assemblyai_transcript_id=self.assemblyai_transcript_id,
            transcript_text=self.transcript_text,
            speaker_count=self.speaker_count,
            confidence_score=self.confidence_score,
            created_at=self.created_at,
            updated_at=self.updated_at,
            transcription_started_at=self.transcription_started_at,
            transcription_completed_at=self.transcription_completed_at,
        )

    @classmethod
    def from_domain(cls, session: Session) -> "SessionModel":
        """Convert domain model to ORM model."""
        return cls(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            language=session.language,
            audio_filename=session.audio_filename,
            duration_seconds=session.duration_seconds,
            status=session.status,
            error_message=session.error_message,
            progress_percentage=session.progress_percentage,
            gcs_audio_path=session.gcs_audio_path,
            gcs_transcript_path=session.gcs_transcript_path,
            stt_provider=session.stt_provider,
            transcription_job_id=session.transcription_job_id,
            assemblyai_transcript_id=session.assemblyai_transcript_id,
            transcript_text=session.transcript_text,
            speaker_count=session.speaker_count,
            confidence_score=session.confidence_score,
            created_at=session.created_at,
            updated_at=session.updated_at,
            transcription_started_at=session.transcription_started_at,
            transcription_completed_at=session.transcription_completed_at,
        )

    def update_from_domain(self, session: Session) -> None:
        """Update ORM model fields from domain model."""
        self.title = session.title
        self.language = session.language
        self.audio_filename = session.audio_filename
        self.duration_seconds = session.duration_seconds
        self.status = session.status
        self.error_message = session.error_message
        self.progress_percentage = session.progress_percentage
        self.gcs_audio_path = session.gcs_audio_path
        self.gcs_transcript_path = session.gcs_transcript_path
        self.stt_provider = session.stt_provider
        self.transcription_job_id = session.transcription_job_id
        self.assemblyai_transcript_id = session.assemblyai_transcript_id
        self.transcript_text = session.transcript_text
        self.speaker_count = session.speaker_count
        self.confidence_score = session.confidence_score
        self.transcription_started_at = session.transcription_started_at
        self.transcription_completed_at = session.transcription_completed_at
        self.updated_at = session.updated_at or datetime.now(UTC)

    # Database-specific helper methods

    def get_usage_logs_count(self) -> int:
        """Get total number of usage logs for this session."""
        return len(self.usage_logs) if self.usage_logs else 0

    def get_total_processing_time(self) -> Optional[int]:
        """Calculate total processing time in seconds."""
        if not self.transcription_started_at:
            return None

        end_time = self.transcription_completed_at or datetime.now(UTC)
        delta = end_time - self.transcription_started_at
        return int(delta.total_seconds())

    def get_transcript_segments_count(self) -> int:
        """Get number of transcript segments."""
        return len(self.transcript_segments) if self.transcript_segments else 0

    def has_transcript_segments(self) -> bool:
        """Check if session has any transcript segments."""
        return self.get_transcript_segments_count() > 0

    def get_transcript_word_count(self) -> Optional[int]:
        """Get word count from transcript text."""
        if not self.transcript_text:
            return None
        return len(self.transcript_text.split())

    def get_transcript_character_count(self) -> Optional[int]:
        """Get character count from transcript text."""
        if not self.transcript_text:
            return None
        return len(self.transcript_text)

    def is_processing_complete(self) -> bool:
        """Check if processing is complete."""
        return self.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        ]

    def is_ready_for_export(self) -> bool:
        """Check if session is ready for export."""
        return (
            self.status == SessionStatus.COMPLETED
            and self.transcript_text is not None
            and len(self.transcript_text.strip()) > 0
        )

    def is_long_audio(self, threshold_minutes: int = 60) -> bool:
        """Check if audio is considered long."""
        if not self.duration_seconds:
            return False
        return (self.duration_seconds / 60) > threshold_minutes

    def get_audio_duration_minutes(self) -> float:
        """Get audio duration in minutes."""
        if not self.duration_seconds:
            return 0.0
        return self.duration_seconds / 60.0

    def get_processing_efficiency_score(self) -> Optional[float]:
        """Calculate processing efficiency score."""
        processing_time = self.get_total_processing_time()
        if not processing_time or not self.duration_seconds:
            return None

        # Efficiency = actual duration / processing time
        efficiency = self.duration_seconds / processing_time
        return min(100.0, efficiency * 100)

    def get_quality_metrics(self) -> dict:
        """Get comprehensive quality metrics."""
        metrics = {
            "confidence_score": self.confidence_score,
            "speaker_count": self.speaker_count,
            "word_count": self.get_transcript_word_count(),
            "character_count": self.get_transcript_character_count(),
            "processing_time_seconds": self.get_total_processing_time(),
            "efficiency_score": self.get_processing_efficiency_score(),
            "has_segments": self.has_transcript_segments(),
            "segments_count": self.get_transcript_segments_count(),
        }
        return {k: v for k, v in metrics.items() if v is not None}

    def update_progress(self, percentage: int) -> None:
        """Update processing progress."""
        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")

        self.progress_percentage = percentage
        self.updated_at = datetime.now(UTC)

    def mark_processing_started(self, job_id: Optional[str] = None) -> None:
        """Mark transcription as started."""
        self.status = SessionStatus.PROCESSING
        self.transcription_job_id = job_id
        self.transcription_started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.progress_percentage = 0

    def mark_processing_completed(
        self,
        transcript_text: str,
        duration_seconds: int,
        speaker_count: Optional[int] = None,
        confidence_score: Optional[float] = None,
    ) -> None:
        """Mark transcription as completed."""
        self.status = SessionStatus.COMPLETED
        self.transcript_text = transcript_text
        self.duration_seconds = duration_seconds
        self.speaker_count = speaker_count
        self.confidence_score = confidence_score
        self.progress_percentage = 100
        self.transcription_completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_processing_failed(self, error_message: str) -> None:
        """Mark transcription as failed."""
        self.status = SessionStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(UTC)

    def add_processing_metadata(self, key: str, value: any) -> None:
        """Add metadata entry for processing details."""
        if self.processing_metadata is None:
            self.processing_metadata = {}

        self.processing_metadata[key] = value
        self.updated_at = datetime.now(UTC)

    def get_legacy_status(self) -> str:
        """Get status in legacy format for backward compatibility."""
        status_mapping = {
            SessionStatus.UPLOADING: "uploading",
            SessionStatus.PENDING: "pending",
            SessionStatus.PROCESSING: "processing",
            SessionStatus.COMPLETED: "completed",
            SessionStatus.FAILED: "failed",
            SessionStatus.CANCELLED: "cancelled",
        }
        return status_mapping.get(self.status, "unknown")

    def __repr__(self):
        """String representation of the SessionModel."""
        return (
            f"<SessionModel(id={self.id}, title='{self.title}', "
            f"status={self.status.value if self.status else 'None'}, "
            f"duration={self.duration_seconds}s)>"
        )
