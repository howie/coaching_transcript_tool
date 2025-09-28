"""Services module for external integrations."""

from .google_stt import GoogleSTTProvider
from .stt_factory import STTProviderFactory
from .stt_provider import (
    STTProvider,
    STTProviderError,
    STTProviderInvalidAudioError,
    STTProviderQuotaExceededError,
    STTProviderUnavailableError,
    TranscriptionResult,
    TranscriptSegment,
)

__all__ = [
    "STTProvider",
    "TranscriptSegment",
    "TranscriptionResult",
    "STTProviderError",
    "STTProviderUnavailableError",
    "STTProviderQuotaExceededError",
    "STTProviderInvalidAudioError",
    "GoogleSTTProvider",
    "STTProviderFactory",
]
