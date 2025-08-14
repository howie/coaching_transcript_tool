# US011: AssemblyAI Provider Integration

## User Story
**As a** coach using the platform  
**I want to** have the option to use AssemblyAI for transcription  
**So that** I can benefit from automatic speaker diarization and potentially better accuracy for certain languages

## Background
Based on POC testing with real coaching session data (Evaluation_1.mp4), AssemblyAI demonstrates strong capabilities in:
- Automatic speaker diarization without additional configuration
- Chinese language transcription (Simplified Chinese 'zh' only, requires post-processing for Traditional Chinese)
- Reasonable processing speed (~2 minutes for 28-minute audio)

**Important Language Limitation**: AssemblyAI only supports Simplified Chinese (language code: 'zh'). For Traditional Chinese (zh-TW) requirements, post-processing conversion is necessary.

## Acceptance Criteria ✅ COMPLETED

### 1. Provider Configuration ✅
- [x] Add AssemblyAI as a selectable STT provider in system configuration
- [x] Support environment variable `STT_PROVIDER` with values: `google` (default) | `assemblyai`
- [x] Store AssemblyAI API key securely in environment variables
- [x] Allow per-session provider selection via API

### 2. Core Integration ✅
- [x] Implement `AssemblyAIProvider` class following existing provider interface
- [x] Support audio upload via URL or file upload
- [x] Handle async transcription with status polling
- [x] Map AssemblyAI response format to internal transcript format

### 3. Chinese Language Support ✅
- [x] **Remove word spacing**: Join Chinese characters without spaces
- [x] **Unified script**: Convert Simplified Chinese output to Traditional Chinese (繁體中文) when zh-TW is requested
- [x] **Language handling**: Map user's zh-TW request to AssemblyAI's 'zh' with post-processing
- [x] **Consistency**: Ensure output format matches Google STT for seamless provider switching

### 4. Speaker Diarization ✅
- [x] Automatically enable speaker diarization (2 speakers expected)
- [x] Map speakers to Coach/Client roles using heuristics:
  - Speaker with more questions → likely Coach
  - Speaker with longer responses → likely Client
- [x] Allow manual role reassignment through existing UI

### 5. Error Handling ✅
- [x] Handle API rate limits gracefully
- [x] Implement retry mechanism for failed transcriptions
- [x] Provide fallback to Google STT if AssemblyAI fails
- [x] Clear error messages for configuration issues

## Technical Design

### Provider Interface
```python
class AssemblyAIProvider(TranscriptionProvider):
    def __init__(self, api_key: str):
        self.client = assemblyai.Transcriber()
        
    async def transcribe(self, audio_url: str, language: str = None) -> TranscriptResult:
        config = TranscriptionConfig(
            speech_model="best",
            speaker_labels=True,
            speakers_expected=2,
            language_code=self._map_language_code(language)
        )
        # Implementation details...
```

### Chinese Text Processing Pipeline
```python
def process_chinese_text(text: str) -> str:
    """Post-process Chinese transcription from AssemblyAI"""
    # 1. Remove spaces between Chinese characters
    text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)
    
    # 2. Convert Simplified to Traditional Chinese
    from chinese_converter import to_traditional
    text = to_traditional(text)
    
    # 3. Fix punctuation spacing
    text = fix_chinese_punctuation(text)
    
    return text
```

### Language Code Mapping
```python
# AssemblyAI language support mapping
ASSEMBLYAI_LANGUAGE_MAP = {
    "cmn-Hant-TW": "zh",  # Map Traditional Chinese to Simplified (with post-processing)
    "zh-TW": "zh",        # Map to 'zh' + post-process to Traditional
    "cmn-Hans-CN": "zh",  # Simplified Chinese (native support)
    "zh-CN": "zh",        # Simplified Chinese (native support)
    "en-US": "en",        # English
    "ja": "ja",           # Japanese
}

# Track which languages need post-processing
NEEDS_TRADITIONAL_CONVERSION = ["cmn-Hant-TW", "zh-TW"]
```

## Implementation Steps ✅ COMPLETED

### Phase 1: Core Integration ✅
1. ✅ Create `AssemblyAIProvider` class in `packages/core-logic/src/coaching_assistant/services/`
2. ✅ Implement basic transcription flow with async status polling
3. ✅ Add provider factory pattern for provider selection with fallback

### Phase 2: Chinese Language Optimization ✅
1. ✅ Implement text post-processing pipeline in `AssemblyAIProvider`
2. ✅ Add Traditional/Simplified Chinese converter using `opencc`
3. ✅ Fix punctuation and formatting issues (remove spaces, proper punctuation)

### Phase 3: Speaker Role Intelligence ✅
1. ✅ Implement speaker analysis heuristics in `SpeakerAnalyzer` utility
2. ✅ Add confidence scoring for role assignment
3. ✅ Integrate with existing role editing UI (segment-level role assignment)

### Phase 4: Testing & Deployment ✅
1. ✅ Unit tests for provider implementation (comprehensive test suite)
2. ✅ Integration tests with provider factory and fallback
3. ✅ Database migration and API endpoint testing
4. ✅ Authentication and CORS verification

## Implementation Details

### Files Created/Modified:
- **New**: `packages/core-logic/src/coaching_assistant/services/assemblyai_stt.py` - Complete AssemblyAI provider implementation
- **New**: `packages/core-logic/src/coaching_assistant/utils/speaker_analysis.py` - Speaker role assignment utility
- **Modified**: `packages/core-logic/src/coaching_assistant/services/stt_factory.py` - Added AssemblyAI support and fallback mechanism
- **Modified**: `packages/core-logic/src/coaching_assistant/models/session.py` - Added STT provider tracking fields
- **New**: `packages/core-logic/alembic/versions/49515d3a1515_add_stt_provider_tracking_fields.py` - Database migration
- **Modified**: `packages/core-logic/src/coaching_assistant/core/config.py` - Added AssemblyAI configuration
- **Modified**: `packages/core-logic/src/coaching_assistant/tasks/transcription_tasks.py` - Updated for multi-provider support
- **Modified**: `packages/core-logic/src/coaching_assistant/api/sessions.py` - Added provider selection and `/providers` endpoint
- **New**: Comprehensive test suite for AssemblyAI provider

## Configuration

### Environment Variables
```env
# STT Provider Selection
STT_PROVIDER=assemblyai  # or 'google'

# AssemblyAI Configuration
ASSEMBLYAI_API_KEY=your_api_key_here
ASSEMBLYAI_WEBHOOK_URL=https://api.example.com/webhooks/assemblyai  # Optional

# Provider-specific settings
ASSEMBLYAI_MODEL=best  # or 'nano' for faster/cheaper
ASSEMBLYAI_SPEAKERS_EXPECTED=2
```

### Feature Flags
```python
FEATURE_FLAGS = {
    "assemblyai_provider": True,
    "auto_speaker_detection": True,
    "chinese_text_processing": True,
    "provider_fallback": True,
}
```

## Cost Analysis

### AssemblyAI Pricing
- **Best model**: $0.00025/second (~$0.42 for 28-minute session)
- **Nano model**: $0.000125/second (~$0.21 for 28-minute session)

### Google STT Pricing (Current)
- **Chirp model**: Similar pricing tier
- **Additional costs**: Speaker diarization configuration

### Recommendation
- Use AssemblyAI for sessions requiring automatic speaker separation
- Use Google STT for languages with better regional support
- Implement cost tracking per provider

## Success Metrics

1. **Accuracy**: ≥95% word accuracy for supported languages
2. **Processing Speed**: <5 minutes for 30-minute audio
3. **Speaker Detection**: >90% correct role assignment
4. **Chinese Support**: 100% proper formatting after post-processing
5. **User Satisfaction**: Option to choose preferred provider

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API Key exposure | High | Secure storage, rotation policy |
| Chinese formatting issues | Medium | Comprehensive post-processing |
| Speaker misidentification | Low | Manual correction UI exists |
| Service downtime | Medium | Fallback to Google STT |
| Cost overrun | Low | Usage monitoring & alerts |

## Dependencies

- `assemblyai` Python SDK
- `opencc-python-reimplemented` for Chinese conversion
- Existing transcription infrastructure
- Redis for job queue management

## References

- [AssemblyAI API Documentation](https://www.assemblyai.com/docs)
- [POC Test Results](../../../poc-assemblyAI/assemblyai_analysis.md)
- [Existing Google STT Implementation](./US002-transcription-processing.md)

## Database Schema Changes

### 1. Add Provider Tracking
```sql
-- Add provider column to transcription_sessions table
ALTER TABLE transcription_sessions 
ADD COLUMN stt_provider VARCHAR(50) DEFAULT 'google';

-- Add provider metadata column for detailed tracking
ALTER TABLE transcription_sessions 
ADD COLUMN provider_metadata JSONB DEFAULT '{}';

-- Example provider_metadata content:
-- {
--   "provider": "assemblyai",
--   "model": "best",
--   "language_requested": "zh-TW",
--   "language_processed": "zh",
--   "post_processing_applied": ["remove_spaces", "convert_to_traditional"],
--   "fallback_used": false,
--   "processing_time_seconds": 118.9
-- }
```

### 2. Migration Script
```python
# Alembic migration
def upgrade():
    op.add_column('transcription_sessions', 
        sa.Column('stt_provider', sa.String(50), 
                  server_default='google', nullable=False))
    op.add_column('transcription_sessions',
        sa.Column('provider_metadata', sa.JSON(), 
                  server_default='{}', nullable=False))

def downgrade():
    op.drop_column('transcription_sessions', 'stt_provider')
    op.drop_column('transcription_sessions', 'provider_metadata')
```

## QA Test Plan

### 1. Provider Consistency Testing

#### Test Case 1.1: Output Format Consistency
**Objective**: Ensure both providers produce the same output structure
- **Steps**:
  1. Transcribe same audio file with Google STT
  2. Transcribe same audio file with AssemblyAI
  3. Compare JSON structure of outputs
- **Expected**: Identical JSON schema, same fields present
- **Validation Points**:
  - segments array structure
  - timestamp formats (start_time, end_time)
  - speaker role fields
  - confidence scores present

#### Test Case 1.2: Export Format Consistency
**Objective**: Verify all export formats work identically
- **Test all formats**: VTT, SRT, JSON, TXT
- **Steps**:
  1. Generate exports from Google STT transcript
  2. Generate exports from AssemblyAI transcript
  3. Validate format compliance
- **Expected**: Both providers produce valid, parseable files

### 2. Language Support Testing

#### Test Case 2.1: English Transcription
- **Input**: English coaching session (en-US)
- **Test both providers**
- **Compare**:
  - Word accuracy
  - Speaker diarization accuracy
  - Processing time

#### Test Case 2.2: Traditional Chinese (zh-TW)
- **Input**: Traditional Chinese coaching session
- **Google STT**: Direct zh-TW support
- **AssemblyAI**: zh → post-process to Traditional
- **Validation**:
  - No spaces between Chinese characters
  - All text in Traditional Chinese
  - Proper punctuation

#### Test Case 2.3: Simplified Chinese (zh-CN)
- **Input**: Simplified Chinese session
- **Both providers**: Native support
- **Compare output quality**

#### Test Case 2.4: Japanese
- **Input**: Japanese coaching session
- **Test both providers**
- **Validate character encoding and accuracy**

### 3. Speaker Diarization Testing

#### Test Case 3.1: Two-Speaker Sessions
- **Input**: Standard coach-client session
- **Validation**:
  - Correct speaker count (2)
  - Reasonable speaker distribution
  - Role assignment accuracy

#### Test Case 3.2: Role Assignment Consistency
- **Test**: Same audio should produce similar role assignments
- **Tolerance**: Allow for minor variations in automatic detection
- **Manual override**: Verify UI allows correction for both providers

### 4. Provider Switching Testing

#### Test Case 4.1: Environment Variable Switch
- **Steps**:
  1. Set `STT_PROVIDER=google`, restart, test
  2. Set `STT_PROVIDER=assemblyai`, restart, test
- **Expected**: Correct provider used each time

#### Test Case 4.2: Fallback Mechanism
- **Simulate AssemblyAI failure** (invalid API key)
- **Expected**: Automatic fallback to Google STT
- **Verify**: User notified of fallback

#### Test Case 4.3: Mid-Session Provider Change
- **Current session**: Should complete with original provider
- **New sessions**: Use new provider setting
- **Database**: Correctly tracks provider per session

### 5. Performance Testing

#### Test Case 5.1: Processing Time Comparison
- **Test files**: 5min, 15min, 30min, 60min audio
- **Measure**:
  - Time to complete transcription
  - API response times
  - Queue processing time
- **Acceptance**: AssemblyAI ≤ 2x Google STT time

#### Test Case 5.2: Concurrent Sessions
- **Test**: 5 simultaneous transcriptions
- **Both providers**
- **Monitor**: System stability, queue management

### 6. Error Handling Testing

#### Test Case 6.1: Invalid Audio Format
- **Both providers should reject gracefully**
- **User receives clear error message**

#### Test Case 6.2: Network Interruption
- **Simulate network issues during transcription**
- **Verify**: Retry mechanism works
- **Expected**: Eventually completes or fails gracefully

#### Test Case 6.3: API Limits
- **Test rate limiting handling**
- **Expected**: Queuing or user notification

### 7. Database Validation

#### Test Case 7.1: Provider Tracking
- **Verify** `stt_provider` field correctly set
- **Check** `provider_metadata` contains:
  - Provider name
  - Model used
  - Language codes
  - Processing details

#### Test Case 7.2: Historical Data
- **Existing sessions**: Should show `stt_provider='google'`
- **New sessions**: Correctly tagged with actual provider

### 8. UI/UX Consistency

#### Test Case 8.1: Transcript Display
- **Both providers' output displays identically**
- **No UI breaks with either provider**

#### Test Case 8.2: Statistics Calculation
- **Word count, duration, speaker percentages**
- **Should be consistent regardless of provider**

#### Test Case 8.3: Role Editing
- **Manual speaker role assignment works for both**
- **Changes persist correctly**

### 9. Regression Testing

#### Test Case 9.1: Existing Features
- **All current features continue working**:
  - Upload flow
  - Progress tracking
  - Email notifications
  - Export functions

#### Test Case 9.2: API Compatibility
- **Frontend API calls unchanged**
- **No breaking changes to API contract**

### 10. Acceptance Testing Checklist ✅ COMPLETED

- [x] Both providers produce transcripts successfully
- [x] Output format identical between providers
- [x] Chinese text properly formatted (no spaces)
- [x] Traditional Chinese conversion works
- [x] Speaker diarization functional
- [x] Export formats work correctly
- [x] Database tracks provider used
- [x] Fallback mechanism works
- [x] Performance acceptable
- [x] No regression in existing features
- [x] Error messages clear and helpful
- [x] API endpoints functional with authentication

### Test Data Requirements

1. **English coaching session** (30 min)
2. **Traditional Chinese session** (30 min)
3. **Simplified Chinese session** (30 min)
4. **Japanese session** (15 min)
5. **Mixed language session** (20 min)
6. **Poor audio quality sample** (5 min)
7. **Multiple speaker sample** (10 min)

### Success Criteria

- **Feature Parity**: 100% - All features work with both providers
- **Output Consistency**: >95% - Similar transcription quality
- **Performance**: AssemblyAI within 2x of Google STT
- **Reliability**: >99% success rate for valid audio
- **User Experience**: No noticeable difference to end users

## Implementation Status: ✅ COMPLETED (August 2025)

### ✅ Successfully Delivered:
1. **Full AssemblyAI Provider Integration** - Complete implementation with production-ready features
2. **Multi-Provider Architecture** - Seamless switching between Google STT and AssemblyAI
3. **Chinese Language Support** - Full Traditional Chinese conversion pipeline with space removal
4. **Speaker Intelligence** - Automatic coach/client role assignment with manual override
5. **Database Migration** - Provider tracking and metadata storage
6. **Comprehensive Testing** - Unit tests, integration tests, and API validation
7. **Fallback Mechanism** - Automatic failover from AssemblyAI to Google STT
8. **API Endpoints** - New `/providers` endpoint and session provider selection

### ✅ Technical Verification:
- **Authentication**: All endpoints properly secured with JWT
- **CORS**: Frontend integration ready
- **Database**: Migration applied and working
- **Provider Selection**: Users can choose provider per session
- **Error Handling**: Graceful failures with clear messages
- **Performance**: Efficient async processing with progress callbacks

### 🚀 Ready for Production:
The AssemblyAI provider is fully integrated and tested. The system now supports:
- Session creation with provider choice (`google`, `assemblyai`, or `auto`)
- Real-time progress tracking during transcription
- Chinese text processing with Traditional/Simplified conversion
- Automatic speaker diarization and role assignment
- Complete API compatibility with existing frontend
- Comprehensive error handling and provider fallback

## Notes

- ✅ Implementation focuses on coaching sessions (2 speakers) as specified
- 🔮 Future enhancement: Support multiple speakers (group coaching)
- 💰 Consider caching transcription results to reduce costs
- 📊 Monitor language-specific accuracy metrics post-deployment
- 🈳 AssemblyAI's 'zh' support includes post-processing for Traditional Chinese users
- 🔄 Seamless provider switching without breaking existing functionality