# User Story 1.2: Intelligent Speaker Assignment

## Story Overview

**Epic**: Epic 1 - Smart Transcript Enhancement  
**Story ID**: US-1.2  
**Priority**: High (Phase 1 Foundation)  
**Effort**: 5 Story Points  

## User Story

**As a coach, I want speaker diarization errors automatically fixed so that conversation flow is clear and professional.**

## Business Value

- **Professional Presentation**: Ensures transcripts are client-ready
- **Time Savings**: Eliminates manual speaker label editing
- **Accuracy Improvement**: Leverages AI to fix STT diarization mistakes
- **Certification Ready**: Meets professional coaching documentation standards

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-1.2.1**: Auto-detects coach vs client based on speaking patterns
- [ ] **AC-1.2.2**: Shows confidence score (High/Medium/Low) for speaker assignments
- [ ] **AC-1.2.3**: Allows manual override with drag-and-drop interface
- [ ] **AC-1.2.4**: Updates all occurrences when speaker label changed
- [ ] **AC-1.2.5**: Exports with proper "[Coach]:" and "[Client]:" formatting

### 🔧 Technical Criteria
- [ ] **AC-1.2.6**: Uses simple role assignment algorithm (speaking ratio based)
- [ ] **AC-1.2.7**: Handles 2-speaker conversations (coach + client)
- [ ] **AC-1.2.8**: Maintains timestamp synchronization
- [ ] **AC-1.2.9**: Supports batch speaker reassignment

### 📊 Quality Criteria
- [ ] **AC-1.2.10**: Achieves 95%+ accuracy in coach/client identification
- [ ] **AC-1.2.11**: <5% false positive rate for speaker misassignment
- [ ] **AC-1.2.12**: 90%+ user satisfaction with automatic assignments

## UI/UX Requirements

### Speaker Assignment Panel
```
┌─────────────────────────────────────────────────────┐
│ Speaker Assignment                                  │
├─────────────────────────────────────────────────────┤
│ Auto-Detection Results:                             │
│                                                     │
│ 🎯 Speaker A → Coach (Confidence: High - 92%)      │
│   ├─ Speaking time: 35% (14.2 min)                 │
│   ├─ Questions asked: 23                           │
│   └─ Word count: 2,847                             │
│                                                     │
│ 👤 Speaker B → Client (Confidence: High - 88%)     │
│   ├─ Speaking time: 65% (26.8 min)                 │
│   ├─ Questions asked: 8                            │
│   └─ Word count: 4,521                             │
│                                                     │
│ [🔄 Re-analyze Speakers] [✏️ Manual Override]       │
└─────────────────────────────────────────────────────┘
```

### Manual Override Interface
```
┌─────────────────────────────────────────────────────┐
│ Manual Speaker Assignment                           │
├─────────────────────────────────────────────────────┤
│ Drag speakers to correct roles:                     │
│                                                     │
│ [Coach] ←→ │ Speaker A (35% speaking time)         │
│ [Client] ←→ │ Speaker B (65% speaking time)        │
│                                                     │
│ ⚠️  Low confidence detected. Please review:         │
│ └─ Similar speaking patterns between speakers       │
│                                                     │
│ [✅ Apply Changes] [❌ Cancel] [🔍 Preview]         │
└─────────────────────────────────────────────────────┘
```

### Transcript Preview with Speaker Labels
```
┌─────────────────────────────────────────────────────┐
│ Transcript Preview                                  │
├─────────────────────────────────────────────────────┤
│ [00:01] [Coach]: Hello, how are you feeling today? │
│ [00:05] [Client]: I'm feeling okay, but a little   │
│         confused about my career direction.         │
│ [00:12] [Coach]: Can you tell me more about that    │
│         confusion?                                  │
│ [00:15] [Client]: Well, I've been in my current    │
│         job for five years...                       │
│                                                     │
│ 📊 Speaker Statistics:                             │
│ Coach: 18 turns, 2,847 words (35%)                 │
│ Client: 22 turns, 4,521 words (65%)                │
│                                                     │
│ [⬇️ Download Formatted] [📋 Copy to Clipboard]      │
└─────────────────────────────────────────────────────┘
```

### Confidence Indicators
```
High Confidence (90%+):   🟢 ●●●●●
Medium Confidence (70-89%): 🟡 ●●●○○  
Low Confidence (<70%):    🔴 ●●○○○

Confidence Factors:
✅ Clear speaking time ratio (Coach: 30-40%, Client: 60-70%)
✅ Question pattern analysis (Coach asks more questions)
✅ Speaking turn length (Coach: shorter, Client: longer)
⚠️  Similar word counts (requires manual review)
```

## Technical Implementation

### Speaker Analysis Algorithm
```python
class SimpleRoleAssigner:
    def analyze_speakers(self, segments):
        """Analyze speaking patterns to identify coach vs client."""
        
        # Calculate speaking statistics
        stats = self._calculate_speaker_stats(segments)
        
        # Apply coach identification heuristics
        confidence_scores = {}
        for speaker_id, data in stats.items():
            score = self._calculate_confidence_score(data)
            confidence_scores[speaker_id] = score
        
        # Assign roles based on patterns
        assignments = self._assign_roles(confidence_scores, stats)
        
        return {
            'assignments': assignments,
            'confidence_scores': confidence_scores,
            'statistics': stats
        }
    
    def _calculate_confidence_score(self, speaker_data):
        """Calculate confidence based on coaching patterns."""
        
        # Coach indicators:
        # - Lower speaking time (30-40%)
        # - More questions asked
        # - Shorter average turns
        # - Professional language patterns
        
        speaking_ratio = speaker_data['speaking_time_percent']
        question_ratio = speaker_data['questions_asked_percent']
        avg_turn_length = speaker_data['avg_turn_words']
        
        # Scoring algorithm
        coach_likelihood = 0.0
        
        # Speaking time scoring (coaches typically speak less)
        if 30 <= speaking_ratio <= 40:
            coach_likelihood += 0.4
        elif speaking_ratio < 30:
            coach_likelihood += 0.2
        
        # Question pattern scoring
        if question_ratio > 60:  # Coach asks most questions
            coach_likelihood += 0.3
        
        # Turn length scoring (coaches use shorter, focused responses)
        if avg_turn_length < 50:
            coach_likelihood += 0.2
        
        # Additional pattern analysis
        if self._detect_coaching_language(speaker_data['content']):
            coach_likelihood += 0.1
        
        return min(coach_likelihood, 1.0)
```

### API Endpoints
```http
POST /api/v1/sessions/{session_id}/analyze-speakers
Content-Type: application/json

{
    "algorithm": "simple_ratio",  // "simple_ratio", "nlp_enhanced", "manual"
    "confidence_threshold": 0.7
}

Response 200 OK:
{
    "analysis_id": "spk_abc123",
    "assignments": {
        "speaker_1": {
            "role": "coach",
            "confidence": 0.92,
            "reasoning": "Lower speaking time (35%), high question ratio (78%)"
        },
        "speaker_2": {
            "role": "client", 
            "confidence": 0.88,
            "reasoning": "Higher speaking time (65%), longer responses"
        }
    },
    "statistics": {
        "speaker_1": {
            "speaking_time_percent": 35.2,
            "word_count": 2847,
            "turn_count": 18,
            "questions_asked": 23,
            "avg_turn_words": 42.3
        }
    }
}
```

```http
PUT /api/v1/sessions/{session_id}/speaker-assignments
Content-Type: application/json

{
    "assignments": {
        "speaker_1": "coach",
        "speaker_2": "client"
    },
    "apply_to_transcript": true
}

Response 200 OK:
{
    "updated": true,
    "transcript_updated": true,
    "assignments_count": 2
}
```

### Database Schema
```sql
-- Speaker analysis results
CREATE TABLE speaker_analyses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    analysis_id VARCHAR(50) UNIQUE NOT NULL,
    algorithm_used VARCHAR(50) NOT NULL,
    overall_confidence DECIMAL(3,2),
    manual_override BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual speaker assignments
CREATE TABLE speaker_assignments (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(50) REFERENCES speaker_analyses(analysis_id),
    speaker_id VARCHAR(50) NOT NULL,
    assigned_role VARCHAR(20) NOT NULL, -- 'coach', 'client', 'unknown'
    confidence_score DECIMAL(3,2),
    speaking_time_percent DECIMAL(5,2),
    word_count INTEGER,
    turn_count INTEGER,
    questions_asked INTEGER,
    manual_assignment BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Test Scenarios

### Happy Path Testing
```gherkin
Scenario: Clear coach-client conversation
  Given I have a session with 2 speakers
  And Speaker A talks 35% of the time with many questions
  And Speaker B talks 65% of the time with longer responses
  When I analyze speakers automatically
  Then Speaker A is assigned as "Coach" with High confidence
  And Speaker B is assigned as "Client" with High confidence
  And I can export transcript with proper labels

Scenario: Manual override of assignments
  Given I have speaker analysis with Medium confidence
  When I drag Speaker A to "Client" role
  And drag Speaker B to "Coach" role
  Then all transcript occurrences update immediately
  And changes are saved to database
  And export uses new assignments
```

### Edge Case Testing
```gherkin
Scenario: Similar speaking patterns (ambiguous case)
  Given I have a session where both speakers talk equally
  And both ask similar numbers of questions  
  When I analyze speakers automatically
  Then system shows Low confidence warning
  And prompts for manual review
  And provides speaking statistics for guidance

Scenario: Single speaker session (monologue)
  Given I have a session with only 1 speaker detected
  When I analyze speakers
  Then system assigns single speaker as "Coach"
  And shows "Single speaker detected" message
  And allows manual addition of client segments if needed
```

### Integration Testing
```gherkin
Scenario: Speaker assignment with transcript correction
  Given I have completed transcript auto-correction
  When I analyze speakers on corrected transcript
  Then speaker analysis uses corrected text
  And assignments maintain timestamp accuracy
  And both corrections and assignments are preserved
```

## Success Metrics

### Quantitative KPIs
- **Accuracy Rate**: 95%+ correct coach/client identification
- **Processing Speed**: Speaker analysis completes within 5 seconds
- **User Override Rate**: <10% of analyses require manual override
- **High Confidence Rate**: 80%+ of analyses achieve "High" confidence
- **User Adoption**: 85% of users rely on auto-assignment

### Qualitative Indicators
- **User Feedback**: "Saves time and improves professionalism" (NPS >8)
- **Error Rate**: <2% of final assignments are incorrect
- **Support Tickets**: <1% of speaker assignments require support
- **Feature Utilization**: 90% of transcripts use speaker assignments

## Dependencies

### Technical Dependencies
- ✅ Session transcript data (existing)
- ✅ Speaker segmentation from STT (existing)
- 🔧 Simple role assignment algorithm (new development)
- 🔧 UI components for speaker management (new development)

### Functional Dependencies
- **Related Feature**: Works best after User Story 1.1 (Transcript Correction)
- **Future Enhancement**: Foundation for advanced speaker analysis (Epic 3)

## Risks & Mitigations

### High-Risk Items
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Ambiguous conversations (similar patterns) | Medium | Medium | Conservative approach + manual override UI |
| Group coaching sessions (3+ speakers) | Low | High | Scope limitation to 2-speaker sessions initially |

### Medium-Risk Items
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Non-traditional coaching styles | Medium | Low | Flexible algorithm parameters + user feedback |
| Different languages/cultures | Low | Medium | Algorithm testing across diverse sessions |

## Definition of Done

### Development Complete ✅
- [ ] Speaker analysis algorithm implemented and tested
- [ ] Manual override UI functional with drag-and-drop
- [ ] Confidence scoring system working accurately
- [ ] Bulk assignment updates working
- [ ] Export functionality includes speaker labels

### Quality Assurance ✅
- [ ] All test scenarios pass including edge cases
- [ ] Accuracy benchmarks met (95% identification rate)
- [ ] UI responsiveness and accessibility verified
- [ ] Integration with transcript correction tested

### Production Readiness ✅
- [ ] Performance optimization for large transcripts
- [ ] Error handling for unusual speaker patterns
- [ ] User documentation and help tooltips
- [ ] Analytics tracking for accuracy monitoring

### Success Validation ✅
- [ ] Beta testing shows 90%+ user satisfaction
- [ ] Accuracy metrics validated with diverse sessions
- [ ] Manual override rate <10% in real usage
- [ ] Support team trained on speaker assignment issues

---

**Previous User Story**: [User Story 1.1: Automatic Transcript Correction](./user-story-1.1-auto-correct.md)

**Next Epic**: [Epic 2: ICF Competency Analysis](../epic2-icf-analysis/README.md)

**Epic Overview**: [Epic 1: Smart Transcript Enhancement](./README.md)

**Technical Implementation**: [Speaker Role Analysis Research](../../research/speaker-role-analysis.md)