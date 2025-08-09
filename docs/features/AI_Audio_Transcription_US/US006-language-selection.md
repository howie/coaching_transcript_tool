# User Story: US006 - Language Selection

## Implementation Status: ⚠️ BASIC BACKEND SUPPORT

**Backend Status:** ⚠️ BASIC LANGUAGE PARAMETER SUPPORT (zh-TW, zh-CN, en-US in sessions API)  
**Frontend Status:** ❌ NO LANGUAGE PICKER UI

### Current Implementation
- ⚠️ Backend accepts language parameter in session creation
- ⚠️ Basic STT configuration for different languages exists
- ❌ No frontend language selection interface
- ❌ No auto-detection capability
- ❌ No language preference persistence

## Story
**As a** coach conducting sessions in different languages  
**I want to** select the appropriate language for transcription  
**So that** I get accurate transcripts regardless of the language used

## Priority: P1 (High)

## Acceptance Criteria

### AC1: Language Options
- [ ] Support Traditional Chinese (zh-TW) as default
- [ ] Support Simplified Chinese (zh-CN)
- [ ] Support English (en-US)
- [ ] Display language names in native script
- [ ] Show flag icons for visual identification

### AC2: Selection Interface
- [ ] Language dropdown in upload form
- [ ] Remember last selected language per user
- [ ] Default to user's browser language if supported
- [ ] Clear labeling: "Select transcription language"
- [ ] Required field before upload

### AC3: Auto-Detection (Beta)
- [ ] Offer "Auto-detect (Beta)" option
- [ ] Clear beta labeling and expectations
- [ ] Fallback to manual selection if detection fails
- [ ] Show detected language for confirmation
- [ ] Allow override of auto-detection

### AC4: Mixed Language Handling
- [ ] Primary language takes precedence
- [ ] Document mixed language limitations
- [ ] Best-effort transcription for secondary languages
- [ ] Note in results about mixed language content

### AC5: Language-Specific Features
- [ ] Apply appropriate punctuation rules
- [ ] Use language-specific STT models
- [ ] Adjust speaker detection patterns per language
- [ ] Format numbers/dates according to locale

## Definition of Done

### Development
- [ ] Language selection UI component created
- [ ] Language preference storage implemented
- [ ] STT configuration per language
- [ ] Auto-detection integration (beta)
- [ ] Unit tests for language handling

### Testing
- [ ] Test each supported language
- [ ] Test auto-detection accuracy
- [ ] Test mixed language scenarios
- [ ] Verify language preference persistence
- [ ] Test with non-supported languages

### Localization
- [ ] UI labels translated for each language
- [ ] Error messages localized
- [ ] Date/time formats adjusted
- [ ] Number formats localized

### Documentation
- [ ] Supported languages list
- [ ] Language accuracy expectations
- [ ] Mixed language limitations
- [ ] Auto-detection disclaimer

## Technical Notes

### Language Configuration
```javascript
const SUPPORTED_LANGUAGES = [
    {
        code: 'zh-TW',
        name: '繁體中文',
        englishName: 'Traditional Chinese',
        flag: '🇹🇼',
        sttModel: 'cmn-Hant-TW',
        priority: 1
    },
    {
        code: 'zh-CN',
        name: '简体中文',
        englishName: 'Simplified Chinese',
        flag: '🇨🇳',
        sttModel: 'cmn-Hans-CN',
        priority: 2
    },
    {
        code: 'en-US',
        name: 'English',
        englishName: 'English',
        flag: '🇺🇸',
        sttModel: 'en-US',
        priority: 3
    }
];
```

### API Request
```json
POST /api/v1/sessions
{
    "title": "Coaching Session",
    "language": "zh-TW",
    "auto_detect": false
}
```

### STT Configuration Mapping
```python
LANGUAGE_CONFIG = {
    "zh-TW": {
        "stt_code": "cmn-Hant-TW",
        "model": "long",
        "use_enhanced": True,
        "profanity_filter": False
    },
    "zh-CN": {
        "stt_code": "cmn-Hans-CN",
        "model": "long",
        "use_enhanced": True,
        "profanity_filter": False
    },
    "en-US": {
        "stt_code": "en-US",
        "model": "long",
        "use_enhanced": True,
        "profanity_filter": False
    }
}
```

### Auto-Detection Flow
```python
async def detect_language(audio_sample: bytes) -> str:
    # Use first 30 seconds for detection
    result = await stt_client.detect_language(
        audio_sample,
        language_hints=["zh-TW", "zh-CN", "en-US"]
    )
    
    if result.confidence > 0.7:
        return result.language
    else:
        return None  # Require manual selection
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wrong language selected | Poor transcription | Clear selection UI |
| Auto-detection failure | User frustration | Beta label, manual fallback |
| Mixed language accuracy | Incomplete transcript | Set expectations |

## Dependencies
- US002: Transcription Processing
- Google STT language models

## Related Stories
- US002: Transcription Processing
- US003: Speaker Role Detection
- Future: US010 - Additional Language Support

## Specification by Example

### Example 1: Manual Language Selection
**Given** I am uploading a coaching session audio  
**When** the upload form loads  
**Then** I should see language dropdown with options:  
- 🇹🇼 繁體中文 (Traditional Chinese) - selected by default  
- 🇨🇳 简体中文 (Simplified Chinese)  
- 🇺🇸 English  
**And** "Auto-detect (Beta)" option should be available  
**And** selected language should be saved for future uploads  

### Example 2: Auto-Detection Success
**Given** I select "Auto-detect (Beta)"  
**And** upload an English coaching session  
**When** detection completes  
**Then** system should detect "English" with >70% confidence  
**And** show confirmation: "Detected language: English. Proceed?"  
**And** I should be able to override if incorrect  
**And** transcription should use English STT model  

### Example 3: Auto-Detection Failure
**Given** I select "Auto-detect (Beta)"  
**And** upload audio with mixed Chinese and English  
**When** detection runs  
**Then** confidence should be <70%  
**And** system should show: "Unable to detect language reliably"  
**And** dropdown should appear for manual selection  
**And** no transcription should start until language is selected  

### Example 4: Traditional Chinese Processing
**Given** I select "繁體中文 (Traditional Chinese)"  
**When** transcription processes  
**Then** STT should use "cmn-Hant-TW" model  
**And** output should contain traditional characters: 你覺得, 這個, 問題  
**And** NOT simplified characters: 你觉得, 这个, 问题  
**And** Taiwan-specific terms should be recognized  

### Example 5: Language Preference Persistence
**Given** I previously selected "English" for a session  
**When** I upload a new file  
**Then** language dropdown should default to "English"  
**And** preference should persist across browser sessions  
**And** I can change it for specific uploads  
**And** new selection becomes new default  

### Example 6: Mixed Language Handling
**Given** I select "Traditional Chinese" as primary  
**And** the audio contains 80% Chinese, 20% English  
**When** transcription completes  
**Then** Chinese portions should be accurately transcribed  
**And** English portions should be best-effort transcribed  
**And** results should note "Mixed language content detected"  
**And** primary language model should be used throughout  

## Notes for QA
- Test with native speakers
- Verify language model accuracy
- Test code-switching scenarios
- Check persistence across sessions
- Validate auto-detection with various accents

## Future Enhancements
- Support more languages (Cantonese, Japanese, Korean)
- Dialect selection (Taiwan vs Beijing Mandarin)
- Multi-language transcripts with language tags
- Custom vocabulary per language
- Language-specific coaching pattern detection