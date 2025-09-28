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

# Lint and format code (ALWAYS run before committing)
uv run ruff format .       # Format all Python files
uv run ruff check . --fix  # Fix linting issues

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

## Project Structure Overview

**Clean Architecture Layout** (PEP 518 compliant):

```
coaching_transcript_tool/
├── apps/                     # Multi-app monorepo structure
│   ├── api-server/           # FastAPI backend entry point
│   ├── cli/                  # Command-line tools and utilities
│   ├── web/                  # Next.js frontend application
│   └── worker/               # Background worker services
├── src/coaching_assistant/   # 🏛️ Main Python package (Clean Architecture)
│   ├── core/                 # Business logic (use cases, domain models)
│   ├── infrastructure/       # External concerns (database, HTTP, cache)
│   ├── api/                  # HTTP interface (controllers, schemas)
│   ├── config/               # Configuration management
│   ├── tasks/                # Celery background tasks
│   └── utils/                # Common utilities
├── tests/                    # Comprehensive test suite
├── docs/                     # Documentation
└── [build/deploy configs]    # pyproject.toml, Makefile, etc.
```

**🚫 CRITICAL ARCHITECTURAL RULES**:
- Core services: ZERO SQLAlchemy imports or Session dependencies
- API layer: Only HTTP concerns, no business logic
- Repository pattern: All data access through repository ports
- Dependency direction: Core ← Infrastructure

📚 **Detailed Architecture Guide**: See `@docs/claude/architecture.md`

## Development Standards

### TDD Methodology
- Follow **Red → Green → Refactor** cycle strictly
- Write failing tests first, implement minimum code to pass
- Separate structural changes from behavioral changes
- **85% test coverage minimum** for core business logic

### Code Quality
- Use semantic, descriptive naming conventions
- Centralized configuration with environment variables
- Comprehensive logging with structured output
- Method chaining pattern for fluent interfaces

### Linting and Formatting
- **Primary Tool**: Ruff (replaces Black, isort, flake8)
- **Configuration**: See `[tool.ruff]` section in `pyproject.toml`
- **Line Length**: 88 characters (E501 ignored, handled by formatter)
- **Performance**: 30-100x faster than Black/autopep8

#### Essential Ruff Commands
```bash
# Format all Python files (ultra-fast)
uv run ruff format .

# Check for linting violations
uv run ruff check .

# Auto-fix violations where possible
uv run ruff check . --fix

# Show statistics of current issues
uv run ruff check --statistics

# Check specific rules (e.g., unused imports)
uv run ruff check --select F401

# Preview changes before applying fixes
uv run ruff check . --fix --diff
```

#### Migration Results
- **Files processed**: 300 Python files reformatted
- **E501 violations**: Reduced from 1,229 → 612 (50% improvement)
- **Processing speed**: ~0.15 seconds for entire 137k line codebase
- **Remaining E501**: Manual review needed for strings, URLs, complex expressions

#### Handling Remaining E501 Violations

**Common Patterns & Solutions**:

1. **F-strings (415 violations)**:
   ```python
   # ❌ Too long
   logger.info(f"Processing {count} items with configuration {config_name}")

   # ✅ Break into multiple lines
   logger.info(
       f"Processing {count} items with configuration {config_name}"
   )

   # ✅ Or split the f-string
   logger.info(
       f"Processing {count} items "
       f"with configuration {config_name}"
   )
   ```

2. **URLs and Database Strings**:
   ```python
   # ✅ Add noqa for legitimate cases
   DATABASE_URL = "postgresql://user:pass@host:5432/db_name"  # noqa: E501
   ```

3. **Long Comments (223 violations)**:
   ```python
   # ❌ Too long
   # This is a very long comment that explains complex business logic in detail

   # ✅ Break into multiple lines
   # This is a very long comment that explains
   # complex business logic in detail
   ```

**Priority Order**:
1. Fix f-strings in core business logic files first
2. Add `# noqa: E501` for URLs, database connections, and legitimate long strings
3. Break long comments into multiple lines
4. Review remaining violations case-by-case

**File Organization for Scripts**:
- **Temporary scripts**: Always place in `tmp/` directory
- **Reusable utilities**: Place in `scripts/` with appropriate subdirectory
- **Never place temporary files in project root**

### 🔄 CI/CD Integration

**Updated Make Commands**:
```bash
make lint    # Now uses Ruff instead of Black/flake8
```

**GitHub Actions**: Automatically updated via `make lint` integration
- CI/CD workflows use `make lint` command
- Pre-commit hooks updated to use Ruff
- No manual CI changes needed

**Pre-commit Configuration**: Updated `.pre-commit-config.yaml`
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.6
  hooks:
    - id: ruff
      args: [--fix, --exit-non-zero-on-fix]
    - id: ruff-format
```

### 🚨 CRITICAL Development Workflow
After making ANY code changes, especially lint fixes:

1. **Format and lint code**:
   ```bash
   uv run ruff format .
   uv run ruff check . --fix
   ```

2. **MANDATORY: Run tests immediately**:
   ```bash
   make test-unit          # Fast unit tests
   make test              # Full test suite
   ```

3. **Fix any test failures** before considering work complete
4. **Never skip testing** - lint fixes can introduce breaking changes

📚 **Complete Development Standards**: See `@docs/claude/development-standards.md`

## API Testing Requirements

### 🔥 MANDATORY Authentication Testing
- **NEVER ACCEPTABLE**: Claims based only on 401 responses
- **ALWAYS REQUIRED**: Test with real JWT tokens and actual data
- **Evidence-based verification**: Show complete request/response cycles

### Test Mode Verification
After any development work (including lint fixes):
```bash
# 1. Always lint and format first
uv run ruff format . && uv run ruff check . --fix

# 2. Run tests to verify no breaking changes
make test-unit

# 3. Test API server functionality
TEST_MODE=true uv run python apps/api-server/main.py
# Verify all functionality without authentication barriers
```

📚 **Complete API Standards**: See `@docs/claude/api-standards.md`

## Key References

### Essential Documentation
- **Architecture Details**: `@docs/claude/architecture.md` - Clean Architecture implementation
- **Development Standards**: `@docs/claude/development-standards.md` - TDD, code style, testing
- **API Standards**: `@docs/claude/api-standards.md` - Testing requirements, verification
- **Quick Reference**: `@docs/claude/quick-reference.md` - Commands, config, deployment

### Technical Implementation
- **i18n Guidelines**: `@docs/claude/i18n.md` - Internationalization patterns
- **Testing Strategy**: `@docs/claude/testing.md` - Frontend/backend testing approaches
- **Session ID Mapping**: `@docs/claude/session-id-mapping.md` - Critical ID distinction guide
- **Configuration**: Environment variables, STT providers, deployment settings

### Project Documentation
- **Subagents Guide**: `@docs/claude/subagents.md` - Detailed capabilities & usage
- **Changelog**: `@docs/claude/CHANGELOG.md` - Version history and releases
- **Architecture Docs**: `@docs/architecture/` - System patterns, tech stack
- **Feature Documentation**: `@docs/features/` - Current and completed features

## Important Notes

- Use virtual environments for Python development
- Audio files auto-delete after 24 hours (GDPR compliance)
- Follow monorepo architecture with clear separation of concerns
- Prioritize security: never commit secrets, use environment variables
- **Session ID Types**: Coaching Session vs Transcript Session distinction
- **File Organization**: Temporary files in `tmp/`, reusable tests in `tests/`
- **Update changelog** when making major changes

## Task Management

Use TodoWrite tool extensively for:
- Planning complex features and multi-step tasks
- Tracking progress and giving users visibility
- Breaking down larger tasks into manageable steps
- Ensuring all requirements are completed

Always mark todos as completed immediately after finishing tasks.
