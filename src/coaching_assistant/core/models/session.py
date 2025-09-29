"""Session domain model with validation logic."""

import enum
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4


class SessionStatus(enum.Enum):
    """Session processing status."""

    UPLOADING = "uploading"  # User is uploading audio file
    PENDING = "pending"  # Audio uploaded, waiting for processing
    PROCESSING = "processing"  # STT processing in progress
    COMPLETED = "completed"  # Processing completed successfully
    FAILED = "failed"  # Processing failed
    CANCELLED = "cancelled"  # User cancelled the session


@dataclass
class Session:
    """Pure domain model for Session entity with validation logic."""

    # Core identity
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    # Basic info
    title: str = ""
    language: str = "auto"

    # Audio file info
    audio_filename: Optional[str] = None
    duration_seconds: Optional[int] = None

    # Processing status
    status: SessionStatus = SessionStatus.UPLOADING
    error_message: Optional[str] = None
    progress_percentage: int = 0

    # Cloud storage paths
    gcs_audio_path: Optional[str] = None
    gcs_transcript_path: Optional[str] = None

    # STT provider info
    stt_provider: Optional[str] = None
    transcription_job_id: Optional[str] = None
    assemblyai_transcript_id: Optional[str] = None

    # Results
    transcript_text: Optional[str] = None
    speaker_count: Optional[int] = None
    confidence_score: Optional[float] = None
    segments_count: int = 0

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    transcription_started_at: Optional[datetime] = None
    transcription_completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)

    # Business Rules & Validation

    def can_upload_audio(self) -> bool:
        """Business rule: Check if session can accept audio upload."""
        return self.status in [SessionStatus.UPLOADING, SessionStatus.FAILED]

    def can_start_transcription(self) -> bool:
        """Business rule: Check if session can start transcription."""
        return (
            self.status in [SessionStatus.PENDING, SessionStatus.UPLOADING]
            and self.gcs_audio_path is not None
            and self.audio_filename is not None
        )

    def can_retry_transcription(self) -> bool:
        """Business rule: Check if transcription can be retried."""
        return self.status == SessionStatus.FAILED

    def is_processing_complete(self) -> bool:
        """Business rule: Check if processing is complete."""
        return self.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        ]

    def is_transcript_available(self) -> bool:
        """Business rule: Check if transcript is available."""
        return (
            self.status == SessionStatus.COMPLETED
            and self.transcript_text is not None
            and len(self.transcript_text.strip()) > 0
        )

    def validate_title(self, title: str) -> None:
        """Business rule: Validate session title."""
        if not title or not title.strip():
            raise ValueError("Session title cannot be empty")
        if len(title) > 255:
            raise ValueError("Session title cannot exceed 255 characters")

    def validate_language(self, language: str) -> None:
        """Business rule: Validate language code."""
        valid_languages = [
            "auto",
            "en-US",
            "en-GB",
            "en-AU",
            "cmn-Hant-TW",
            "cmn-Hans-CN",
            "ja-JP",
            "ko-KR",
            "th-TH",
            "vi-VN",
            "ms-MY",
            "id-ID",
        ]
        if language not in valid_languages:
            raise ValueError(f"Unsupported language: {language}")

    def validate_stt_provider(self, provider: str) -> None:
        """Business rule: Validate STT provider."""
        valid_providers = ["google", "assemblyai", "auto"]
        if provider not in valid_providers:
            raise ValueError(f"Unsupported STT provider: {provider}")

    # State Transitions

    def mark_audio_uploaded(self, gcs_path: str, filename: str) -> None:
        """Business rule: Mark audio as uploaded."""
        if not self.can_upload_audio():
            raise ValueError(f"Cannot upload audio in status: {self.status.value}")

        self.gcs_audio_path = gcs_path
        self.audio_filename = filename
        self.status = SessionStatus.PENDING
        self.error_message = None
        self.updated_at = datetime.now(UTC)

    def start_transcription(self, job_id: Optional[str] = None) -> None:
        """Business rule: Start transcription process."""
        if not self.can_start_transcription():
            raise ValueError(
                f"Cannot start transcription in status: {self.status.value}"
            )

        self.status = SessionStatus.PROCESSING
        self.transcription_job_id = job_id
        self.transcription_started_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.progress_percentage = 0

    def complete_transcription(
        self,
        transcript_text: str,
        duration_seconds: int,
        speaker_count: Optional[int] = None,
        confidence_score: Optional[float] = None,
        gcs_transcript_path: Optional[str] = None,
    ) -> None:
        """Business rule: Complete transcription with results."""
        if self.status != SessionStatus.PROCESSING:
            raise ValueError(
                f"Cannot complete transcription in status: {self.status.value}"
            )

        if not transcript_text or not transcript_text.strip():
            raise ValueError("Transcript text cannot be empty")

        if duration_seconds <= 0:
            raise ValueError("Duration must be positive")

        self.transcript_text = transcript_text.strip()
        self.duration_seconds = duration_seconds
        self.speaker_count = speaker_count
        self.confidence_score = confidence_score
        self.gcs_transcript_path = gcs_transcript_path
        self.status = SessionStatus.COMPLETED
        self.progress_percentage = 100
        self.transcription_completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def fail_transcription(self, error_message: str) -> None:
        """Business rule: Mark transcription as failed."""
        if self.status != SessionStatus.PROCESSING:
            raise ValueError(
                f"Cannot fail transcription in status: {self.status.value}"
            )

        if not error_message:
            raise ValueError("Error message cannot be empty")

        self.status = SessionStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(UTC)

    def cancel_session(self) -> None:
        """Business rule: Cancel session."""
        if self.is_processing_complete():
            raise ValueError(f"Cannot cancel session in status: {self.status.value}")

        self.status = SessionStatus.CANCELLED
        self.updated_at = datetime.now(UTC)

    def retry_transcription(self) -> None:
        """Business rule: Retry failed transcription."""
        if not self.can_retry_transcription():
            raise ValueError(
                f"Cannot retry transcription in status: {self.status.value}"
            )

        self.status = SessionStatus.PENDING
        self.error_message = None
        self.progress_percentage = 0
        self.transcription_job_id = None
        self.assemblyai_transcript_id = None
        self.updated_at = datetime.now(UTC)

    def update_progress(self, percentage: int) -> None:
        """Business rule: Update processing progress."""
        if self.status != SessionStatus.PROCESSING:
            raise ValueError(f"Cannot update progress in status: {self.status.value}")

        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")

        self.progress_percentage = percentage
        self.updated_at = datetime.now(UTC)

    # Calculations & Derived Properties

    def get_processing_duration(self) -> Optional[int]:
        """Business rule: Calculate processing duration in seconds."""
        if not self.transcription_started_at:
            return None

        end_time = self.transcription_completed_at or datetime.now(UTC)
        delta = end_time - self.transcription_started_at
        return int(delta.total_seconds())

    def get_audio_duration_minutes(self) -> float:
        """Business rule: Get audio duration in minutes."""
        if not self.duration_seconds:
            return 0.0
        return self.duration_seconds / 60.0

    def is_long_audio(self, threshold_minutes: int = 60) -> bool:
        """Business rule: Check if audio is considered long."""
        return self.get_audio_duration_minutes() > threshold_minutes

    def get_estimated_processing_time(self) -> int:
        """Business rule: Estimate processing time based on audio duration."""
        if not self.duration_seconds:
            return 60  # Default 1 minute

        # Rough estimate: 1 second of audio = 2-3 seconds processing time
        base_time = self.duration_seconds * 2.5

        # Add overhead based on STT provider
        if self.stt_provider == "assemblyai":
            base_time *= 1.2  # AssemblyAI tends to be slightly slower

        # Minimum 30 seconds, maximum 10 minutes
        return max(30, min(600, int(base_time)))

    def calculate_cost_estimate(self) -> float:
        """Business rule: Calculate estimated cost for transcription."""
        if not self.duration_seconds:
            return 0.0

        # Cost per minute varies by provider and duration
        self.get_audio_duration_minutes()

        if self.stt_provider == "assemblyai":
            # AssemblyAI pricing: roughly $0.00025 per second
            return self.duration_seconds * 0.00025
        else:
            # Google STT pricing: roughly $0.006 per 15 seconds
            return (self.duration_seconds / 15) * 0.006

    def is_ready_for_export(self) -> bool:
        """Business rule: Check if session is ready for export."""
        return (
            self.status == SessionStatus.COMPLETED
            and self.transcript_text is not None
            and len(self.transcript_text.strip()) > 0
        )
