# User Story 1.1: Automatic Transcript Correction

## Story Overview

**Epic**: Epic 1 - Smart Transcript Enhancement  
**Story ID**: US-1.1  
**Priority**: High (Phase 1 Foundation)  
**Effort**: 8 Story Points  

## User Story

**As a coach, I want my raw transcripts automatically corrected so that I can focus on coaching insights rather than fixing typos.**

## Business Value

- **Time Savings**: Reduces manual transcript review from 30+ minutes to 2-3 minutes
- **Professional Quality**: Ensures all transcripts meet professional standards
- **Foundation Feature**: Enables all subsequent AI analysis features
- **User Satisfaction**: Addresses #1 user complaint about STT quality

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-1.1.1**: Click "Auto-Correct" button on session detail page
- [ ] **AC-1.1.2**: System processes transcript within 30 seconds for 60-minute sessions
- [ ] **AC-1.1.3**: Shows before/after comparison with highlighted changes
- [ ] **AC-1.1.4**: Can accept/reject individual corrections via toggle controls
- [ ] **AC-1.1.5**: Corrected transcript saved and immediately downloadable
- [ ] **AC-1.1.6**: Maintains original speaker turn structure and timing

### 🔧 Technical Criteria
- [ ] **AC-1.1.7**: Uses cost-effective LLM (Claude Haiku or GPT-3.5 Turbo)
- [ ] **AC-1.1.8**: Implements fallback mechanism for LLM failures
- [ ] **AC-1.1.9**: Tracks processing cost per correction
- [ ] **AC-1.1.10**: Preserves original meaning (human validation required)

### 📊 Quality Criteria
- [ ] **AC-1.1.11**: Achieves 90%+ accuracy vs human-corrected transcripts
- [ ] **AC-1.1.12**: 85%+ user acceptance rate of AI corrections
- [ ] **AC-1.1.13**: <5% false positive rate for unnecessary changes

## UI/UX Requirements

### Session Detail Page Enhancement
```
┌─────────────────────────────────────────────────────┐
│ Session: Client A - March 15, 2025                 │
├─────────────────────────────────────────────────────┤
│ Raw Transcript (STT Output)                        │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Coach]: hello how are u feeling today         │ │
│ │ [Client]: i am feeling ok but littl confused   │ │
│ │ [Coach]: can u tell me more about that         │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ [🔧 Auto-Correct Transcript] [⬇️ Download Raw]     │
└─────────────────────────────────────────────────────┘
```

### Processing State
```
┌─────────────────────────────────────────────────────┐
│ 🔄 Correcting transcript...                        │
│ ████████████████▒▒▒▒ 80% Complete (24s remaining)  │
│                                                     │
│ ✅ Grammar and punctuation fixes                   │
│ ✅ Speaker label standardization                   │
│ 🔄 Final validation and formatting                 │
└─────────────────────────────────────────────────────┘
```

### Diff Viewer Component
```
┌─────────────────────────────────────────────────────┐
│ Transcript Corrections Review                       │
├─────────────────────────────────────────────────────┤
│ Original                  │ Corrected               │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ │
│ │[Coach]: hello how are u │ │[Coach]: Hello, how are │ │
│ │feeling today            │ │you feeling today?       │ │
│ │                        │ │                        │ │
│ │[Client]: i am feeling  │ │[Client]: I am feeling  │ │
│ │ok but littl confused   │ │okay, but little        │ │
│ │                        │ │confused.               │ │
│ └─────────────────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ Changes Summary: 8 corrections found               │
│ ✅ Grammar (3) ✅ Punctuation (4) ✅ Spelling (1)  │
│                                                     │
│ [✅ Accept All] [❌ Reject All] [🔍 Review Each]    │
│ [⬇️ Download Corrected] [💾 Save & Continue]       │
└─────────────────────────────────────────────────────┘
```

### Individual Change Control
```
┌─────────────────────────────────────────────────────┐
│ Change #3 of 8                                      │
├─────────────────────────────────────────────────────┤
│ Original: "littl confused"                          │
│ Corrected: "little confused"                        │
│ Type: Spelling correction                           │
│                                                     │
│ [✅ Accept] [❌ Reject] [✏️ Edit Manually]          │
│                                [⏭️ Next Change]     │
└─────────────────────────────────────────────────────┘
```

## Technical Implementation

### API Endpoints
```http
POST /api/v1/sessions/{session_id}/correct-transcript
Content-Type: application/json

{
    "provider": "auto",  // "auto", "claude-haiku", "gpt-3.5-turbo"
    "options": {
        "fix_grammar": true,
        "fix_punctuation": true,
        "fix_spelling": true,
        "standardize_speakers": true
    }
}

Response 202 Accepted:
{
    "correction_id": "corr_abc123",
    "status": "processing",
    "estimated_completion": "2025-03-15T10:30:45Z"
}
```

```http
GET /api/v1/sessions/{session_id}/corrections/{correction_id}

Response 200 OK:
{
    "correction_id": "corr_abc123",
    "status": "completed",
    "processing_time_ms": 24500,
    "cost_usd": 0.15,
    "changes": [
        {
            "position": 12,
            "original": "hello how are u",
            "corrected": "Hello, how are you",
            "type": "grammar_punctuation",
            "confidence": 0.95
        }
    ],
    "corrected_transcript": "...",
    "diff_html": "..."
}
```

### Database Schema
```sql
-- Transcript corrections tracking
CREATE TABLE transcript_corrections (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    correction_id VARCHAR(50) UNIQUE NOT NULL,
    provider_used VARCHAR(50) NOT NULL,
    processing_time_ms INTEGER,
    cost_usd DECIMAL(10,4),
    changes_count INTEGER,
    user_accepted_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Individual correction changes
CREATE TABLE correction_changes (
    id SERIAL PRIMARY KEY,
    correction_id VARCHAR(50) REFERENCES transcript_corrections(correction_id),
    position_start INTEGER NOT NULL,
    position_end INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    confidence DECIMAL(3,2),
    user_action VARCHAR(20), -- 'accepted', 'rejected', 'modified'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Test Scenarios

### Happy Path Testing
```gherkin
Scenario: Successful transcript correction
  Given I have a session with raw STT transcript
  When I click "Auto-Correct Transcript" button
  Then I see processing indicator
  And processing completes within 30 seconds
  And I see before/after diff view
  And I can accept/reject individual changes
  And I can download corrected transcript
```

### Edge Case Testing
```gherkin
Scenario: LLM provider failure with fallback
  Given I have a session with raw transcript
  When I request auto-correction
  And primary provider (Claude) fails
  Then system automatically retries with GPT-3.5
  And correction completes successfully
  And user is unaware of the fallback

Scenario: Very short transcript (under 50 words)
  Given I have a 2-minute session with minimal speech
  When I request auto-correction
  Then system processes without errors
  And shows "minimal corrections needed" message
  And still provides downloadable result
```

### Performance Testing
```gherkin
Scenario: Large transcript processing
  Given I have a 90-minute session (15,000+ words)
  When I request auto-correction
  Then processing completes within 45 seconds
  And cost remains under $0.50
  And all corrections are accurately tracked
```

## Success Metrics

### Quantitative KPIs
- **Processing Speed**: 95% of corrections complete within 30 seconds
- **Accuracy Rate**: 90%+ vs human-validated corrections
- **User Adoption**: 75% of users use auto-correct within first month
- **Acceptance Rate**: 85%+ of AI corrections accepted by users
- **Cost Efficiency**: Average cost <$0.25 per transcript correction

### Qualitative Indicators
- **User Feedback**: "Saves me 20+ minutes per session" (NPS >8)
- **Support Tickets**: <2% of corrections require support intervention
- **Feature Stickiness**: 90% of users who try it use it regularly
- **Professional Quality**: Transcripts meet coaching certification standards

## Dependencies

### Technical Dependencies
- ✅ LLM Router Service (concurrent development)
- ✅ Session management system (existing)
- ✅ File upload/download infrastructure (existing)
- 🔧 Diff generation library (new requirement)

### External Dependencies
- **LLM Providers**: Claude (Anthropic) and GPT-3.5 (OpenAI) API access
- **Cost Monitoring**: Token usage tracking for billing
- **Performance Monitoring**: Response time tracking

### Business Dependencies
- **Legal Review**: AI correction disclaimers and user consent
- **Pricing Model**: Cost pass-through vs absorption strategy
- **Support Training**: Customer success team education

## Risks & Mitigations

### High-Risk Items
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| LLM accuracy below 90% | Medium | High | Extensive prompt engineering + human validation |
| Processing time >30s | Low | Medium | Performance optimization + user expectation setting |
| High per-correction cost | Medium | Medium | Cost monitoring + efficient provider selection |

### Medium-Risk Items
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| User rejection of AI changes | Medium | Medium | Conservative correction approach + user control |
| Provider API reliability | Low | High | Multi-provider fallback system |

## Definition of Done

### Development Complete ✅
- [ ] All acceptance criteria implemented and tested
- [ ] API endpoints functional with proper error handling
- [ ] UI components integrated and responsive
- [ ] Database schema deployed and migrated
- [ ] LLM integration working with fallback

### Quality Assurance ✅
- [ ] All test scenarios pass (happy path + edge cases)
- [ ] Performance benchmarks met (30s processing time)
- [ ] Security review completed (no PII leakage)
- [ ] Accessibility compliance verified (WCAG 2.1 AA)

### Production Readiness ✅
- [ ] Feature flag implemented for gradual rollout
- [ ] Monitoring and alerting configured
- [ ] Cost tracking and billing integration
- [ ] User documentation and help content
- [ ] Support team training completed

### Success Validation ✅
- [ ] Beta user testing shows 85%+ satisfaction
- [ ] Accuracy metrics validated with human experts
- [ ] Performance benchmarks consistently met
- [ ] Cost projections align with actual usage

---

**Next User Story**: [User Story 1.2: Intelligent Speaker Assignment](./user-story-1.2-speaker-assignment.md)

**Epic Overview**: [Epic 1: Smart Transcript Enhancement](../README.md)

**Technical Implementation**: [Transcript Correction Workflow](../../technical/workflows/transcript-correction.md)