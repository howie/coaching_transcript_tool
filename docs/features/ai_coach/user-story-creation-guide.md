# User Story Creation Guide for Claude Subagents

## Purpose

This guide provides Claude subagents with a structured methodology for breaking down complex features into deliverable user stories that provide end-to-end value and can be demonstrated through the UI.

## When to Use This Guide

### Primary Use Cases
- **feature-analyst**: Breaking down requirements into logical epics and stories
- **user-story-designer**: Creating detailed user story specifications
- **product-planner**: Creating implementation roadmaps with phased delivery
- **requirements-analyst**: Analyzing and documenting complex requirements

### Trigger Conditions
- User requests feature breakdown or analysis
- Complex requirements need to be decomposed
- Product planning and roadmap creation needed
- User story documentation required for development teams

## Methodology Overview

### 1. Analysis Framework
```
📋 Requirements Input
    ↓ 
🎯 Epic Identification (group related features)
    ↓
📖 User Story Creation (individual value delivery)
    ↓
✅ Acceptance Criteria (testable conditions)
    ↓
🖥️ UI/UX Specification (demonstrable interface)
    ↓
🔧 Technical Implementation (development guidance)
    ↓
📊 Success Metrics (measurable outcomes)
```

### 2. Core Principles

#### User Value Focus
- **End-to-End Value**: Each story must deliver complete user value
- **Demonstrable**: Must be testable and demonstrable through UI
- **Independent**: Stories should be deliverable independently
- **Measurable**: Success must be quantifiable

#### Quality Standards
- **Testable**: All acceptance criteria must be verifiable
- **Specific**: Avoid vague or subjective requirements
- **Achievable**: Within team capabilities and timeline
- **Business-Aligned**: Supports strategic business objectives

## Step-by-Step Process

### Step 1: Epic Identification
**Goal**: Group related functionality into logical delivery phases

**Process**:
1. **Analyze Requirements**: Identify major functional areas
2. **Group by Value**: Cluster features that deliver related business value  
3. **Sequence by Dependency**: Order epics based on technical dependencies
4. **Validate Business Impact**: Ensure each epic justifies development investment

**Epic Naming Convention**: 
```
Epic X: [Value Proposition] 
Example: "Epic 1: Smart Transcript Enhancement"
```

**Epic Structure**:
```markdown
# Epic X: [Name]

## Value Proposition
[Clear statement of business value and user benefit]

## User Stories
- Story X.1: [Primary feature]
- Story X.2: [Supporting feature]

## Success Criteria
[Measurable outcomes for epic completion]
```

### Step 2: User Story Creation
**Goal**: Define individual deliverable features with clear user value

**Story Template**:
```markdown
# User Story X.Y: [Feature Name]

## Story Overview
**Epic**: [Epic Name]
**Story ID**: US-X.Y  
**Priority**: High/Medium/Low (Phase X)
**Effort**: [Story Points]

## User Story
**As a [user type], I want [functionality] so that [business value].**

## Business Value
- [Quantified user/business impact]
- [Revenue/cost implications] 
- [Strategic importance]

## Acceptance Criteria
### ✅ Primary Criteria
- [ ] **AC-X.Y.1**: [Core user interaction]
- [ ] **AC-X.Y.2**: [Key functionality requirement]

### 🔧 Technical Criteria
- [ ] **AC-X.Y.6**: [Performance requirement]
- [ ] **AC-X.Y.7**: [Integration requirement]

### 📊 Quality Criteria  
- [ ] **AC-X.Y.10**: [Accuracy/success metrics]

## UI/UX Requirements
[ASCII mockups and interface specifications]

## Technical Implementation
[API endpoints, database schema, key algorithms]

## Success Metrics
[Quantitative KPIs and qualitative indicators]

## Dependencies & Risks
[Prerequisites and potential blockers]
```

### Step 3: Acceptance Criteria Definition
**Goal**: Create testable conditions for story completion

**Criteria Categories**:

#### Primary Criteria (User Experience)
- User interactions and workflows
- Core functionality requirements
- UI behavior and feedback
- Data input/output validation

#### Technical Criteria (System Requirements)
- Performance benchmarks
- Integration requirements
- Security and privacy standards
- Error handling and edge cases

#### Quality Criteria (Success Measurement)
- Accuracy targets
- User satisfaction metrics
- Business impact measurements
- Adoption and usage goals

**Writing Guidelines**:
- Use active voice and specific verbs
- Include measurable targets (time, accuracy, percentage)
- Specify user interactions clearly
- Cover happy path and edge cases

### Step 4: UI/UX Specification
**Goal**: Provide clear visual guidance for interface development

**Requirements**:
- ASCII mockups for key interfaces
- User workflow diagrams
- Component interaction specifications
- Responsive design considerations

**ASCII Mockup Template**:
```
┌─────────────────────────────────────────────────────┐
│ [Page/Component Title]                              │
├─────────────────────────────────────────────────────┤
│ [Main content area with user interactions]         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Sub-component or form element]                 │ │
│ │ [Input field] [Button] [Feedback area]          │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ [Action buttons and navigation]                     │
└─────────────────────────────────────────────────────┘
```

### Step 5: Technical Implementation Guidance
**Goal**: Provide development teams with implementation direction

**Required Elements**:
- API endpoint specifications
- Database schema changes
- Key algorithms or business logic
- Integration requirements
- Performance considerations

**API Specification Template**:
```http
POST /api/v1/[endpoint]
Content-Type: application/json

{
    "parameter": "value",
    "options": {...}
}

Response 200 OK:
{
    "result": "success",
    "data": {...}
}
```

### Step 6: Success Metrics Definition
**Goal**: Establish measurable outcomes for feature validation

**Metric Categories**:

#### Quantitative KPIs
- Performance metrics (speed, accuracy, uptime)
- User adoption and engagement rates
- Business impact (revenue, cost savings)
- Quality indicators (error rates, completion rates)

#### Qualitative Indicators
- User satisfaction feedback
- Support ticket reduction
- Professional/certification value
- Competitive advantage

**Metrics Template**:
```markdown
### Quantitative KPIs
- **[Metric Name]**: [Target Value] ([Measurement Method])
- **User Adoption**: X% ([Tracking Mechanism])
- **Performance**: <X seconds ([Benchmark Scenario])

### Qualitative Indicators  
- **User Feedback**: "[Expected Response]" (NPS >X)
- **Business Value**: "[Strategic Impact]"
```

## Quality Assurance Checklist

### Before Story Completion ✅

#### User Value Validation
- [ ] Delivers complete end-to-end user value
- [ ] Can be demonstrated through UI interactions
- [ ] Provides measurable business benefit
- [ ] Is deliverable independently of other stories

#### Acceptance Criteria Quality
- [ ] All criteria are testable (not subjective)
- [ ] Include specific user interactions
- [ ] Cover primary workflow and edge cases
- [ ] Specify measurable success targets

#### Implementation Clarity
- [ ] Technical requirements clearly specified
- [ ] API contracts and database changes defined
- [ ] Dependencies and integration points identified
- [ ] Performance and quality targets established

#### Documentation Completeness
- [ ] UI/UX mockups provided for key interfaces
- [ ] Success metrics defined with measurement methods
- [ ] Risk assessment and mitigation strategies included
- [ ] Cross-references to related stories and technical docs

## Common Pitfalls to Avoid

### ❌ Anti-Patterns

#### Vague Requirements
```
❌ "The system should be fast"
✅ "Processing completes within 30 seconds for 60-minute sessions"
```

#### Technical Implementation Focus
```
❌ "Implement LLM integration service"  
✅ "As a coach, I want automatic transcript correction so I can focus on insights"
```

#### Missing User Context
```
❌ "Add competency scoring feature"
✅ "As a coach seeking ICF certification, I want competency analysis so I can track progress"
```

#### Subjective Acceptance Criteria
```
❌ "Interface should be user-friendly"
✅ "90% of users complete the workflow without help documentation"
```

### ✅ Best Practices

#### User-Centric Language
- Start with user needs and pain points
- Focus on business value and outcomes
- Use personas and specific user scenarios
- Emphasize the "why" behind features

#### Measurable Success
- Define specific, quantifiable targets
- Include both leading and lagging indicators
- Establish baseline measurements where possible
- Plan for success metric collection and analysis

#### Progressive Complexity
- Start with simple, foundational features
- Build complexity incrementally
- Ensure each story enables subsequent stories
- Validate assumptions before advancing

## Templates and Examples

### Epic Template
See: `docs/features/ai_coach/epics/epic1-transcript-enhancement/README.md`

### User Story Template  
See: `docs/features/ai_coach/epics/epic1-transcript-enhancement/user-story-1.1-auto-correct.md`

### Implementation Roadmap Template
See: `docs/features/ai_coach/implementation-roadmap.md`

## Subagent Interaction Guidelines

### When to Escalate
- Requirements are ambiguous or conflicting
- Technical feasibility is uncertain
- Business value proposition is unclear
- Cross-team dependencies are complex

### Collaboration Points
- **feature-analyst** + **user-story-designer**: Epic breakdown and story detail
- **user-story-designer** + **api-designer**: Technical implementation specification
- **product-planner** + **requirements-analyst**: Roadmap validation and prioritization

### Output Standards
- All deliverables follow established templates
- Cross-references are maintained between related documents
- Success metrics are measurable and trackable
- Documentation is ready for development team consumption

---

This guide ensures consistent, high-quality user story creation that delivers measurable user value while providing clear development guidance.