# User Story 2.1: ICF Skills Assessment Dashboard

## Story Overview

**Epic**: Epic 2 - ICF Competency Analysis  
**Story ID**: US-2.1  
**Priority**: High (Phase 2 Core)  
**Effort**: 13 Story Points  

## User Story

**As a coach seeking ICF certification, I want AI analysis of my competencies so that I can track my progress and identify areas for improvement.**

## Business Value

- **Certification Support**: Directly supports ICF credential pursuit (40% of users)
- **Revenue Driver**: Justifies Pro tier subscription ($29/month)
- **Competitive Advantage**: First AI-powered ICF competency analysis tool
- **User Retention**: High-value feature drives long-term engagement

## Acceptance Criteria

### ✅ Primary Criteria
- [ ] **AC-2.1.1**: "Analyze ICF Competencies" button visible for Pro+ plans only
- [ ] **AC-2.1.2**: Generates scores (1-5 scale) for all 8 core competencies
- [ ] **AC-2.1.3**: Shows direct evidence quotes from transcript supporting each score
- [ ] **AC-2.1.4**: Provides specific, actionable improvement recommendations
- [ ] **AC-2.1.5**: Tracks competency progress over time with trend charts

### 🔧 Technical Criteria
- [ ] **AC-2.1.6**: Uses high-reasoning LLM (Claude 3.5 Sonnet preferred)
- [ ] **AC-2.1.7**: Processes analysis within 5 minutes for 60-minute sessions
- [ ] **AC-2.1.8**: Outputs structured JSON for reliable parsing
- [ ] **AC-2.1.9**: Costs <$2.00 per analysis (including retries)

### 📊 Quality Criteria
- [ ] **AC-2.1.10**: ±0.5 point accuracy vs expert ICF evaluator ratings
- [ ] **AC-2.1.11**: 90%+ evidence quote relevance to assigned scores
- [ ] **AC-2.1.12**: 80%+ coaches find recommendations actionable

## ICF Core Competencies Framework

### The 8 ICF Core Competencies
1. **Demonstrates Ethical Practice** - Understands and applies coaching ethics
2. **Embodies a Coaching Mindset** - Develops and maintains coaching mindset
3. **Establishes and Maintains Agreements** - Partners with client on process
4. **Cultivates Trust and Safety** - Creates supportive coaching environment
5. **Maintains Presence** - Remains conscious and responsive to client
6. **Listens Actively** - Focuses completely on what client expresses
7. **Evokes Awareness** - Facilitates client insights and learning
8. **Facilitates Client Growth** - Partners with client to transform learning

### Scoring Scale (ICF Standard)
- **5 - Expertly Demonstrated**: Exceptional skill level, consistent application
- **4 - Clearly Demonstrated**: Strong skill, mostly consistent application  
- **3 - Adequately Demonstrated**: Competent skill, generally consistent
- **2 - Somewhat Demonstrated**: Developing skill, inconsistent application
- **1 - Not Demonstrated**: Skill not evident or poorly applied

## UI/UX Requirements

### Analysis Trigger Interface
```
┌─────────────────────────────────────────────────────┐
│ Session: Executive Coaching - Sarah M.             │
├─────────────────────────────────────────────────────┤
│ ✅ Transcript Corrected                            │
│ ✅ Speakers Assigned (Coach: 38%, Client: 62%)     │
│                                                     │
│ 🎯 ICF Competency Analysis                         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 📊 Get professional ICF assessment of your     │ │
│ │     coaching skills and competencies           │ │
│ │                                                 │ │
│ │ • Scores for all 8 core competencies          │ │
│ │ • Evidence-based feedback                      │ │
│ │ • Improvement recommendations                  │ │
│ │ • Progress tracking over time                  │ │
│ │                                                 │ │
│ │ Estimated cost: $1.50 | Processing: 3-5 min   │ │
│ │                                                 │ │
│ │ [🚀 Analyze ICF Competencies] (Pro Feature)    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Processing State
```
┌─────────────────────────────────────────────────────┐
│ 🔄 Analyzing ICF Competencies...                    │
├─────────────────────────────────────────────────────┤
│ ████████████▒▒▒▒▒▒▒▒ 60% Complete (2:15 remaining) │
│                                                     │
│ ✅ Transcript processed and validated               │
│ ✅ Competency 1-3: Ethical Practice analyzed       │
│ 🔄 Competency 4-6: Trust and Listening in progress │
│ ⏳ Competency 7-8: Awareness and Growth pending     │
│ ⏳ Generating recommendations and evidence          │
│                                                     │
│ 💡 This analysis uses Claude 3.5 Sonnet for       │
│    expert-level coaching competency evaluation     │
└─────────────────────────────────────────────────────┘
```

### ICF Competency Dashboard
```
┌─────────────────────────────────────────────────────┐
│ ICF Competency Analysis - March 15, 2025           │
├─────────────────────────────────────────────────────┤
│ Overall Assessment: 3.4/5 (Above Average)          │
│ Processing: Claude 3.5 Sonnet | Cost: $1.45       │
│                                                     │
│ 📊 Competency Radar Chart                          │
│      Ethical Practice (4.0) ●●●●○                  │
│           /          \\                             │
│    Growth (3.0)      Mindset (3.5)                │
│       /                  \\                       │
│ Awareness (3.5) ——————————— Agreements (3.8)      │
│       \\                  /                       │
│    Presence (3.2)    Trust & Safety (3.1)         │
│           \\          /                           │
│        Active Listening (3.4)                      │
│                                                     │
│ 🎯 Key Strengths:                                  │
│ • Excellent ethical boundaries and agreements      │
│ • Strong coaching mindset and presence             │
│                                                     │
│ 🔍 Growth Areas:                                   │
│ • Trust & safety building needs attention          │
│ • Client growth facilitation could be enhanced     │
│                                                     │
│ [📋 View Detailed Report] [📈 Track Progress]       │
└─────────────────────────────────────────────────────┘
```

### Detailed Competency Breakdown
```
┌─────────────────────────────────────────────────────┐
│ Competency 4: Cultivates Trust and Safety (3.1/5)  │
├─────────────────────────────────────────────────────┤
│ Score Justification:                                │
│ The coach demonstrates basic trust-building skills  │
│ but missed opportunities to deepen psychological    │
│ safety. Some interruptions and advice-giving       │
│ reduced the collaborative atmosphere.               │
│                                                     │
│ 📝 Evidence from Transcript:                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [12:30] Coach: "I understand that must be       │ │
│ │ difficult. Can you tell me more about how       │ │
│ │ that makes you feel?"                           │ │
│ │                                                 │ │
│ │ [18:45] Coach: "You mentioned feeling stuck.   │ │
│ │ What does 'stuck' look like for you?"          │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ⚠️  Areas for Improvement:                         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [23:10] Coach: "You should try setting         │ │
│ │ clearer boundaries with your manager."          │ │
│ │ 💡 Consider: "What boundaries might serve you?" │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ 🎯 Specific Recommendations:                       │
│ • Practice holding silence longer (3-5 seconds)    │
│ • Replace advice with curious questions             │
│ • Acknowledge client emotions before redirecting   │
│ • Use more "What if..." and "How might..." stems  │
│                                                     │
│ [🔗 Link to Transcript] [📚 Resources] [✏️ Notes]  │
└─────────────────────────────────────────────────────┘
```

### Progress Tracking Interface
```
┌─────────────────────────────────────────────────────┐
│ ICF Competency Progress - Last 6 Months            │
├─────────────────────────────────────────────────────┤
│ Competency Trend Analysis:                          │
│                                                     │
│ Trust & Safety:    2.8 → 3.1 → 3.1 ↗️ +0.3       │
│ Active Listening:  3.1 → 3.4 → 3.4 ↗️ +0.3       │
│ Evokes Awareness:  3.2 → 3.5 → 3.5 ↗️ +0.3       │
│ Client Growth:     2.9 → 3.0 → 3.0 ↗️ +0.1       │
│                                                     │
│ 📈 Biggest Improvements:                           │
│ • Active Listening (+0.3) - More powerful questions │
│ • Trust & Safety (+0.3) - Better emotional attunement │
│                                                     │
│ 🎯 Focus Areas for Next Session:                   │
│ • Client Growth (3.0) - Lowest current score       │
│ • Facilitating deeper insights and accountability   │
│                                                     │
│ [📊 Export Progress Report] [🎯 Set Goals]          │
└─────────────────────────────────────────────────────┘
```

## Technical Implementation

### LLM Prompt Engineering
```python
ICF_ANALYSIS_PROMPT = """
You are an ICF Master Certified Coach (MCC) responsible for evaluating a coaching session. Analyze the provided transcript based on the 8 ICF Core Competencies.

**Instructions:**
1. For each of the 8 competencies, provide a score from 1 to 5 (1=Not Demonstrated, 5=Expertly Demonstrated).
2. For each score, provide a brief justification (2-3 sentences).
3. For each competency, extract 1-2 direct quotes from the transcript as evidence.
4. Provide one actionable recommendation for improvement for each competency.
5. Return the entire analysis as a single, valid JSON object. Do not include any text outside of the JSON.

**JSON Structure:**
{
  "overall_summary": "Brief summary of the coach's performance...",
  "average_score": 3.4,
  "processing_notes": "Key observations about the session...",
  "competencies": [
    {
      "id": 1,
      "name": "Demonstrates Ethical Practice",
      "score": 4,
      "justification": "Coach maintained clear boundaries...",
      "evidence": [
        { "timestamp": "12:30", "speaker": "Coach", "quote": "..." },
        { "timestamp": "25:15", "speaker": "Coach", "quote": "..." }
      ],
      "recommendation": "Consider...",
      "improvement_areas": ["boundary setting", "confidentiality"]
    }
    // ... (repeat for all 8 competencies)
  ]
}

**Transcript to Analyze:**
{transcript_content}

**JSON Output:**
"""
```

### API Endpoints
```http
POST /api/v1/sessions/{session_id}/analyze-icf
Content-Type: application/json

{
    "provider": "claude-sonnet",  // Preferred for ICF analysis
    "include_evidence": true,
    "include_recommendations": true,
    "previous_analyses": true  // For progress tracking
}

Response 202 Accepted:
{
    "analysis_id": "icf_abc123",
    "status": "processing",
    "estimated_completion": "2025-03-15T10:35:00Z",
    "estimated_cost_usd": 1.50
}
```

```http
GET /api/v1/sessions/{session_id}/icf-analysis/{analysis_id}

Response 200 OK:
{
    "analysis_id": "icf_abc123",
    "status": "completed",
    "processing_time_ms": 245000,
    "cost_usd": 1.45,
    "provider_used": "claude-3-5-sonnet",
    "overall_summary": "Strong coaching performance with...",
    "average_score": 3.4,
    "competencies": [
        {
            "id": 1,
            "name": "Demonstrates Ethical Practice",
            "score": 4.0,
            "justification": "Coach maintained excellent boundaries...",
            "evidence": [...],
            "recommendation": "Continue current approach...",
            "improvement_areas": []
        }
    ],
    "progress_data": {
        "previous_scores": [3.2, 3.4],
        "trend": "improving",
        "sessions_analyzed": 3
    }
}
```

### Database Schema
```sql
-- ICF competency analyses
CREATE TABLE icf_analyses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    analysis_id VARCHAR(50) UNIQUE NOT NULL,
    provider_used VARCHAR(50) NOT NULL,
    processing_time_ms INTEGER,
    cost_usd DECIMAL(10,4),
    overall_summary TEXT,
    average_score DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Individual competency scores
CREATE TABLE competency_scores (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(50) REFERENCES icf_analyses(analysis_id),
    competency_id INTEGER NOT NULL, -- 1-8 for ICF competencies
    competency_name VARCHAR(100) NOT NULL,
    score DECIMAL(3,2) NOT NULL, -- 1.0 to 5.0
    justification TEXT,
    recommendation TEXT,
    improvement_areas JSONB, -- Array of focus areas
    evidence JSONB, -- Array of evidence objects
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progress tracking
CREATE TABLE competency_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    competency_id INTEGER NOT NULL,
    analysis_date DATE NOT NULL,
    score DECIMAL(3,2) NOT NULL,
    session_id INTEGER REFERENCES sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, competency_id, analysis_date)
);
```

## Test Scenarios

### Happy Path Testing
```gherkin
Scenario: Successful ICF competency analysis
  Given I have a Pro+ subscription
  And I have a session with corrected transcript
  When I click "Analyze ICF Competencies"
  Then I see processing indicator with time estimate
  And analysis completes within 5 minutes
  And I see radar chart with 8 competency scores
  And each score has supporting evidence quotes
  And I receive actionable improvement recommendations

Scenario: Progress tracking across multiple sessions
  Given I have completed 3 ICF analyses over 2 months
  When I view my competency progress
  Then I see trend lines for each competency
  And I can identify my biggest improvements
  And I see focus areas for next sessions
```

### Edge Case Testing
```gherkin
Scenario: Short session with limited competency demonstration
  Given I have a 15-minute session transcript
  When I request ICF analysis
  Then system processes without errors
  And provides scores based on available evidence
  And notes limitations due to session length
  And suggests longer sessions for comprehensive analysis

Scenario: LLM provider failure with fallback
  Given Claude 3.5 Sonnet is unavailable
  When I request ICF analysis
  Then system automatically retries with GPT-4o
  And analysis completes successfully
  And user is notified of provider used
```

### Quality Validation Testing
```gherkin
Scenario: Expert validation comparison
  Given I have a session rated by an ICF MCC evaluator
  When I run AI analysis on the same session
  Then AI scores are within ±0.5 points of expert scores
  And evidence quotes support the given scores
  And recommendations align with expert feedback
```

## Success Metrics

### Quantitative KPIs
- **Accuracy**: ±0.5 point accuracy vs expert ICF evaluator ratings
- **Processing Time**: 95% complete within 5 minutes
- **Cost Efficiency**: Average cost <$2.00 per analysis
- **User Adoption**: 60% of Pro+ users try ICF analysis within 30 days
- **Evidence Quality**: 90%+ evidence quotes rated as relevant

### Qualitative Indicators
- **User Feedback**: "Provides insights I wouldn't have noticed" (NPS >8)
- **Professional Value**: "Helps me prepare for ICF credential applications"
- **Accuracy Perception**: 85%+ users trust the AI assessment
- **Actionability**: 80%+ users implement at least one recommendation

## Dependencies

### Technical Dependencies
- ✅ Epic 1: Enhanced transcripts (required for accurate analysis)
- ✅ LLM Router Service with Claude 3.5 Sonnet integration
- 🔧 Structured JSON parsing and validation system
- 🔧 Progress tracking database and visualization

### Business Dependencies
- **ICF Standards**: Ensure alignment with current ICF competency framework
- **Pro+ Subscription**: Feature gating and billing integration
- **Expert Validation**: Access to ICF-certified coaches for accuracy validation
- **Legal Review**: Disclaimers about AI assessment vs human evaluation

## Risks & Mitigations

### High-Priority Risks
| Risk | Impact | Probability | Mitigation |
|------|---------|-------------|------------|
| **ICF Accuracy Below ±0.5** | High | Medium | Extensive prompt engineering + expert validation |
| **High Processing Cost >$2** | Medium | Medium | Cost monitoring + model optimization |
| **User Distrust of AI Assessment** | High | Low | Transparency + expert validation studies |

### Medium-Priority Risks
| Risk | Impact | Probability | Mitigation |
|------|---------|-------------|------------|
| **JSON Parsing Failures** | Medium | Medium | Robust validation + retry logic |
| **Evidence Quote Irrelevance** | Medium | Low | Quote relevance scoring + filtering |

## Definition of Done

### Development Complete ✅
- [ ] ICF analysis triggered from session detail page
- [ ] Processing pipeline with progress indicators
- [ ] Radar chart visualization of competency scores
- [ ] Evidence viewer with transcript quote links
- [ ] Progress tracking across multiple sessions
- [ ] Structured JSON parsing and validation

### Quality Assurance ✅
- [ ] Expert validation shows ±0.5 point accuracy
- [ ] All test scenarios pass including edge cases
- [ ] Performance benchmarks met (5-minute processing)
- [ ] Cost targets achieved (<$2.00 per analysis)
- [ ] UI/UX tested for professional coaching context

### Production Readiness ✅
- [ ] Pro+ subscription gating implemented
- [ ] Cost tracking and billing integration
- [ ] Error handling and retry mechanisms
- [ ] User documentation and help content
- [ ] Analytics tracking for adoption and accuracy

### Success Validation ✅
- [ ] Beta testing with ICF-certified coaches
- [ ] Accuracy validated against human expert ratings
- [ ] User feedback shows 80%+ find recommendations actionable
- [ ] Business metrics justify Pro+ tier pricing

---

**Next User Story**: [User Story 2.2: Professional ICF Assessment Report](./user-story-2.2-icf-report.md)

**Epic Overview**: [Epic 2: ICF Competency Analysis](./README.md)

**Technical Implementation**: [ICF Analysis Workflow](../../technical/workflows/icf-analysis.md)