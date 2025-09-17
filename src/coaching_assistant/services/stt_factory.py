"""STT Provider factory for creating provider instances."""

import logging
from typing import Literal, Optional
from .stt_provider import STTProvider, STTProviderError
from .google_stt import GoogleSTTProvider
from .assemblyai_stt import AssemblyAIProvider
from ..core.config import settings

logger = logging.getLogger(__name__)


class STTProviderFactory:
    """Factory for creating STT provider instances."""

    @staticmethod
    def create(
        provider_type: Optional[
            Literal["google", "google_stt_v2", "assemblyai", "whisper"]
        ] = None,
    ) -> STTProvider:
        """
        Create STT provider instance.

        Args:
            provider_type: Type of provider to create. Defaults to value from settings.STT_PROVIDER.

        Returns:
            STT provider instance

        Raises:
            ValueError: If provider type is not supported
            STTProviderError: If provider initialization fails
        """
        # Use provider from settings if not specified
        if provider_type is None:
            provider_type = settings.STT_PROVIDER
        else:
            if not isinstance(provider_type, str):
                raise ValueError("provider_type must be a string")
            provider_type = provider_type.strip().lower()
            if not provider_type:
                raise ValueError("provider_type cannot be empty")

        logger.info(f"Creating STT provider: {provider_type}")

        try:
            if provider_type == "google" or provider_type == "google_stt_v2":
                return GoogleSTTProvider()
            elif provider_type == "assemblyai":
                return AssemblyAIProvider()
            elif provider_type == "whisper":
                # TODO: Implement WhisperSTTProvider when needed
                raise NotImplementedError(
                    "Whisper STT provider not yet implemented"
                )
            else:
                raise ValueError(
                    f"Unsupported STT provider type: {provider_type}"
                )
        except Exception as e:
            logger.error(
                f"Failed to create STT provider '{provider_type}': {e}"
            )
            raise STTProviderError(
                f"Failed to create STT provider '{provider_type}': {e}"
            )

    @staticmethod
    def create_with_fallback(
        primary_provider: Optional[str] = None,
        fallback_provider: str = "google",
    ) -> STTProvider:
        """
        Create STT provider with fallback support.

        Args:
            primary_provider: Primary provider to try first
            fallback_provider: Fallback provider if primary fails

        Returns:
            STT provider instance
        """
        if primary_provider is None:
            primary_provider = settings.STT_PROVIDER

        try:
            logger.info(
                f"Attempting to create primary STT provider: {primary_provider}"
            )
            return STTProviderFactory.create(primary_provider)
        except Exception as e:
            logger.warning(
                f"Primary provider '{primary_provider}' failed: {e}. Falling back to '{fallback_provider}'"
            )
            return STTProviderFactory.create(fallback_provider)

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available provider types."""
        return ["google", "assemblyai"]
