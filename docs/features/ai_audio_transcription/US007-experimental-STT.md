# US007: Experimental STT Configuration & Speaker Diarization Analysis

## Overview

This document analyzes the current Google Speech-to-Text v2 implementation challenges and proposes solutions for speaker diarization in coaching session transcriptions.

## Current Implementation Status

###  Step 1: Basic Transcription (COMPLETED)
- **Method**: Google STT v2 `batchRecognize`
- **Configuration**: 
  - Language: `cmn-Hant-TW` (BCP-47 format)
  - Model: `chirp_2` (latest with Chinese support)
  - Location: `asia-southeast1` (optimized for Asian languages)
  - Features: Auto punctuation, word timestamps, confidence scores
- **Result**: High-quality Chinese transcription without speaker diarization

### L Step 2: Speaker Diarization (NOT IMPLEMENTED)

## Technical Challenge: batchRecognize Limitation

### Problem
Google STT v2 speaker diarization is marked as "Preview" and only supports:
- `recognize` (synchronous, max 1 minute)
- `streamingRecognize` (real-time streaming)

**NOT supported**: `batchRecognize` (batch processing for long files)

### Error Encountered
```
400 Config contains unsupported fields. 
field_violations { field: "features.diarization_config" description: "Recognizer does not support feature: speaker_diarization" }
```

## Solution Architecture: Two-Stage Processing

### Stage 1: Transcription via batchRecognize 
- **Input**: Long audio file (up to 2 hours)
- **Output**: Word-level transcription with timestamps
- **Benefits**:
  -  Handles long coaching sessions (30-120 minutes)
  -  High accuracy for Chinese with `chirp_2` model
  -  Word-level timing information preserved
  -  Automatic punctuation and confidence scores

### Stage 2: Post-Processing Speaker Diarization L
- **Input**: Audio file + word-level transcript with timestamps
- **Output**: Speaker-segmented transcript
- **Implementation Options**:

## Speaker Diarization Implementation Options

### Option 1: PyAnnote.audio (Recommended)
```python
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
diarization = pipeline("audio.wav")
```

**Advantages**:
-  State-of-the-art accuracy
-  Supports Chinese and multilingual audio
-  Pre-trained models available
-  Active community and updates

**Disadvantages**:
- L Requires HuggingFace account and token
- L Additional compute resources needed
- L Extra processing time (30-60 seconds per minute of audio)

### Option 2: SpeechBrain Diarization
```python
from speechbrain.pretrained import SpeakerRecognition

model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)
```

**Advantages**:
-  Good accuracy
-  No external API dependencies
-  Integrated with SpeechBrain ecosystem

**Disadvantages**:
- L More complex setup
- L Less documentation for Chinese
- L Requires manual clustering implementation

### Option 3: Google STT v2 Streaming (Alternative)
Switch from `batchRecognize` to `streamingRecognize` with chunking.

**Advantages**:
-  Native diarization support
-  Same quality as batch processing
-  No additional ML models needed

**Disadvantages**:
- L Complex chunking logic for long files
- L Requires significant code restructuring
- L Streaming quota limits

## Use Cases & Benefits Analysis

### For Coaching Sessions

#### Primary Use Case: Coach-Client Identification
- **Benefit**: Automatic separation of coach vs. client speech
- **Value**: Enables role-based analysis and coaching effectiveness metrics
- **Implementation**: Map speaker_1 ’ Coach, speaker_2 ’ Client

#### Secondary Use Case: Group Coaching
- **Benefit**: Identify multiple participants in group sessions
- **Value**: Individual participation tracking and engagement metrics
- **Implementation**: Multiple speaker detection (2-6 speakers typical)

#### Quality Assurance Use Case
- **Benefit**: Verify transcription accuracy by speaker consistency
- **Value**: Detect transcription errors through speaker switching patterns
- **Implementation**: Flag unusual speaker change frequencies

### Business Value Proposition

#### Immediate Benefits (Stage 1 Only)
-  **Cost Effective**: Single-pass processing, no additional compute
-  **Fast Processing**: Direct batchRecognize, ~15-30 minutes for 1-hour audio
-  **High Accuracy**: chirp_2 model optimized for Chinese
-  **Reliable**: No dependencies on external ML models

#### Enhanced Benefits (Stage 1 + 2)
-  **Coach Analytics**: Measure speaking time ratios, conversation flow
-  **Client Insights**: Track client engagement and participation
-  **Session Quality**: Identify coaching techniques and effectiveness
-  **Automated Reporting**: Generate role-based session summaries

#### Cost-Benefit Analysis

| Aspect | Stage 1 Only | Stage 1 + 2 |
|--------|-------------|--------------|
| **Complexity** | Low | Medium |
| **Processing Time** | 15-30 min | 30-60 min |
| **Accuracy** | High (text) | High (text) + Medium (speakers) |
| **Resource Usage** | Low | Medium |
| **Maintenance** | Low | Medium |
| **Business Value** | Medium | High |

## Implementation Recommendations

### Phase 1: Stabilize Basic Transcription (Current Priority)
1.  Fix batchRecognize configuration
2.  Test with real coaching audio files
3.  Verify Chinese language accuracy
4.  Ensure stable processing pipeline

### Phase 2: Evaluate Diarization Need (Future)
1. Gather user feedback on single-speaker transcripts
2. Measure demand for speaker separation
3. Analyze coaching session audio characteristics
4. Determine ROI for diarization implementation

### Phase 3: Implement Diarization (If Needed)
1. **Recommended**: Start with PyAnnote.audio
2. Implement as background job (non-blocking)
3. Store both single-speaker and multi-speaker versions
4. Allow users to choose processing type

## Current Configuration (Working)

```python
# Google STT v2 Configuration
location = "asia-southeast1"
model = "chirp_2" 
language_codes = ["cmn-Hant-TW"]
features = {
    "enable_automatic_punctuation": True,
    "enable_word_time_offsets": True,
    "enable_word_confidence": True
    # diarization_config: REMOVED (not supported in batchRecognize)
}

# Result: Single speaker (speaker_id=1) with accurate timestamps
```

## Future Considerations

### Alternative: Hybrid Approach
For critical sessions requiring diarization:
1. Use `streamingRecognize` with 5-minute chunks
2. Enable native diarization for each chunk
3. Merge results with speaker mapping across chunks

### Model Evolution
Monitor Google STT v2 updates:
- Watch for `batchRecognize` diarization support
- Evaluate new model versions (chirp_3, etc.)
- Consider regional endpoint improvements

## Conclusion

**Current Strategy**: Implement robust Stage 1 (basic transcription) first, evaluate Stage 2 (diarization) based on user needs and technical requirements.

**Rationale**: 
- Solve immediate transcription needs with proven technology
- Avoid over-engineering without confirmed user demand
- Maintain system stability and predictable costs
- Allow for future enhancement when business case is clear

---

*Document Status: DRAFT*  
*Last Updated: 2025-08-11*  
*Next Review: After Stage 1 deployment*