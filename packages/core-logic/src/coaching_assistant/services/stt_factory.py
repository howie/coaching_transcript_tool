"""STT Provider factory for creating provider instances."""

from typing import Literal, Optional
from .stt_provider import STTProvider
from .google_stt import GoogleSTTProvider


class STTProviderFactory:
    """Factory for creating STT provider instances."""
    
    @staticmethod
    def create(provider_type: Optional[Literal["google", "whisper"]] = None) -> STTProvider:
        """
        Create STT provider instance.
        
        Args:
            provider_type: Type of provider to create. Defaults to "google".
            
        Returns:
            STT provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type is None or provider_type == "google":
            return GoogleSTTProvider()
        elif provider_type == "whisper":
            # TODO: Implement WhisperSTTProvider when needed
            raise NotImplementedError("Whisper STT provider not yet implemented")
        else:
            raise ValueError(f"Unsupported STT provider type: {provider_type}")
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider types."""
        return ["google"]  # Add "whisper" when implemented