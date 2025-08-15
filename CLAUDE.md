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
make test          # Backend tests
cd apps/web && npm test  # Frontend tests
```

## Work Modes & Subagents

Delegate specialized tasks to appropriate subagents:

### Code Quality & Testing
- **After writing/modifying code** → `code-reviewer`
- **When tests fail or errors occur** → `debugger`  
- **Need to add test coverage** → `test-writer`
- **Analyzing production errors** → `error-analyzer`

### Architecture & Design
- **New API endpoints** → `api-designer`
- **Database schema changes** → `database-migrator`
- **Background job implementation** → `celery-task-designer`
- **Performance issues** → `performance-optimizer`

### DevOps & Maintenance
- **Before deployment** → `security-auditor`
- **Container setup** → `docker-builder`
- **Package updates** → `dependency-updater`
- **Multi-language support** → `i18n-translator`

### General
- **Complex multi-step tasks** → `general-purpose`
- **Post-commit tasks** → `post-commit-updater`

See `@docs/claude/subagents.md` for detailed capabilities and usage patterns.

## Key Development Commands

### Backend (Python/FastAPI)
- `make dev-setup` - Install Python dependencies
- `make run-api` - Start API server
- `make test` - Run pytest suite
- `make lint` - Run code linting

### Frontend (Next.js)
- `make install-frontend` - Install npm dependencies  
- `make dev-frontend` - Start dev server
- `make build-frontend` - Production build
- `make deploy-frontend` - Deploy to Cloudflare

## Project Structure

**Standard Python Project Layout** (following PEP 518 and community best practices):

```
coaching_transcript_tool/
├── apps/                     # Multi-app monorepo structure
│   ├── api-server/           # FastAPI backend entry point
│   ├── cli/                  # Command-line tools and utilities
│   ├── web/                  # Next.js frontend application
│   │   ├── app/              # Next.js 14 App Router pages
│   │   ├── components/       # Reusable React components
│   │   ├── contexts/         # React contexts (auth, i18n, theme)
│   │   ├── hooks/            # Custom React hooks
│   │   └── lib/              # Frontend utilities and API client
│   └── worker/               # Background worker services
├── src/                      # Python source code (PEP 518 src layout)
│   └── coaching_assistant/   # Main Python package
│       ├── __init__.py       # Package initialization
│       ├── __main__.py       # CLI entry point (python -m coaching_assistant)
│       ├── py.typed          # Type marker file for mypy
│       ├── version.py        # Version information
│       ├── exceptions.py     # Custom exceptions
│       ├── constants.py      # Application constants
│       ├── config/           # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py   # Main configuration class
│       │   ├── environment.py # Environment variable handling
│       │   └── logging_config.py # Logging configuration
│       ├── core/             # Core business logic
│       │   ├── services/     # Business logic layer
│       │   ├── models/       # SQLAlchemy database models
│       │   └── repositories/ # Data access abstraction layer
│       ├── api/              # FastAPI route handlers
│       ├── tasks/            # Celery background tasks
│       └── utils/            # Common utilities and helpers
├── tests/                    # Test suite (separate from src)
│   ├── conftest.py           # pytest configuration
│   ├── fixtures/             # Test data and mocks
│   ├── unit/                 # Fast, isolated unit tests
│   ├── integration/          # Service integration tests
│   ├── e2e/                  # End-to-end workflow tests
│   └── performance/          # Performance benchmarks
├── alembic/                  # Database migrations (SQLAlchemy)
├── logs/                     # Application log files
├── examples/                 # Usage examples and tutorials
├── docs/                     # Documentation
│   ├── features/             # Feature documentation (in development)
│   ├── features_done/        # Completed feature documentation
│   └── deployment/          # Deployment guides and configs
├── scripts/                  # Development and maintenance scripts
├── terraform/               # Infrastructure as code (GCP)
├── memory-bank/             # Project context for AI assistants
├── poc-assemblyAI/          # AssemblyAI integration prototypes
├── pyproject.toml           # Modern Python project configuration (PEP 518)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example             # Environment variables template
├── .pre-commit-config.yaml  # Code quality automation
├── mypy.ini                 # Type checking configuration
├── pytest.ini              # Test runner configuration
└── Makefile                 # Development commands
```

### Key Structure Benefits

1. **PEP 518 Compliance**: Uses modern `pyproject.toml` and `src/` layout
2. **Package Isolation**: Prevents import issues during development
3. **Clear Separation**: Tests, docs, and source code are properly separated
4. **Type Safety**: Includes `py.typed` marker and mypy configuration
5. **Development Workflow**: Pre-commit hooks and quality tools configured

### Module Organization

The `coaching_assistant` package follows layered architecture:

- **config/**: Centralized configuration with environment handling
- **core/services/**: Business logic and domain services
- **core/models/**: Database models and domain entities
- **core/repositories/**: Data access abstraction layer
- **api/**: HTTP request handlers and routing
- **tasks/**: Asynchronous background processing
- **utils/**: Shared utilities and helper functions

**Note**: This structure is planned for implementation. See `docs/refactor-new-claude-structure.md` for detailed migration plan.

## Development Methodology: Test-Driven Development (TDD)

### ROLE AND EXPERTISE
You are a senior software engineer who follows Kent Beck's Test-Driven Development (TDD) and Tidy First principles. Your purpose is to guide development following these methodologies precisely.

### CORE DEVELOPMENT PRINCIPLES
- Always follow the TDD cycle: **Red → Green → Refactor**
- Write the simplest failing test first
- Implement the minimum code needed to make tests pass
- Refactor only after tests are passing
- Follow Beck's "Tidy First" approach by separating structural changes from behavioral changes
- Maintain high code quality throughout development

### TDD METHODOLOGY GUIDANCE
1. Start by writing a failing test that defines a small increment of functionality
2. Use meaningful test names that describe behavior (e.g., "shouldSumTwoPositiveNumbers")
3. Make test failures clear and informative
4. Write just enough code to make the test pass - no more
5. Once tests pass, consider if refactoring is needed
6. Repeat the cycle for new functionality

**When fixing a defect:**
1. First write an API-level failing test
2. Then write the smallest possible test that replicates the problem
3. Get both tests to pass

### TIDY FIRST APPROACH
Separate all changes into two distinct types:

**STRUCTURAL CHANGES**: Rearranging code without changing behavior (renaming, extracting methods, moving code)
**BEHAVIORAL CHANGES**: Adding or modifying actual functionality

- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

### COMMIT DISCIPLINE
Only commit when:
- ALL tests are passing
- ALL compiler/linter warnings have been resolved
- The change represents a single logical unit of work
- Commit messages clearly state whether the commit contains structural or behavioral changes
- Use small, frequent commits rather than large, infrequent ones

### CODE QUALITY STANDARDS
- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects
- Use the simplest solution that could possibly work

### REFACTORING GUIDELINES
- Refactor only when tests are passing (in the "Green" phase)
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

### EXAMPLE WORKFLOW
When approaching a new feature:

1. Write a simple failing test for a small part of the feature
2. Implement the bare minimum to make it pass
3. Run tests to confirm they pass (Green)
4. Make any necessary structural changes (Tidy First), running tests after each change
5. Commit structural changes separately
6. Add another test for the next small increment of functionality
7. Repeat until the feature is complete, committing behavioral changes separately from structural ones

**Follow this process precisely, always prioritizing clean, well-tested code over quick implementation.**

Always write one test at a time, make it run, then improve structure. Always run all the tests (except long-running tests) each time.

## Python Code Style & Standards

### Core Requirements
- **Python Compatibility**: Python 3.11+ (primary), test on 3.12 when possible
- **Framework**: FastAPI for backend APIs (established choice)
- **HTTP Libraries**: Use `httpx` for async operations, `requests` for simple sync calls
- **CLI Arguments**: Use `argparse` or `click` with standard format (`--option value` or `--option=value`)

### Naming Conventions
- **Use highly semantic and descriptive names** for classes, functions, and parameters
- Prefer longer, clear names over abbreviated ones
- Examples: `TranscriptionProcessingService` vs `TPS`, `analyze_speaker_segments()` vs `analyze()`

### Configuration Management
- **Centralized configuration** - avoid scattered settings across individual classes
- Use environment variables for deployment-specific settings
- Create configuration classes with validation
- Example pattern:
  ```python
  from pydantic import BaseSettings
  
  class Settings(BaseSettings):
      database_url: str
      redis_url: str
      stt_provider: str = "google"
      
      class Config:
          env_file = ".env"
  ```

### Method Chaining Pattern
- **All setter methods must return `self`** to support method chaining
- Use for configuration builders and fluent interfaces
- Example:
  ```python
  class TranscriptionBuilder:
      def set_language(self, lang: str) -> 'TranscriptionBuilder':
          self.language = lang
          return self
      
      def set_provider(self, provider: str) -> 'TranscriptionBuilder':
          self.provider = provider
          return self
  ```

### Logging Standards
Use comprehensive logging with structured output and clear indicators:

```python
import logging
import sys
from datetime import datetime

def setup_logging(debug_mode=False):
    log_level = logging.DEBUG if debug_mode else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    return logging.getLogger(__name__)

# Usage with clear indicators
logger = setup_logging()
logger.info("🚀 Application startup initiated")
logger.info("📋 Loading configuration...")
logger.warning("⚠️  Potential issue detected")
logger.error("❌ Operation failed: detailed error")
logger.info("✅ Operation completed successfully")
logger.info("🏁 Application finished")
```

**All important execution steps must include logging:**
- 📋 Configuration loading and validation
- 🔗 External service connections (STT providers, database)
- 📊 Data processing progress (transcription status)
- ⏱️ Performance statistics
- 🔍 Debug information (when debug mode enabled)
- ⚠️ Warning messages
- ❌ Error handling with context
- ✅ Success confirmations
- 📈 Execution result statistics

### Documentation Requirements
- **Every module must include usage examples** in docstrings or README
- **All public functions require docstrings** with examples
- **Create README.md files** for major components explaining "how to use"
- **Include type hints** for all function parameters and return values

### Code Quality Tools
Use these tools for consistent code quality:

```bash
# Code formatting
black .                    # Auto-format code
isort .                    # Sort imports

# Code analysis  
flake8 .                   # Syntax and style checking
mypy .                     # Type checking
pytest --cov=src --cov-report=html  # Testing with coverage

# Pre-commit hooks
pre-commit install         # Set up automated checks
```

**Quality Targets:**
- **Test coverage**: 85% minimum for core-logic package
- **Type coverage**: 90% minimum with mypy
- **No flake8 warnings** in production code
- **All imports sorted** with isort

## Testing Philosophy

- Follow TDD methodology strictly (Red → Green → Refactor)
- Use pytest for backend, Jest for frontend
- Mock external services in tests (STT providers, databases)
- **Maintain 85% coverage minimum** for core-logic package (upgraded from 70%)
- Write tests that describe behavior, not implementation
- Use meaningful test names that explain the expected behavior

### Test Organization
```
tests/
├── unit/                  # Fast, isolated tests
├── integration/           # Service integration tests  
├── e2e/                   # End-to-end workflow tests
├── fixtures/              # Test data and mocks
└── performance/           # Performance benchmarks
```

### Test Requirements
- **All test files must be comprehensive** and test edge cases
- **Mock external dependencies** (Google STT, AssemblyAI, Redis, PostgreSQL)
- **Use fixtures** for common test data setup
- **Include performance tests** for critical paths
- **Test error conditions** and recovery scenarios

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

Coaching Management:
GET /api/v1/clients - List clients
POST /api/v1/clients - Create client
GET /api/v1/coaching-sessions - List coaching sessions
POST /api/v1/coaching-sessions - Create session
```

## Documentation Pointers

For detailed information, reference these docs:

- **Subagents Guide**: `@docs/claude/subagents.md` - Detailed subagent capabilities & usage
- **Engineering Standards**: `@docs/claude/engineering-standards.md` - TDD, code style, quality
- **Testing**: `@docs/claude/testing.md` - Test organization, coverage requirements
- **Configuration**: `@docs/claude/configuration.md` - Environment variables, providers
- **STT Architecture**: `@docs/claude/architecture/stt.md` - Provider details, fallback
- **Deployment**: `@docs/claude/deployment/*.md` - Platform-specific guides
- **API Reference**: See `/docs/api/` or OpenAPI at `/docs`
- **Changelog**: `@docs/claude/CHANGELOG.md` - Complete version history and releases

## Important Notes

- Use virtual environments for Python development
- Audio files auto-delete after 24 hours (GDPR compliance)
- All database migrations use consistent foreign key naming: `{referenced_table}_id`
- Follow the monorepo architecture with clear separation of concerns
- Prioritize security: never commit secrets, use environment variables
- **Update changelog** - When making major changes, update `docs/claude/CHANGELOG.md`

## Deployment

- **Frontend**: Auto-deploy to Cloudflare on main branch push
- **Backend**: Deploy to Render via GitHub Actions
- **Database**: Managed PostgreSQL on Render
- **Monitoring**: Render Metrics + custom logging

For detailed technical documentation, see `/docs/` directory.