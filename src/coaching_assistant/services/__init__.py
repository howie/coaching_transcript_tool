"""Services module for external integrations."""

from .stt_provider import (
    STTProvider, 
    TranscriptSegment, 
    TranscriptionResult, 
    STTProviderError,
    STTProviderUnavailableError,
    STTProviderQuotaExceededError,
    STTProviderInvalidAudioError
)
from .google_stt import GoogleSTTProvider
from .stt_factory import STTProviderFactory

__all__ = [
    "STTProvider",
    "TranscriptSegment", 
    "TranscriptionResult",
    "STTProviderError",
    "STTProviderUnavailableError",
    "STTProviderQuotaExceededError", 
    "STTProviderInvalidAudioError",
    "GoogleSTTProvider",
    "STTProviderFactory"
]