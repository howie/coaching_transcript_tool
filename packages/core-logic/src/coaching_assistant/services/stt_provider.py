"""Speech-to-Text provider abstraction layer."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A single transcript segment from STT processing."""
    speaker_id: int
    start_sec: float
    end_sec: float
    content: str
    confidence: float
    
    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class TranscriptionResult:
    """Complete transcription result from STT provider."""
    segments: List[TranscriptSegment]
    total_duration_sec: float
    language_code: str
    cost_usd: Optional[Decimal] = None
    provider_metadata: Optional[Dict[str, Any]] = None


class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""
    
    @abstractmethod
    def transcribe(
        self,
        audio_uri: str, 
        language: str = "auto",
        enable_diarization: bool = True,
        max_speakers: int = 4,
        min_speakers: int = 2
    ) -> TranscriptionResult:
        """
        Transcribe audio file with speaker diarization.
        
        Args:
            audio_uri: URI to audio file (e.g., gs://bucket/file.mp3)
            language: Language code (zh-TW, en-US, auto)
            enable_diarization: Enable speaker separation
            max_speakers: Maximum number of speakers to detect
            min_speakers: Minimum number of speakers to detect
            
        Returns:
            TranscriptionResult with segments and metadata
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, duration_seconds: int) -> Decimal:
        """
        Estimate transcription cost in USD.
        
        Args:
            duration_seconds: Audio duration in seconds
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass


class STTProviderError(Exception):
    """Base exception for STT provider errors."""
    pass


class STTProviderUnavailableError(STTProviderError):
    """STT provider is temporarily unavailable."""
    pass


class STTProviderQuotaExceededError(STTProviderError):
    """STT provider quota exceeded."""
    pass


class STTProviderInvalidAudioError(STTProviderError):
    """Invalid audio format or corrupted file."""
    pass