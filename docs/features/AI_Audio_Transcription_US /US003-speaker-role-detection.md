# User Story: US003 - Automatic Speaker Role Detection

## Story
**As a** coach  
**I want to** have speakers automatically identified as Coach or Client  
**So that** I can quickly understand who said what without manual labeling

## Priority: P1 (High)

## Acceptance Criteria

### AC1: Automatic Detection Algorithm
- [ ] Analyze existing transcript segments with speaker IDs (1, 2, 3...)
- [ ] Use question frequency as primary indicator (coaches ask more questions)
- [ ] Detect coaching-specific language patterns
- [ ] Calculate confidence score for detection (0-100%)
- [ ] Support Traditional Chinese language patterns
- [ ] Input: segments with speaker_id, Output: role assignments

### AC2: Pattern Recognition
- [ ] Identify question markers ("嗎", "呢", "?")
- [ ] Detect coaching phrases ("你覺得", "你認為", "讓我們探索")
- [ ] Recognize client patterns ("我擔心", "我不知道", "困難")
- [ ] Weight patterns appropriately (questions = high weight)
- [ ] Handle mixed language sessions

### AC3: Confidence Thresholds
- [ ] Auto-assign roles when confidence > 60%
- [ ] Flag for manual review when confidence < 60%
- [ ] Show confidence score to users
- [ ] Allow manual override of automatic detection
- [ ] Remember manual corrections for learning (future)

### AC4: Two-Speaker Validation
- [ ] Ensure exactly one Coach and one Client for 2-speaker sessions
- [ ] Use question ratio to resolve conflicts
- [ ] Handle edge cases (both speakers similar patterns)
- [ ] Provide clear feedback when detection fails

### AC5: UI Integration
- [ ] Display detected roles in transcript view
- [ ] Show confidence indicator (high/medium/low)
- [ ] Provide easy role switching interface
- [ ] Highlight sections where detection is uncertain
- [ ] Save role assignments to database

## Definition of Done

### Development
- [ ] Speaker detection service implemented
- [ ] Pattern matching rules configured for zh-TW
- [ ] Confidence calculation algorithm tested
- [ ] Integration with transcription pipeline
- [ ] Unit tests with >80% coverage
- [ ] Test cases for various conversation styles

### Testing
- [ ] Test with real coaching conversations
- [ ] Validate >70% accuracy on test dataset
- [ ] Test edge cases (monologue, equal talking time)
- [ ] Verify manual override functionality
- [ ] Test with different coaching styles

### Performance
- [ ] Detection completes within 2 seconds for 1-hour transcript
- [ ] No significant memory overhead
- [ ] Efficient pattern matching implementation

### Documentation
- [ ] Algorithm documentation with examples
- [ ] Pattern library documented
- [ ] Confidence score calculation explained
- [ ] User guide for manual correction

## Technical Notes

### Detection Algorithm
```python
class SpeakerRoleDetector:
    def detect_roles(
        segments: List[TranscriptSegment],
        confidence_threshold: float = 0.6
    ) -> Tuple[Dict[int, str], float]:
        # Returns role mapping and confidence
        pass
```

### Pattern Configuration
```python
COACH_INDICATORS = [
    r"你覺得.*?",      # "What do you think..."
    r"你認為.*?",      # "What do you believe..."
    r"讓我們.*",       # "Let's..."
    r"能不能.*",       # "Can you..."
]

CLIENT_INDICATORS = [
    r"我擔心.*",       # "I'm worried..."
    r"我不知道.*",     # "I don't know..."
    r"困難.*",         # "It's difficult..."
]
```

### API Endpoint
```
PATCH /api/v1/sessions/{id}/speakers
{
    "speaker_roles": {
        "1": "Coach",
        "2": "Client"
    },
    "detection_method": "automatic|manual",
    "confidence": 0.75
}
```

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low detection accuracy | User frustration | Easy manual override |
| Cultural language differences | Misidentification | Locale-specific patterns |
| Non-standard coaching styles | False positives | Adjustable thresholds |

## Dependencies
- US002: Transcription Processing (segments with speaker IDs must exist)
- Language pattern research for zh-TW

## Related Stories
- US002: Transcription Processing
- US004: Transcript Export
- Future: US007 - Machine Learning Enhancement

## Specification by Example

### Example 1: Clear Coach Detection
**Given** a completed transcript with speaker-separated segments:  
- Speaker 1: "你覺得這個情況怎麼樣？"  
- Speaker 1: "能不能跟我分享一下？"  
- Speaker 2: "我覺得很困難。"  
**When** role detection algorithm processes the segments  
**Then** Speaker 1 should be identified as "Coach" with confidence >80%  
**And** Speaker 2 should be identified as "Client" with confidence >80%  
**And** detection method should be "automatic"  
**And** original speaker IDs are preserved with role labels added  

### Example 2: Low Confidence Detection
**Given** completed segments where both speakers ask equal questions  
**And** both use similar language patterns  
**When** role detection algorithm processes the segments  
**Then** confidence should be <60%  
**And** speaker_roles should be null  
**And** detection_method should be "manual_required"  
**And** UI should prompt for manual assignment  
**And** original speaker separation remains intact  

### Example 3: Manual Override
**Given** auto-detection assigned Speaker 1 as "Coach"  
**And** user manually changes Speaker 1 to "Client"  
**When** user saves the change  
**Then** speaker_roles should update to manual assignment  
**And** detection_method should be "manual"  
**And** confidence should remain from original detection  
**And** transcript export should use manual assignments  

### Example 4: Question Ratio Analysis
**Given** Speaker 1 asks 12 questions in 20 segments  
**And** Speaker 2 asks 2 questions in 15 segments  
**When** detection analyzes patterns  
**Then** Speaker 1 question ratio should be 60%  
**And** Speaker 2 question ratio should be 13%  
**And** Speaker 1 should be identified as "Coach"  
**And** Speaker 2 should be identified as "Client"  

### Example 5: Coaching Language Patterns
**Given** Speaker 1 uses phrases: "我聽到你在說", "讓我們探索"  
**And** Speaker 2 uses phrases: "我擔心", "我不知道怎麼辦"  
**When** pattern matching runs  
**Then** Speaker 1 coach_score should increase by 2  
**And** Speaker 2 client_score should increase by 2  
**And** these should contribute to final role assignment  

### Example 6: Edge Case Handling
**Given** a monologue with only one speaker  
**When** role detection runs  
**Then** single speaker should be labeled "Speaker 1"  
**And** no role should be automatically assigned  
**And** manual assignment should be required  
**And** UI should show "Unable to detect roles - single speaker"  

## Notes for QA
- Test with various coaching methodologies
- Verify with native Chinese speakers
- Test boundary cases (50/50 question ratio)
- Check persistence of manual corrections
- Validate confidence score accuracy

## Future Enhancements
- Machine learning model training
- Multi-language pattern support
- Group coaching support (>2 speakers)
- Pattern customization per user
- Learning from manual corrections