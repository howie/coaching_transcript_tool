#!/usr/bin/env python3
"""
Provider Switching Design for STT Services
Demonstrates how to switch between Google STT and AssemblyAI
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from enum import Enum
import os

class STTProvider(Enum):
    """Available STT providers"""
    GOOGLE = "google"
    ASSEMBLYAI = "assemblyai"
    
class TranscriptionResult:
    """Unified transcription result format"""
    def __init__(self):
        self.status: str = "pending"
        self.full_text: str = ""
        self.segments: List[Dict] = []
        self.language: str = ""
        self.duration_seconds: float = 0
        self.speaker_count: int = 0
        self.metadata: Dict = {}

class BaseSTTProvider(ABC):
    """Abstract base class for STT providers"""
    
    @abstractmethod
    async def transcribe(self, audio_url: str, config: Dict) -> TranscriptionResult:
        """Transcribe audio and return unified result"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Return list of supported language codes"""
        pass
    
    @abstractmethod
    def supports_speaker_diarization(self) -> bool:
        """Check if provider supports speaker diarization"""
        pass

class GoogleSTTProvider(BaseSTTProvider):
    """Google Speech-to-Text provider implementation"""
    
    def __init__(self, credentials_json: str):
        self.credentials = credentials_json
        # Initialize Google STT client
        
    async def transcribe(self, audio_url: str, config: Dict) -> TranscriptionResult:
        """Implement Google STT transcription"""
        result = TranscriptionResult()
        # Implementation details...
        result.metadata["provider"] = "Google STT"
        result.metadata["model"] = config.get("model", "chirp_2")
        return result
    
    def get_supported_languages(self) -> List[str]:
        return ["en-US", "cmn-Hant-TW", "ja", "es", "fr"]
    
    def supports_speaker_diarization(self) -> bool:
        return True  # With configuration

class AssemblyAIProvider(BaseSTTProvider):
    """AssemblyAI provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize AssemblyAI client
        
    async def transcribe(self, audio_url: str, config: Dict) -> TranscriptionResult:
        """Implement AssemblyAI transcription"""
        result = TranscriptionResult()
        
        # Apply Chinese text processing if needed
        if config.get("language", "").startswith("zh"):
            from chinese_text_processor import process_assemblyai_chinese
            # Process Chinese text...
        
        result.metadata["provider"] = "AssemblyAI"
        result.metadata["model"] = config.get("model", "best")
        return result
    
    def get_supported_languages(self) -> List[str]:
        # AssemblyAI supports many languages with auto-detection
        return ["auto", "en", "zh", "ja", "es", "fr", "de", "it", "pt", "ko"]
    
    def supports_speaker_diarization(self) -> bool:
        return True  # Automatic, no configuration needed

class STTProviderFactory:
    """Factory for creating STT provider instances"""
    
    @staticmethod
    def create_provider(provider_type: STTProvider = None) -> BaseSTTProvider:
        """
        Create an STT provider instance based on configuration
        
        Priority:
        1. Explicit provider_type parameter
        2. STT_PROVIDER environment variable
        3. Default to Google STT
        """
        # Determine which provider to use
        if provider_type is None:
            env_provider = os.getenv("STT_PROVIDER", "google").lower()
            provider_type = STTProvider(env_provider) if env_provider in [p.value for p in STTProvider] else STTProvider.GOOGLE
        
        # Create provider instance
        if provider_type == STTProvider.ASSEMBLYAI:
            api_key = os.getenv("ASSEMBLYAI_API_KEY")
            if not api_key:
                raise ValueError("ASSEMBLYAI_API_KEY environment variable not set")
            return AssemblyAIProvider(api_key)
        else:  # Default to Google
            credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if not credentials:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")
            return GoogleSTTProvider(credentials)

class TranscriptionService:
    """High-level transcription service with provider switching"""
    
    def __init__(self, default_provider: STTProvider = None):
        self.default_provider = default_provider
        self.providers = {}
        
    def get_provider(self, provider_type: STTProvider = None) -> BaseSTTProvider:
        """Get or create a provider instance"""
        provider_type = provider_type or self.default_provider
        
        if provider_type not in self.providers:
            self.providers[provider_type] = STTProviderFactory.create_provider(provider_type)
        
        return self.providers[provider_type]
    
    async def transcribe_with_fallback(self, audio_url: str, config: Dict) -> TranscriptionResult:
        """
        Transcribe with automatic fallback to alternative provider
        """
        primary_provider_type = STTProvider(os.getenv("STT_PROVIDER", "google"))
        fallback_provider_type = STTProvider.GOOGLE if primary_provider_type == STTProvider.ASSEMBLYAI else STTProvider.ASSEMBLYAI
        
        try:
            # Try primary provider
            provider = self.get_provider(primary_provider_type)
            result = await provider.transcribe(audio_url, config)
            result.metadata["provider_used"] = primary_provider_type.value
            return result
            
        except Exception as e:
            print(f"Primary provider {primary_provider_type.value} failed: {e}")
            
            # Try fallback provider
            try:
                provider = self.get_provider(fallback_provider_type)
                result = await provider.transcribe(audio_url, config)
                result.metadata["provider_used"] = fallback_provider_type.value
                result.metadata["fallback_reason"] = str(e)
                return result
                
            except Exception as fallback_error:
                print(f"Fallback provider {fallback_provider_type.value} also failed: {fallback_error}")
                raise
    
    def select_best_provider_for_language(self, language: str) -> STTProvider:
        """
        Select the best provider based on language
        """
        # Language-specific recommendations
        language_preferences = {
            "zh-TW": STTProvider.ASSEMBLYAI,  # Better Chinese handling with post-processing
            "zh-CN": STTProvider.ASSEMBLYAI,
            "en-US": STTProvider.GOOGLE,       # Good diarization support
            "ja": STTProvider.ASSEMBLYAI,      # Better Japanese support
        }
        
        return language_preferences.get(language, STTProvider.GOOGLE)

# Configuration examples
def get_provider_config_examples():
    """Show configuration examples for different scenarios"""
    
    configs = {
        "google_coaching_session": {
            "provider": "google",
            "config": {
                "model": "chirp_2",
                "location": "us-central1",
                "enable_speaker_diarization": True,
                "min_speakers": 2,
                "max_speakers": 2,
                "language": "en-US"
            }
        },
        "assemblyai_coaching_session": {
            "provider": "assemblyai",
            "config": {
                "model": "best",
                "speaker_labels": True,
                "speakers_expected": 2,
                "language_detection": True,
                "auto_highlights": True
            }
        },
        "assemblyai_chinese_session": {
            "provider": "assemblyai",
            "config": {
                "model": "best",
                "speaker_labels": True,
                "speakers_expected": 2,
                "language_code": "zh",
                "post_processing": {
                    "remove_spaces": True,
                    "convert_to_traditional": True,
                    "fix_punctuation": True
                }
            }
        }
    }
    
    return configs

# Usage example
async def example_usage():
    """Demonstrate provider switching"""
    
    # Create transcription service
    service = TranscriptionService()
    
    # Example 1: Use default provider from environment
    audio_url = "https://example.com/coaching_session.mp3"
    config = {"language": "en-US", "speakers_expected": 2}
    result = await service.transcribe_with_fallback(audio_url, config)
    print(f"Transcribed using: {result.metadata['provider_used']}")
    
    # Example 2: Explicitly use AssemblyAI
    assemblyai_provider = service.get_provider(STTProvider.ASSEMBLYAI)
    result = await assemblyai_provider.transcribe(audio_url, config)
    
    # Example 3: Choose provider based on language
    language = "zh-TW"
    best_provider = service.select_best_provider_for_language(language)
    provider = service.get_provider(best_provider)
    result = await provider.transcribe(audio_url, {"language": language})
    
    return result

if __name__ == "__main__":
    import asyncio
    
    print("STT Provider Switching Design")
    print("=" * 60)
    
    # Show configuration examples
    configs = get_provider_config_examples()
    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  Provider: {config['provider']}")
        print(f"  Config: {config['config']}")
    
    # Show environment variables needed
    print("\n" + "=" * 60)
    print("Required Environment Variables:")
    print("=" * 60)
    print("STT_PROVIDER=google|assemblyai  # Choose provider")
    print("GOOGLE_APPLICATION_CREDENTIALS_JSON=<json>  # For Google STT")
    print("ASSEMBLYAI_API_KEY=<key>  # For AssemblyAI")
    
    # Run example (would need actual implementation)
    # asyncio.run(example_usage())