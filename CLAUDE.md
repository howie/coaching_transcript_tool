# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Coaching Assistant Platform** - A comprehensive SaaS solution for ICF coaches to transcribe, analyze, and manage coaching sessions.

### Core Purpose
Transform audio recordings of coaching sessions into high-quality transcripts with speaker diarization, supporting future AI-powered coaching assessment and supervision features.

### Technology Stack
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **Deployment**: Cloudflare Workers (Frontend) + Render.com (Backend)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Task Queue**: Celery + Redis
- **STT Providers**: Google Speech-to-Text v2, AssemblyAI

## Quick Start

```bash
# Install all dependencies
make dev-setup && make install-frontend

# Start development servers
make run-api        # Backend at http://localhost:8000
make dev-frontend   # Frontend at http://localhost:3000

# Run tests
make test          # Backend tests (unit + db integration)
make test-server   # API/E2E tests (requires API server)
cd apps/web && npm test  # Frontend tests
```

## Work Modes & Subagents

### Available Agents ✅ (Invokable via Task Tool)

These agents can be directly invoked and will handle tasks autonomously:

- **Complex multi-step tasks** → `general-purpose`
- **Post-commit maintenance** → `post-commit-updater`
- **Web research and documentation** → `web-research-agent`
- **Git worktree and feature management** → `git-worktree-feature-manager`
- **Database analysis and monitoring** → `database-query-analyzer`

### Workflow Patterns 📋 (Manual Implementation)

These are structured approaches and best practices - follow the documented patterns manually or delegate to `general-purpose` agent:

**Code Quality & Testing**
- **After writing/modifying code** → Follow `@docs/claude/subagent/planned/code-reviewer.md`
- **When tests fail or errors occur** → Follow `@docs/claude/subagent/planned/debugger.md`
- **Need to add test coverage** → Follow `@docs/claude/subagent/planned/test-writer.md`
- **Analyzing production errors** → Follow `@docs/claude/subagent/planned/error-analyzer.md`

**Architecture & Design**
- **New API endpoints** → Follow `@docs/claude/subagent/planned/api-designer.md`
- **Database schema changes** → Follow `@docs/claude/subagent/planned/database-migrator.md`
- **Background job implementation** → Follow `@docs/claude/subagent/planned/celery-task-designer.md`
- **Performance issues** → Follow `@docs/claude/subagent/planned/performance-optimizer.md`

**Feature Development & Planning**
- **Breaking down complex features** → Follow `@docs/claude/subagent/planned/feature-analyst.md`
- **Creating user stories** → Follow `@docs/claude/subagent/planned/user-story-designer.md`
- **Epic planning and roadmaps** → Follow `@docs/claude/subagent/planned/product-planner.md`
- **Requirements analysis** → Follow `@docs/claude/subagent/planned/requirements-analyst.md`

**DevOps & Maintenance**
- **Before deployment** → Follow `@docs/claude/subagent/planned/security-auditor.md`
- **Container setup** → Follow `@docs/claude/subagent/planned/docker-builder.md`
- **Package updates** → Follow `@docs/claude/subagent/planned/dependency-updater.md`
- **Multi-language support** → Follow `@docs/claude/subagent/planned/i18n-translator.md`

See `@docs/claude/subagent/` for detailed agent documentation and workflow patterns.

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

## Architecture Overview

Clean Architecture implementation with PEP 518 principles. For complete details, see [`@docs/claude/project-structure.md`](docs/claude/project-structure.md).

**🚫 CRITICAL RULES - NEVER VIOLATE**:
1. **Core Services**: ZERO SQLAlchemy imports or Session dependencies
2. **API Layer**: Only HTTP concerns, no business logic or direct DB access
3. **Repository Pattern**: All data access through repository ports
4. **Dependency Direction**: Core → Infrastructure, never the reverse

### High-Level Structure
- **`apps/`** - Multi-app monorepo (api-server, web, cli, worker)
- **`src/coaching_assistant/`** - Main Python package with Clean Architecture layers
- **`core/`** - 🏛️ Pure business logic (use cases, domain models, repository ports)
- **`infrastructure/`** - 🔧 External concerns (DB, HTTP, cache adapters)
- **`api/`** - 🌐 HTTP interface (controllers, schemas, middleware)

## Development Standards

### Test-Driven Development
Follow TDD methodology strictly (Red → Green → Refactor). Complete guidelines: [`@docs/claude/tdd-methodology.md`](docs/claude/tdd-methodology.md).

### Python Code Style
- Use semantic, descriptive names
- Centralized configuration management
- Comprehensive logging with indicators
- 85% test coverage minimum

Complete standards: [`@docs/claude/python-style.md`](docs/claude/python-style.md).

### API Testing Standards
**🔥 MANDATORY**: Use real JWT tokens for ALL API testing. Never claim fixes based only on 401 responses.

Complete verification requirements: [`@docs/claude/api-testing-standards.md`](docs/claude/api-testing-standards.md).

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

## Key API Endpoints

```
Authentication:
POST /auth/google - Google SSO authentication

Sessions:
POST /sessions - Create transcription session
GET /sessions - List user sessions
GET /sessions/{id} - Get session details
POST /sessions/{id}/upload-url - Get signed upload URL
POST /sessions/{id}/start-transcription - Start processing
GET /sessions/{id}/transcript - Download transcript
PATCH /sessions/{id}/speaker-roles - Update speaker assignments

LeMUR Optimization:
POST /lemur-speaker-identification - Optimize speaker identification
POST /lemur-punctuation-optimization - Optimize punctuation
POST /session/{session_id}/lemur-speaker-identification - Database-based speaker optimization
POST /session/{session_id}/lemur-punctuation-optimization - Database-based punctuation optimization

Coaching Management:
GET /api/v1/clients - List clients
POST /api/v1/clients - Create client
GET /api/v1/coaching-sessions - List coaching sessions
POST /api/v1/coaching-sessions - Create session
```

## Plan Limitations & Features

The platform enforces different limits based on user subscription plans:

### File Size Limits
- **FREE Plan**: 60MB per file
- **STUDENT Plan**: 60MB per file
- **PRO Plan**: 200MB per file
- **COACHING_SCHOOL Plan**: 500MB per file

### Session & Transcription Limits
- **Database-driven**: All plan limits are stored in PostgreSQL and dynamically loaded
- **API Integration**: `/api/v1/plans/current` endpoint provides real-time limit information
- **Frontend Validation**: File upload component shows dynamic size limits based on user's plan
- **Backend Enforcement**: Plan validation occurs before processing to prevent overuse

### Dynamic Limit Display
The frontend automatically adapts to show the correct limits:
- AudioUploader component displays plan-specific file size limits
- Error messages include current plan context
- Billing pages show accurate feature comparisons per plan

## Documentation References

For detailed information, reference these docs:

**🏛️ Clean Architecture**:
- **Project Structure**: `@docs/claude/project-structure.md` - Complete architecture layout and patterns
- **Architecture Refactoring Plan**: `@docs/features/refactor-architecture/README.md` - Complete migration strategy
- **Architectural Rules**: `@docs/features/refactor-architecture/architectural-rules.md` - ⚠️ **CRITICAL** - Mandatory compliance rules
- **Repository Patterns**: Reference implementation in `src/coaching_assistant/infrastructure/`

**📚 Development Standards**:
- **TDD Methodology**: `@docs/claude/tdd-methodology.md` - Test-driven development workflow
- **Python Code Style**: `@docs/claude/python-style.md` - Naming, logging, quality standards
- **API Testing Standards**: `@docs/claude/api-testing-standards.md` - Authentication testing requirements
- **Task Breakdown**: `@docs/claude/task-breakdown.md` - User story and epic methodology
- **Subagents Guide**: `@docs/claude/subagents.md` - Detailed subagent capabilities & usage
- **Engineering Standards**: `@docs/claude/engineering-standards.md` - TDD, code style, quality
- **Testing**: `@docs/claude/testing.md` - Test organization, frontend/backend testing strategies
- **i18n Guidelines**: `@docs/claude/i18n.md` - Internationalization implementation and best practices

**⚙️ Technical Implementation**:
- **Configuration**: `@docs/claude/configuration.md` - Environment variables, providers
- **STT Architecture**: `@docs/architecture/stt.md` - Provider details, fallback
- **Session ID Mapping**: `@docs/claude/session-id-mapping.md` - Critical guide for Coaching vs Transcript Session IDs
- **Deployment**: `@docs/claude/deployment/*.md` - Platform-specific guides
- **API Reference**: See `/docs/api/` or OpenAPI at `/docs`
- **Changelog**: `@docs/claude/CHANGELOG.md` - Complete version history and releases

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

## Deployment

- **Frontend**: Auto-deploy to Cloudflare on main branch push
- **Backend**: Deploy to Render via GitHub Actions
- **Database**: Managed PostgreSQL on Render
- **Monitoring**: Render Metrics + custom logging

For detailed technical documentation, see `/docs/` directory.