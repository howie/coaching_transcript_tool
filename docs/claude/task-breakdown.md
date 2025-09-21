# Task Breakdown Methodology

## Breaking Down Complex Features into User Stories

When working with complex features or requirements, follow this structured approach to create clear, testable user stories:

### 1. Feature Analysis Process
```
Requirements/Feature Request
    ↓
Epic Identification (group related stories)
    ↓
User Story Creation (individual deliverable value)
    ↓
Acceptance Criteria Definition (testable conditions)
    ↓
UI/UX Specification (demonstrable interface)
    ↓
Technical Implementation Planning
```

### 2. User Story Template Structure
Use this template for consistent user story documentation:

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
- [Quantified impact on users/business]
- [Revenue/cost implications]
- [Strategic importance]

## Acceptance Criteria
### ✅ Primary Criteria
- [ ] **AC-X.Y.1**: [Testable condition]
- [ ] **AC-X.Y.2**: [User interaction requirement]

### 🔧 Technical Criteria
- [ ] **AC-X.Y.6**: [Performance requirement]
- [ ] **AC-X.Y.7**: [Integration requirement]

### 📊 Quality Criteria
- [ ] **AC-X.Y.10**: [Accuracy/success metrics]

## UI/UX Requirements
[ASCII mockups and component specifications]

## Technical Implementation
[API endpoints, database schema, algorithms]

## Success Metrics
[Quantitative KPIs and qualitative indicators]
```

### 3. Epic Organization Structure
Organize features into logical epics with clear progression:

```
docs/features/[feature-name]/
├── README.md                    # Navigation and overview
├── user-stories.md             # Consolidated user stories
├── implementation-roadmap.md   # Phased development plan
├── epics/
│   ├── epic1-[name]/
│   │   ├── README.md           # Epic overview
│   │   ├── user-story-1.1-[name].md
│   │   └── user-story-1.2-[name].md
│   └── epic2-[name]/
│       └── [similar structure]
└── technical/
    ├── workflows/              # Technical specifications
    └── [architecture docs]
```

### 4. Quality Gates for User Stories

Before considering a user story complete, ensure:

**✅ User Value**
- Delivers end-to-end value demonstrable through UI
- Can be tested independently
- Provides measurable business impact

**✅ Acceptance Criteria**
- All criteria are testable (not subjective)
- Include UI interactions and user workflows
- Cover happy path, edge cases, and error conditions

**✅ Implementation Clarity**
- Technical requirements clearly specified
- API contracts and database changes defined
- Dependencies and risks identified

**✅ Success Measurement**
- Quantitative success metrics defined
- User satisfaction indicators specified
- Business impact trackable

### 5. Subagent Delegation Guidelines

When delegating user story creation to subagents:

**For feature-analyst subagent:**
```
Please analyze [requirement/feature] and break it down into:
1. Logical epics with clear business value
2. Individual user stories within each epic
3. Epic dependency relationships
4. Implementation priority recommendations

Focus on user value delivery and ensure each story is independently testable.
```

**For user-story-designer subagent:**
```
Create detailed user story documentation for [epic/feature] including:
1. Complete acceptance criteria (primary, technical, quality)
2. UI/UX mockups with ASCII diagrams
3. Technical implementation specifications
4. Success metrics and testing scenarios

Follow the standard user story template and ensure all stories deliver end-to-end user value.
```

**For product-planner subagent:**
```
Create an implementation roadmap for [feature set] including:
1. Phase-by-phase development plan with timelines
2. Resource allocation and team requirements
3. Risk assessment and mitigation strategies
4. Business impact projections and success metrics

Consider technical dependencies and business priorities.
```

This methodology ensures consistent, high-quality feature breakdown that delivers measurable user value while maintaining technical excellence.