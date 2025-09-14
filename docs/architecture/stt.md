# STT Provider Architecture

## Overview

The coaching assistant platform supports multiple Speech-to-Text (STT) providers with automatic fallback and per-session configuration. This architecture ensures high availability and optimal language support.

## Supported Providers

### Google Speech-to-Text v2 (Default)
- **Model**: chirp_2 (latest, best accuracy)
- **Languages**: 100+ languages with automatic detection
- **Diarization**: Native speaker separation support
- **Regions**: Global with optimized regional endpoints
- **Pricing**: ~$0.016/minute, 60 min free tier

### AssemblyAI
- **Languages**: Enhanced Chinese (Traditional/Simplified) support
- **Diarization**: Advanced speaker separation
- **Features**: Auto-punctuation, sentiment analysis, summarization
- **Webhook**: Real-time status updates supported
- **Pricing**: ~$0.015/minute, no free tier

## Provider Selection Strategy

### 1. Environment Default
```python
STT_PROVIDER=google  # Set in .env file
```

### 2. Per-Session Override
```python
POST /sessions
{
    "language": "zh-TW",
    "stt_provider": "assemblyai"  # Override for this session
}
```

### 3. Automatic Selection (Future)
```python
def select_provider(language: str, region: str) -> str:
    """Auto-select best provider based on language and region"""
    if language.startswith("zh"):  # Chinese variants
        return "assemblyai"
    elif region == "US" and language == "en":
        return "google"  # Better US English diarization
    return "google"  # Default fallback
```

## Fallback Mechanism

### Primary Flow
1. **Google STT** (default) → Success → Return result
2. If Google fails → **Fallback to AssemblyAI** (if configured)
3. If AssemblyAI fails → Return error to user

### Fallback Triggers
- HTTP 5xx errors from provider
- Timeout (> 30 seconds for connection)
- Rate limiting responses
- Unsupported language errors

### Implementation
```python
async def transcribe_with_fallback(
    audio_file: str,
    primary_provider: str = "google"
) -> TranscriptionResult:
    """Transcribe with automatic fallback"""
    providers = ["google", "assemblyai"]
    
    # Try primary provider first
    try:
        provider = get_provider(primary_provider)
        return await provider.transcribe(audio_file)
    except ProviderError as e:
        logger.warning(f"Primary provider {primary_provider} failed: {e}")
    
    # Try fallback providers
    for fallback in providers:
        if fallback == primary_provider:
            continue
        try:
            provider = get_provider(fallback)
            logger.info(f"Attempting fallback to {fallback}")
            return await provider.transcribe(audio_file)
        except ProviderError:
            continue
    
    raise TranscriptionError("All providers failed")
```

## Language-Specific Optimization

### English (en-US, en-GB)
- **Preferred**: Google STT with `us-central1` region
- **Diarization**: Excellent native support
- **Accuracy**: 95%+ for clear audio

### Chinese (zh-TW, zh-CN)
- **Preferred**: AssemblyAI
- **Output**: Traditional Chinese characters
- **Speaker Roles**: Manual assignment available
- **Accuracy**: 92%+ with proper audio quality

### Japanese (ja-JP)
- **Preferred**: Google STT with `asia-northeast1` region
- **Features**: Excellent kanji/kana recognition
- **Speaker Roles**: Manual assignment recommended
- **Accuracy**: 93%+ for standard Japanese

## Regional Endpoint Strategy

### Google STT Regions
```python
REGION_MAPPING = {
    "en-US": "us-central1",      # Best English diarization
    "en-GB": "europe-west2",     # UK English optimization
    "zh-*": "asia-southeast1",   # Chinese languages
    "ja-JP": "asia-northeast1",  # Japanese optimization
    "es-*": "us-central1",       # Spanish variants
    "fr-*": "europe-west1",      # French optimization
}
```

### Latency Considerations
- Use closest regional endpoint to reduce latency
- Audio upload to GCS should use same region
- Consider multi-region replication for global users

## Audio Processing Pipeline

### 1. Audio Upload
```
Client → API → GCS Bucket (regional)
```

### 2. Provider Selection
```
Session Config → Provider Strategy → Select Provider
```

### 3. Transcription
```
Provider API → Process Audio → Return Segments
```

### 4. Post-Processing
```
Raw Transcript → Diarization → Speaker Assignment → Final Output
```

## Provider-Specific Features

### Google STT Features
- **Auto-punctuation**: Enabled by default
- **Word-level timestamps**: For precise alignment
- **Confidence scores**: Per-word and per-segment
- **Profanity filter**: Optional censoring
- **Model adaptation**: Custom vocabulary boost

### AssemblyAI Features
- **Sentiment analysis**: Per-segment emotion detection
- **Entity detection**: Names, locations, organizations
- **Summarization**: Automatic key points extraction
- **Custom vocabulary**: Industry-specific terms
- **Speaker labels**: Automatic speaker identification

## Error Handling

### Provider Errors
```python
class ProviderError(Exception):
    """Base class for provider-specific errors"""
    pass

class RateLimitError(ProviderError):
    """Provider rate limit exceeded"""
    retry_after: int  # Seconds to wait

class LanguageNotSupportedError(ProviderError):
    """Language not supported by provider"""
    supported_languages: List[str]

class AudioFormatError(ProviderError):
    """Audio format not supported"""
    supported_formats: List[str]
```

### Retry Strategy
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(ProviderError)
)
async def transcribe_with_retry(audio_file: str) -> TranscriptionResult:
    """Transcribe with automatic retry on failure"""
    return await provider.transcribe(audio_file)
```

## Monitoring & Metrics

### Key Metrics
- **Provider success rate**: Track failures per provider
- **Transcription latency**: P50, P95, P99 percentiles
- **Fallback frequency**: How often fallback is triggered
- **Language distribution**: Usage per language
- **Cost per provider**: Track spending

### Alerting Thresholds
- Provider error rate > 5% → Alert
- Fallback rate > 10% → Investigate primary provider
- Latency P95 > 30s → Performance degradation
- Cost spike > 150% → Budget alert

## Cost Optimization

### Strategies
1. **Batch processing**: 50% discount for async batch (Google)
2. **Regional pricing**: Use cheaper regions when possible
3. **Audio compression**: Reduce file size before upload
4. **Caching**: Cache transcripts for identical audio
5. **Provider mixing**: Use cheapest provider per language

### Cost Calculation
```python
def calculate_transcription_cost(
    duration_seconds: int,
    provider: str,
    features: List[str]
) -> float:
    """Calculate transcription cost"""
    duration_minutes = duration_seconds / 60
    
    base_rates = {
        "google": 0.016,      # Per minute
        "assemblyai": 0.015,  # Per minute
    }
    
    feature_multipliers = {
        "diarization": 1.0,   # No extra cost
        "sentiment": 1.2,     # 20% extra (AssemblyAI)
        "summarization": 1.3, # 30% extra (AssemblyAI)
    }
    
    base_cost = base_rates[provider] * duration_minutes
    multiplier = max(feature_multipliers.get(f, 1.0) for f in features)
    
    return base_cost * multiplier
```

## Future Enhancements

1. **Multi-provider parallel processing**: Run multiple providers and merge results
2. **Custom model training**: Fine-tune models for coaching domain
3. **Real-time transcription**: WebSocket-based live transcription
4. **Offline processing**: On-premise STT for sensitive data
5. **Quality scoring**: Automatic audio quality assessment