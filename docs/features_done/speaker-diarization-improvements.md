# Speaker Diarization Improvements

## Overview

This document outlines the recent improvements to the speaker diarization system, implemented to enhance the accuracy of speaker identification in coaching session transcripts.

## Problem Statement

The original implementation encountered issues with Google Speech-to-Text v2's speaker diarization support:

1. **Limited Regional Support**: Not all Google Cloud regions support speaker diarization
2. **Model Compatibility**: Not all STT models support diarization features
3. **Language Restrictions**: Diarization support varies by language
4. **API Limitations**: `batchRecognize` API doesn't support diarization, only `recognize` API does

## Solution Architecture

### Intelligent API Selection

The system now implements a dual-API approach:

```python
def transcribe(self, audio_uri, language, enable_diarization=None, ...):
    if enable_diarization and self._validate_diarization_support(language, model, location):
        return self._transcribe_with_diarization(...)  # Uses recognize API
    else:
        return self._transcribe_batch_mode(...)        # Uses batchRecognize API
```

### Configuration-Driven Approach

New environment variables provide fine-grained control:

```env
# Core diarization settings
ENABLE_SPEAKER_DIARIZATION=true
MAX_SPEAKERS=2
MIN_SPEAKERS=2

# API selection (future use)
USE_STREAMING_FOR_DIARIZATION=false
```

## Implementation Details

### 1. Diarization Support Validation

```python
def _validate_diarization_support(self, language: str, model: str, enable_diarization: bool) -> bool:
    """
    Validate that the language-model-location combination supports diarization.
    Returns True if supported, False if fallback to batch mode needed.
    """
    diarization_supported = {
        ("en-us", "chirp_2", "us-central1"),
        ("en-us", "latest_long", "us-central1"),
        ("en-us", "latest_short", "us-central1"),
        ("en-us", "chirp", "global"),
        ("en-gb", "chirp", "global"),
    }
    
    location = settings.GOOGLE_STT_LOCATION
    return (language.lower(), model.lower(), location) in diarization_supported
```

### 2. Diarization-Enabled Transcription

When diarization is supported, the system uses the `recognize` API with enhanced processing:

```python
def _transcribe_with_diarization(self, audio_uri, language, max_speakers, min_speakers, ...):
    features = RecognitionFeatures(
        enable_automatic_punctuation=settings.ENABLE_PUNCTUATION,
        enable_word_time_offsets=True,
        enable_word_confidence=True,
        diarization_config=SpeakerDiarizationConfig(
            min_speaker_count=min_speakers,
            max_speaker_count=max_speakers
        )
    )
    
    response = self.client.recognize(request={
        "recognizer": recognizer_path,
        "config": config,
        "uri": audio_uri
    })
    
    return self._process_recognition_results_with_diarization(response)
```

### 3. Advanced Diarization Processing

The new processing method handles speaker tags and creates proper segments:

```python
def _process_recognition_results_with_diarization(self, response):
    segments = []
    
    for recognition_result in response.results:
        for alternative in recognition_result.alternatives:
            if hasattr(alternative, 'words') and alternative.words:
                # Group words by speaker_tag
                speaker_groups = {}
                for word in alternative.words:
                    speaker_tag = getattr(word, 'speaker_tag', 1)
                    if speaker_tag not in speaker_groups:
                        speaker_groups[speaker_tag] = []
                    speaker_groups[speaker_tag].append(word)
                
                # Create segments for each speaker group
                for speaker_tag, speaker_words in speaker_groups.items():
                    # Group consecutive words from same speaker
                    # Create segments with proper timing
```

### 4. Manual Role Assignment Enhancement

For scenarios where automatic diarization isn't available, the frontend provides enhanced manual editing:

#### Backend API
- **New endpoint**: `PATCH /sessions/{id}/segment-roles`
- **Data model**: `SegmentRole` for per-segment role assignments
- **Export integration**: All export formats include segment-level roles

#### Frontend Features
- **Individual segment editing**: Each transcript segment has an independent role selector
- **Real-time statistics**: Speaking time calculations update immediately
- **Persistent storage**: Role assignments are saved to database
- **Export consistency**: Manual assignments are included in all export formats

## Database Schema Changes

### New Table: `segment_role`

```sql
CREATE TABLE segment_role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES transcript_segment(id) ON DELETE CASCADE,
    role speakerrole NOT NULL,  -- ENUM: 'COACH', 'CLIENT', 'UNKNOWN'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, segment_id)
);
```

### Migration Applied
- **File**: `2961da1deaa6_add_segment_level_role_assignments.py`
- **Reuses existing enum**: `speakerrole` enum for consistency
- **Foreign key constraints**: Ensures data integrity

## Language and Region Support Matrix

| Language Code | Optimal Region | Model | Auto Diarization | Fallback Method |
|---------------|----------------|--------|------------------|-----------------|
| `en-US` | `us-central1` | `chirp_2` | ✅ Supported | recognize API |
| `en-US` | `asia-southeast1` | `chirp_2` | ❌ No support | batchRecognize + manual |
| `cmn-Hant-TW` | `asia-southeast1` | `chirp_2` | ❌ No support | batchRecognize + manual |
| `cmn-Hans-CN` | `asia-southeast1` | `chirp_2` | ❌ No support | batchRecognize + manual |
| `ja` | `asia-southeast1` | `chirp_2` | ❌ No support | batchRecognize + manual |
| `ko` | `asia-southeast1` | `chirp_2` | ❌ No support | batchRecognize + manual |

## Configuration Recommendations

### For English-Primary Coaching Sessions
```env
GOOGLE_STT_LOCATION=us-central1
GOOGLE_STT_MODEL=chirp_2
ENABLE_SPEAKER_DIARIZATION=true
MAX_SPEAKERS=2
MIN_SPEAKERS=2
```

### For Chinese/Multi-Asian Language Sessions (Current Default)
```env
GOOGLE_STT_LOCATION=asia-southeast1
GOOGLE_STT_MODEL=chirp_2
ENABLE_SPEAKER_DIARIZATION=true  # Will auto-fallback to batch mode
MAX_SPEAKERS=2
MIN_SPEAKERS=2
```

## Error Handling and Resilience

### Graceful Degradation
1. **Validation Check**: System validates diarization support before API calls
2. **Automatic Fallback**: If diarization not supported, seamlessly switches to batch API
3. **No Service Interruption**: Transcription continues regardless of diarization availability
4. **Informative Logging**: Clear logs indicate which API method and reasoning

### Error Recovery
```python
try:
    if enable_diarization:
        return self._transcribe_with_diarization(...)
    else:
        return self._transcribe_batch_mode(...)
        
except gcp_exceptions.InvalidArgument as e:
    if "diarization_config" in str(e):
        logger.warning("Diarization not supported, falling back to batch mode")
        return self._transcribe_batch_mode(...)
    raise
```

## Performance Impact

### Positive Impacts
- **Reduced API Errors**: Validation prevents unsupported API calls
- **Optimal Resource Usage**: Uses batch API when diarization not needed
- **Better User Experience**: No failed transcriptions due to configuration issues

### Considerations
- **Slight Overhead**: Validation adds minimal processing time
- **Memory Usage**: Diarization processing requires more memory for word-level analysis
- **API Costs**: `recognize` API may have different pricing than `batchRecognize`

## Testing Strategy

### Unit Tests
- Diarization support validation for various language/model/region combinations
- API selection logic testing
- Segment role assignment functionality

### Integration Tests
- End-to-end transcription with diarization enabled/disabled
- Manual role assignment workflow
- Export format consistency

### Load Testing
- Performance comparison between recognize and batchRecognize APIs
- Memory usage analysis for large audio files with diarization

## Future Enhancements

### Planned Improvements
1. **Dynamic Region Selection**: Automatically choose optimal region per language
2. **Hybrid Processing**: Combine automatic diarization with manual refinement
3. **Machine Learning**: Train custom speaker identification models
4. **Real-time Diarization**: Support for live coaching session transcription

### Configuration Flexibility
1. **Per-Client Settings**: Different diarization settings per coaching client
2. **Language Detection**: Automatic language detection for optimal model selection
3. **Quality Thresholds**: Confidence-based fallback mechanisms

## Troubleshooting Guide

### Common Issues

**Issue**: "Recognizer does not support feature: speaker_diarization"
**Solution**: System now automatically detects this and falls back to batch mode

**Issue**: Poor diarization accuracy
**Solutions**:
1. Verify using `us-central1` region for English content
2. Ensure audio quality is sufficient (clear speaker separation)
3. Adjust `MAX_SPEAKERS` and `MIN_SPEAKERS` parameters

**Issue**: Manual role assignments not saving
**Solution**: Check `segment_role` table exists and API endpoint is properly configured

### Monitoring and Logging

Key log messages to monitor:
- `"Using recognize API with diarization"` - Diarization enabled
- `"Using batchRecognize API without diarization"` - Fallback mode
- `"Diarization not supported for {language}+{model} in {location}"` - Configuration issue

## Conclusion

These improvements provide a robust, intelligent speaker diarization system that:
1. **Maximizes accuracy** where automatic diarization is supported
2. **Ensures reliability** through automatic fallback mechanisms  
3. **Maintains flexibility** with manual override capabilities
4. **Supports all languages** through degradation strategies

The implementation successfully resolves the original configuration errors while significantly enhancing the overall transcription experience for coaching professionals.