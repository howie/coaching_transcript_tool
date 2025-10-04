"""UsageLogModel ORM with domain model conversion."""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import (
    DECIMAL,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ....core.config import settings
from ....core.models.usage_log import TranscriptionType, UsageLog
from .base import BaseModel


class UsageLogModel(BaseModel):
    """ORM model for UsageLog entity with SQLAlchemy mappings."""

    __tablename__ = "usage_logs"

    # Core relationships
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Usage metrics
    duration_minutes = Column(Integer, nullable=False)
    transcription_type = Column(
        Enum(TranscriptionType),
        default=TranscriptionType.ORIGINAL,
        nullable=False,
    )

    # Billing information
    # TODO: Re-enable after adding columns to database schema
    # billable = Column(Boolean, default=True, nullable=False)
    # cost_cents = Column(
    #     Integer, default=0, nullable=False
    # )  # Cost in cents for precise calculation
    # currency = Column(String(10), default="TWD", nullable=False)

    # Processing details
    stt_provider = Column(String(50), default="google", nullable=False)
    # TODO: Re-enable after adding columns to database schema
    # processing_time_seconds = Column(Integer)
    # confidence_score = Column(Float)

    # Quality metrics
    # TODO: Re-enable after adding columns to database schema
    # word_count = Column(Integer)
    # character_count = Column(Integer)
    # speaker_count = Column(Integer)

    # Error tracking
    # TODO: Re-enable after adding columns to database schema
    # error_occurred = Column(Boolean, default=False, nullable=False)
    # error_message = Column(Text)
    # retry_count = Column(Integer, default=0, nullable=False)

    # Metadata
    # TODO: Re-enable after adding columns to database schema
    # usage_metadata = Column(JSON)  # Store additional metadata as JSON

    # Legacy fields (maintain compatibility)
    # NOTE: According to actual DB schema, only cost_usd exists
    cost_usd = Column(DECIMAL(10, 4))  # Legacy cost field in USD
    # TODO: Re-enable after adding columns to database schema
    # processing_duration_seconds = Column(Integer)  # Legacy processing duration
    # session_duration_minutes = Column(Integer)  # Legacy session duration

    # ORM relationships
    session = relationship("SessionModel", back_populates="usage_logs")
    user = relationship("UserModel", back_populates="usage_logs")

    def to_domain(self) -> UsageLog:
        """Convert ORM model to domain model."""
        return UsageLog(
            id=PyUUID(str(self.id)) if self.id else None,
            session_id=(PyUUID(str(self.session_id)) if self.session_id else None),
            user_id=PyUUID(str(self.user_id)) if self.user_id else None,
            duration_minutes=self.duration_minutes or 0,
            transcription_type=self.transcription_type or TranscriptionType.ORIGINAL,
            billable=getattr(
                self, "billable", True
            ),  # Default to True if column doesn't exist
            cost_cents=getattr(self, "cost_cents", 0),
            currency=getattr(self, "currency", "TWD"),
            stt_provider=(
                (self.stt_provider or "").strip().lower() or settings.STT_PROVIDER
            ),
            processing_time_seconds=getattr(self, "processing_time_seconds", None),
            confidence_score=getattr(self, "confidence_score", None),
            word_count=getattr(self, "word_count", None),
            character_count=getattr(self, "character_count", None),
            speaker_count=getattr(self, "speaker_count", None),
            error_occurred=getattr(self, "error_occurred", False),
            error_message=getattr(self, "error_message", None),
            retry_count=getattr(self, "retry_count", 0),
            metadata=getattr(self, "usage_metadata", None),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, usage_log: UsageLog) -> "UsageLogModel":
        """Convert domain model to ORM model."""
        return cls(
            id=usage_log.id,
            session_id=usage_log.session_id,
            user_id=usage_log.user_id,
            duration_minutes=usage_log.duration_minutes,
            transcription_type=usage_log.transcription_type,
            # billable=usage_log.billable,  # Column doesn't exist yet
            # cost_cents=usage_log.cost_cents,  # Column doesn't exist yet
            # currency=usage_log.currency,  # Column doesn't exist yet
            stt_provider=usage_log.stt_provider,
            processing_time_seconds=usage_log.processing_time_seconds,
            confidence_score=usage_log.confidence_score,
            word_count=usage_log.word_count,
            character_count=usage_log.character_count,
            speaker_count=usage_log.speaker_count,
            error_occurred=usage_log.error_occurred,
            error_message=usage_log.error_message,
            retry_count=usage_log.retry_count,
            usage_metadata=usage_log.metadata,
            created_at=usage_log.created_at,
            updated_at=usage_log.updated_at,
        )

    def update_from_domain(self, usage_log: UsageLog) -> None:
        """Update ORM model fields from domain model."""
        self.duration_minutes = usage_log.duration_minutes
        self.transcription_type = usage_log.transcription_type
        # self.billable = usage_log.billable  # Column doesn't exist yet
        # self.cost_cents = usage_log.cost_cents  # Column doesn't exist yet
        # self.currency = usage_log.currency  # Column doesn't exist yet
        self.stt_provider = usage_log.stt_provider
        self.processing_time_seconds = usage_log.processing_time_seconds
        self.confidence_score = usage_log.confidence_score
        self.word_count = usage_log.word_count
        self.character_count = usage_log.character_count
        self.speaker_count = usage_log.speaker_count
        self.error_occurred = usage_log.error_occurred
        self.error_message = usage_log.error_message
        self.retry_count = usage_log.retry_count
        self.usage_metadata = usage_log.metadata
        self.updated_at = usage_log.updated_at or datetime.now(UTC)

    # Database-specific helper methods

    def get_cost_formatted(self) -> str:
        """Format cost in local currency."""
        cost_cents = getattr(self, "cost_cents", 0)
        currency = getattr(self, "currency", "TWD")

        if currency == "TWD":
            dollars = cost_cents / 100
            return f"NT${dollars:.2f}"
        elif currency == "USD":
            dollars = cost_cents / 100
            return f"${dollars:.2f}"
        else:
            return f"{cost_cents} cents"

    def get_duration_formatted(self) -> str:
        """Format duration in human-readable format."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def calculate_efficiency_score(self) -> Optional[float]:
        """Calculate processing efficiency score."""
        if not self.processing_time_seconds or self.duration_minutes <= 0:
            return None

        # Efficiency = actual duration / processing time
        actual_duration = self.duration_minutes * 60  # Convert to seconds
        efficiency = actual_duration / self.processing_time_seconds

        # Normalize to 0-100 scale
        return min(100.0, efficiency * 100)

    def get_words_per_minute(self) -> Optional[float]:
        """Calculate words per minute rate."""
        if not self.word_count or self.duration_minutes <= 0:
            return None

        return self.word_count / self.duration_minutes

    def get_quality_score(self) -> float:
        """Calculate overall quality score."""
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
        if efficiency and efficiency > 0:
            score += (efficiency / 100) * 10  # Weight: 10%
            factors += 1

        return score / factors if factors > 0 else 0.0

    def is_billable_usage(self) -> bool:
        """Check if this usage counts toward billing."""
        billable = getattr(self, "billable", True)  # Default to True
        return billable and self.transcription_type in [
            TranscriptionType.ORIGINAL,
            TranscriptionType.RETRY_SUCCESS,
        ]

    def contributes_to_monthly_usage(self) -> bool:
        """Check if this log counts toward monthly usage limits."""
        return self.is_billable_usage()

    def get_effective_minutes(self) -> int:
        """Get minutes that count toward user's quota."""
        return self.duration_minutes if self.contributes_to_monthly_usage() else 0

    def is_retry_attempt(self) -> bool:
        """Check if this is a retry attempt."""
        return self.transcription_type in [
            TranscriptionType.RETRY_FAILED,
            TranscriptionType.RETRY_SUCCESS,
        ]

    def is_free_retry(self) -> bool:
        """Check if this is a free retry."""
        return self.transcription_type == TranscriptionType.RETRY_FAILED

    def get_cost_per_minute(self) -> Optional[float]:
        """Calculate cost per minute."""
        if self.duration_minutes <= 0:
            return None
        cost_cents = getattr(self, "cost_cents", 0)
        return cost_cents / self.duration_minutes

    def get_processing_metrics(self) -> dict:
        """Get comprehensive processing metrics."""
        metrics = {
            "duration_minutes": self.duration_minutes,
            "cost_cents": getattr(self, "cost_cents", 0),
            "cost_formatted": self.get_cost_formatted(),
            "processing_time_seconds": self.processing_time_seconds,
            "confidence_score": self.confidence_score,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "speaker_count": self.speaker_count,
            "words_per_minute": self.get_words_per_minute(),
            "efficiency_score": self.calculate_efficiency_score(),
            "quality_score": self.get_quality_score(),
            "billable": getattr(self, "billable", True),
            "is_retry": self.is_retry_attempt(),
            "is_free": self.is_free_retry(),
            "effective_minutes": self.get_effective_minutes(),
        }
        return {k: v for k, v in metrics.items() if v is not None}

    def update_processing_metrics(
        self,
        processing_time_seconds: int,
        confidence_score: Optional[float] = None,
        word_count: Optional[int] = None,
        character_count: Optional[int] = None,
    ) -> None:
        """Update processing performance metrics."""
        # Future: Update when columns are added to schema
        # setattr(self, "processing_time_seconds", processing_time_seconds)
        # if confidence_score is not None:
        #     setattr(self, "confidence_score", confidence_score)
        # if word_count is not None:
        #     setattr(self, "word_count", word_count)
        # if character_count is not None:
        #     setattr(self, "character_count", character_count)
        self.updated_at = datetime.now(UTC)

    def mark_error(self, error_message: str) -> None:
        """Mark usage log with error."""
        # Future: self.error_occurred = True
        # Future: self.error_message = error_message
        self.updated_at = datetime.now(UTC)

    def clear_error(self) -> None:
        """Clear error status."""
        # Future: self.error_occurred = False
        # Future: self.error_message = None
        self.updated_at = datetime.now(UTC)

    def add_metadata(self, key: str, value: any) -> None:
        """Add metadata entry."""
        # Future: Use usage_metadata column when available
        # if self.usage_metadata is None:
        #     self.usage_metadata = {}
        # self.usage_metadata[key] = value
        self.updated_at = datetime.now(UTC)

    def sync_legacy_fields(self) -> None:
        """Sync data to legacy fields for backward compatibility."""
        cost_cents = getattr(self, "cost_cents", 0)
        currency = getattr(self, "currency", "TWD")

        # Convert cost to USD (assuming 30:1 TWD to USD ratio)
        if currency == "TWD":
            self.cost_usd = cost_cents / 100 / 30  # Rough conversion
        else:
            self.cost_usd = cost_cents / 100

        # Future: Sync processing duration when columns exist
        # self.processing_duration_seconds = getattr(self, "processing_time_seconds", None)
        # self.session_duration_minutes = self.duration_minutes

    def get_legacy_transcription_type(self) -> str:
        """Get transcription type in legacy string format."""
        type_mapping = {
            TranscriptionType.ORIGINAL: "original",
            TranscriptionType.RETRY_FAILED: "retry_failed",
            TranscriptionType.RETRY_SUCCESS: "retry_success",
            TranscriptionType.EXPORT: "export",
            TranscriptionType.MANUAL: "manual",
        }
        return type_mapping.get(self.transcription_type, "original")

    def __repr__(self):
        """String representation of the UsageLogModel."""
        return (
            f"<UsageLogModel(id={self.id}, "
            f"session_id={self.session_id}, "
            f"duration={self.duration_minutes}m, "
            f"type={self.transcription_type.value if self.transcription_type else 'None'}, "
            f"billable={getattr(self, 'billable', True)})>"
        )
