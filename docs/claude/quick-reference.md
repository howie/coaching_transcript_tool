# Quick Reference Guide

## Environment Configuration

### Required Environment Variables
```env
# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Authentication
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type": "service_account"...}

# STT Providers
STT_PROVIDER=google  # "google" (default) | "assemblyai"
GOOGLE_STT_MODEL=chirp_2
GOOGLE_STT_LOCATION=asia-southeast1
ASSEMBLYAI_API_KEY=your_api_key_here  # Required for AssemblyAI
```

## STT Provider Architecture

### Supported Providers
1. **Google Speech-to-Text** (Default) - chirp_2 model
2. **AssemblyAI** - Enhanced Chinese language support

### Provider Selection
- **Per-session**: `POST /sessions` with `stt_provider: "google"|"assemblyai"|"auto"`
- **Environment default**: `STT_PROVIDER` environment variable
- **Automatic fallback**: AssemblyAI → Google STT on failures

### Language Support
- **English**: Optimal diarization with `us-central1` region
- **Chinese**: Traditional Chinese output, manual role assignment available
- **Japanese**: Manual role assignment, excellent transcription quality

## Key Development Commands

### Backend (Python/FastAPI)
- `make dev-setup` - Install Python dependencies
- `make run-api` - Start API server
- `make test` - Run standalone tests (unit + db integration)
- `make test-server` - Run server-dependent tests (API/E2E)
- `make lint` - Run code linting

### Frontend (Next.js)
- `make install-frontend` - Install npm dependencies
- `make dev-frontend` - Start dev server
- `make build-frontend` - Production build
- `make deploy-frontend` - Deploy to Cloudflare

## Internationalization (i18n) Guidelines

The application uses a **modular translation system** organized by feature domain for better maintainability.

**Translation Structure:**
```
apps/web/lib/i18n/translations/
├── account.ts      # Account management
├── audio.ts        # Audio upload/processing
├── auth.ts         # Authentication
├── billing.ts      # Billing and plans
├── clients.ts      # Client management
├── common.ts       # Common UI, limits, features
├── converter.ts    # Transcript converter
├── dashboard.ts    # Dashboard
├── help.ts         # Help and support
├── landing.ts      # Landing page
├── layout.ts       # Layout components
├── menu.ts         # Navigation menus
├── nav.ts          # Navigation
├── profile.ts      # User profile
└── sessions.ts     # Session management
```

**Key points:**
- Always use `t()` function for user-facing text
- Test both Chinese and English translations
- Follow `namespace.specificFunction` naming convention (e.g., `billing.upgradePlan`, `sessions.processingCompleted`)
- Add new translations to the appropriate domain-specific file
- All translations are combined automatically in `lib/i18n/index.ts`
- See detailed guidelines: `@docs/claude/i18n.md`

## Frontend Testing Strategy

For comprehensive frontend testing strategies and best practices, see `@docs/claude/testing.md`.

**Key points:**
- Unit tests for components (Jest + React Testing Library)
- i18n testing for all translations
- Mock external APIs and contexts properly
- See detailed testing guide: `@docs/claude/testing.md`

## Task Breakdown Methodology

### Breaking Down Complex Features into User Stories

When working with complex features or requirements, follow this structured approach to create clear, testable user stories:

#### 1. Feature Analysis Process
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

#### 2. User Story Template Structure
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

#### 3. Epic Organization Structure
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

## Deployment

- **Frontend**: Auto-deploy to Cloudflare on main branch push
- **Backend**: Deploy to Render via GitHub Actions
- **Database**: Managed PostgreSQL on Render
- **Monitoring**: Render Metrics + custom logging

## Important Notes

- Use virtual environments for Python development
- Audio files auto-delete after 24 hours (GDPR compliance)
- All database migrations use consistent foreign key naming: `{referenced_table}_id`
- Follow the monorepo architecture with clear separation of concerns
- Prioritize security: never commit secrets, use environment variables
- **Session ID Types**: Be aware of Coaching Session ID vs Transcript Session ID distinction (see `@docs/claude/session-id-mapping.md`)
- **File Organization**: Store temporary debug files in `tmp/`, reusable tests in `tests/` directory
- **Documentation Organization**:
  - `docs/` - Team-shared documentation (architecture, project status, roadmaps)
  - `docs/claude/` - AI assistant-specific guidance (engineering standards, i18n, testing)
  - `docs/claude/context/` - AI contextual information (project overview, strategy)
  - `docs/architecture/` - Unified architectural documentation (system patterns, tech stack, STT)
  - `docs/lessons-learned/` - Development lessons and retrospectives
  - Avoid duplicate documentation between team and AI directories
- **Update changelog** - When making major changes, update `docs/claude/CHANGELOG.md`