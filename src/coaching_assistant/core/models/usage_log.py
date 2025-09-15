"""UsageLog domain model with calculation methods."""

import enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from .user import User
from .session import Session


class TranscriptionType(enum.Enum):
    """Type of transcription for billing classification."""

    ORIGINAL = "original"
    RETRY_FAILED = "retry_failed"  # Free retry after failure
    RETRY_SUCCESS = "retry_success"  # Paid re-transcription
    EXPORT = "export"  # Export-related processing
    MANUAL = "manual"  # Manual transcription entry


@dataclass
class UsageLog:
    """Pure domain model for UsageLog entity with calculation methods."""

    # Core identity
    id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

    # Usage metrics
    duration_minutes: int = 0
    transcription_type: TranscriptionType = TranscriptionType.ORIGINAL

    # Billing information
    billable: bool = True
    cost_cents: int = 0  # Cost in cents for precise calculation
    currency: str = "TWD"

    # Processing details
    stt_provider: str = "google"
    processing_time_seconds: Optional[int] = None
    confidence_score: Optional[float] = None

    # Quality metrics
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    speaker_count: Optional[int] = None

    # Error tracking
    error_occurred: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0

    # Metadata
    metadata: Optional[dict] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    # Factory Methods

    @classmethod
    def create_for_session(
        cls,
        session: Session,
        user: User,
        transcription_type: TranscriptionType = TranscriptionType.ORIGINAL,
    ) -> "UsageLog":
        """Factory method: Create usage log for a session."""
        if not session.duration_seconds:
            raise ValueError("Session must have duration to create usage log")

        if not session.user_id or session.user_id != user.id:
            raise ValueError("Session user_id must match user")

        duration_minutes = max(1, int(session.duration_seconds / 60))  # Round up to nearest minute

        usage_log = cls(
            session_id=session.id,
            user_id=user.id,
            duration_minutes=duration_minutes,
            transcription_type=transcription_type,
            stt_provider=session.stt_provider or "google",
            confidence_score=session.confidence_score,
            speaker_count=session.speaker_count,
        )

        # Calculate billability and cost
        usage_log._calculate_billability(user)
        usage_log._calculate_cost(session)

        # Extract quality metrics from session
        if session.transcript_text:
            usage_log._calculate_text_metrics(session.transcript_text)

        return usage_log

    @classmethod
    def create_for_retry(
        cls,
        original_log: "UsageLog",
        session: Session,
        user: User,
        is_failure_retry: bool = False,
    ) -> "UsageLog":
        """Factory method: Create usage log for retry attempt."""
        retry_type = (
            TranscriptionType.RETRY_FAILED if is_failure_retry
            else TranscriptionType.RETRY_SUCCESS
        )

        retry_log = cls.create_for_session(session, user, retry_type)
        retry_log.retry_count = original_log.retry_count + 1

        # Free retries for failures
        if is_failure_retry:
            retry_log.billable = False
            retry_log.cost_cents = 0

        return retry_log

    # Business Rules & Validation

    def is_billable_usage(self, user: User) -> bool:
        """Business rule: Determine if usage should be billed."""
        # Free retries for failures
        if self.transcription_type == TranscriptionType.RETRY_FAILED:
            return False

        # Manual entries are not billed
        if self.transcription_type == TranscriptionType.MANUAL:
            return False

        # Export operations may or may not be billed based on plan
        if self.transcription_type == TranscriptionType.EXPORT:
            return user.plan.value in ["pro", "enterprise", "coaching_school"]

        # Original transcriptions are always billed
        return True

    def validate_duration(self, duration_minutes: int) -> None:
        """Business rule: Validate duration constraints."""
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")

        if duration_minutes > 600:  # 10 hours
            raise ValueError("Duration cannot exceed 10 hours per session")

    def validate_cost(self, cost_cents: int) -> None:
        """Business rule: Validate cost constraints."""
        if cost_cents < 0:
            raise ValueError("Cost cannot be negative")

        # Maximum reasonable cost: 10 hours at premium rate
        max_cost = 10 * 60 * 50  # 10 hours * 60 minutes * 50 cents per minute
        if cost_cents > max_cost:
            raise ValueError(f"Cost {cost_cents} cents exceeds maximum reasonable cost")

    # Calculations

    def _calculate_billability(self, user: User) -> None:
        """Internal: Calculate if this usage should be billed."""
        self.billable = self.is_billable_usage(user)

    def _calculate_cost(self, session: Session) -> None:
        """Internal: Calculate cost based on duration and provider."""
        if not self.billable:
            self.cost_cents = 0
            return

        # Base cost per minute varies by provider
        if self.stt_provider == "assemblyai":
            # AssemblyAI: ~$0.00025 per second = ~$0.015 per minute
            cost_per_minute_cents = 2  # 2 cents per minute
        else:
            # Google STT: ~$0.006 per 15 seconds = ~$0.024 per minute
            cost_per_minute_cents = 3  # 3 cents per minute

        base_cost = self.duration_minutes * cost_per_minute_cents

        # Add complexity multiplier for multiple speakers
        if self.speaker_count and self.speaker_count > 2:
            multiplier = 1.0 + (self.speaker_count - 2) * 0.1  # 10% per additional speaker
            base_cost = int(base_cost * multiplier)

        # Add quality multiplier for low confidence
        if self.confidence_score and self.confidence_score < 0.8:
            base_cost = int(base_cost * 1.2)  # 20% surcharge for low confidence

        self.cost_cents = base_cost

    def _calculate_text_metrics(self, transcript_text: str) -> None:
        """Internal: Calculate text-based quality metrics."""
        if not transcript_text:
            return

        self.character_count = len(transcript_text)
        self.word_count = len(transcript_text.split())

    def get_cost_currency_formatted(self) -> str:
        """Business rule: Format cost in local currency."""
        if self.currency == "TWD":
            dollars = self.cost_cents / 100
            return f"NT${dollars:.2f}"
        elif self.currency == "USD":
            dollars = self.cost_cents / 100
            return f"${dollars:.2f}"
        else:
            return f"{self.cost_cents} cents"

    def get_duration_formatted(self) -> str:
        """Business rule: Format duration in human-readable format."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def calculate_efficiency_score(self) -> float:
        """Business rule: Calculate processing efficiency score."""
        if not self.processing_time_seconds or self.duration_minutes <= 0:
            return 0.0

        # Efficiency = actual duration / processing time
        # Higher score = more efficient processing
        actual_duration = self.duration_minutes * 60  # Convert to seconds
        efficiency = actual_duration / self.processing_time_seconds

        # Normalize to 0-100 scale (processing faster than real-time = 100+)
        return min(100.0, efficiency * 100)

    def get_words_per_minute(self) -> Optional[float]:
        """Business rule: Calculate words per minute rate."""
        if not self.word_count or self.duration_minutes <= 0:
            return None

        return self.word_count / self.duration_minutes

    def get_quality_score(self) -> float:
        """Business rule: Calculate overall quality score."""
        score = 0.0
        factors = 0

        # Factor 1: Confidence score (0-1)
        if self.confidence_score is not None:
            score += self.confidence_score * 40  # Weight: 40%
            factors += 1

        # Factor 2: Words per minute (reasonable range: 100-200 WPM)
        wpm = self.get_words_per_minute()
        if wpm is not None:
            # Optimal range: 120-180 WPM
            if 120 <= wpm <= 180:
                score += 30  # Weight: 30%
            elif 100 <= wpm <= 220:
                score += 20  # Acceptable range
            else:
                score += 10  # Outside optimal range
            factors += 1

        # Factor 3: Error occurrence
        if not self.error_occurred:
            score += 20  # Weight: 20%
        elif self.retry_count <= 1:
            score += 10  # Partial credit for quick recovery
        factors += 1

        # Factor 4: Processing efficiency
        efficiency = self.calculate_efficiency_score()
        if efficiency > 0:
            score += (efficiency / 100) * 10  # Weight: 10%
            factors += 1

        return score / factors if factors > 0 else 0.0

    # State Management

    def mark_error(self, error_message: str) -> None:
        """Business rule: Mark usage log with error."""
        if not error_message:
            raise ValueError("Error message cannot be empty")

        self.error_occurred = True
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def clear_error(self) -> None:
        """Business rule: Clear error status."""
        self.error_occurred = False
        self.error_message = None
        self.updated_at = datetime.utcnow()

    def update_processing_metrics(
        self,
        processing_time_seconds: int,
        confidence_score: Optional[float] = None,
    ) -> None:
        """Business rule: Update processing performance metrics."""
        if processing_time_seconds <= 0:
            raise ValueError("Processing time must be positive")

        if confidence_score is not None and not 0 <= confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")

        self.processing_time_seconds = processing_time_seconds
        if confidence_score is not None:
            self.confidence_score = confidence_score
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: any) -> None:
        """Business rule: Add metadata entry."""
        if not key:
            raise ValueError("Metadata key cannot be empty")

        if self.metadata is None:
            self.metadata = {}

        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    # Aggregation Helpers

    def contributes_to_monthly_usage(self) -> bool:
        """Business rule: Check if this log counts toward monthly usage limits."""
        return (
            self.billable and
            self.transcription_type in [
                TranscriptionType.ORIGINAL,
                TranscriptionType.RETRY_SUCCESS,
            ]
        )

    def get_effective_minutes(self) -> int:
        """Business rule: Get minutes that count toward user's quota."""
        return self.duration_minutes if self.contributes_to_monthly_usage() else 0