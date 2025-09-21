# Project Structure - Clean Architecture Implementation

## Clean Architecture Layout

Following Clean Architecture and PEP 518 principles:

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
│       ├── core/             # 🏛️ CORE BUSINESS LOGIC (Clean Architecture)
│       │   ├── services/     # 📋 Use Cases - PURE business logic
│       │   ├── models/       # 🎯 Domain models (eventually pure domain)
│       │   └── repositories/ # 🔌 Repository ports/interfaces
│       │       └── ports.py  # Protocol definitions for data access
│       ├── infrastructure/   # 🔧 INFRASTRUCTURE LAYER (Clean Architecture)
│       │   ├── db/           # Database-specific implementations
│       │   │   ├── models/   # SQLAlchemy ORM models (future)
│       │   │   ├── repositories/ # SQLAlchemy repository implementations
│       │   │   └── session.py    # Database session factory
│       │   ├── memory_repositories.py # In-memory repos for testing
│       │   ├── factories.py  # Dependency injection factories
│       │   ├── http/         # HTTP client adapters
│       │   └── cache/        # Redis/cache adapters
│       ├── api/              # 🌐 API INTERFACE LAYER (Clean Architecture)
│       │   ├── controllers/  # HTTP request handlers
│       │   ├── schemas/      # Pydantic I/O models (boundary only)
│       │   └── middleware/   # FastAPI middleware
│       ├── tasks/            # Celery background tasks
│       └── utils/            # Common utilities and helpers
├── tests/                    # Test suite (separate from src)
│   ├── README.md             # Testing overview and structure
│   ├── conftest.py           # pytest configuration
│   ├── fixtures/             # Test data and mocks
│   ├── unit/                 # Fast, isolated unit tests (use in-memory repos)
│   ├── integration/          # Service integration tests
│   ├── api/                  # API endpoint tests
│   ├── architecture/         # Architecture compliance tests
│   ├── e2e/                  # End-to-end workflow tests
│   │   ├── requirements.txt  # Python dependencies for E2E tests
│   │   ├── test_lemur_*.py   # LeMUR optimization testing scripts
│   │   └── lemur_examples/   # Example scripts and usage patterns
│   └── performance/          # Performance benchmarks
├── tmp/                     # Temporary files and debug outputs (gitignored)
│   ├── debug_*.py           # Debug scripts (auto-cleanup)
│   └── *_results.json       # Temporary output files
├── alembic/                  # Database migrations (SQLAlchemy)
├── logs/                     # Application log files
├── examples/                 # Usage examples and tutorials
├── docs/                     # Documentation
│   ├── architecture/         # System architecture documentation
│   ├── claude/               # AI assistant configuration
│   │   └── context/          # Project context for AI assistants
│   ├── features/             # Feature documentation (in development)
│   │   └── refactor-architecture/ # Clean Architecture migration docs
│   ├── features_done/        # Completed feature documentation
│   └── deployment/          # Deployment guides and configs
├── scripts/                  # Development and maintenance scripts
│   └── check_architecture.py # Architecture compliance checker
├── terraform/               # Infrastructure as code (GCP)
├── poc-assemblyAI/          # AssemblyAI integration prototypes
├── pyproject.toml           # Modern Python project configuration (PEP 518)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example             # Environment variables template
├── .pre-commit-config.yaml  # Code quality automation
├── mypy.ini                 # Type checking configuration
├── pytest.ini              # Test runner configuration
└── Makefile                 # Development commands + architecture checks
```

## Clean Architecture Principles ✨

**🚫 CRITICAL RULES - NEVER VIOLATE**:
1. **Core Services**: ZERO SQLAlchemy imports or Session dependencies
2. **API Layer**: Only HTTP concerns, no business logic or direct DB access
3. **Repository Pattern**: All data access through repository ports
4. **Dependency Direction**: Core → Infrastructure, never the reverse

## Key Structure Benefits

1. **Clean Architecture**: Proper separation of concerns with dependency inversion
2. **Testability**: Business logic can be tested without database dependencies
3. **Maintainability**: Changes in infrastructure don't affect business logic
4. **PEP 518 Compliance**: Uses modern `pyproject.toml` and `src/` layout
5. **Package Isolation**: Prevents import issues during development
6. **Clear Separation**: Tests, docs, and source code are properly separated
7. **Type Safety**: Includes `py.typed` marker and mypy configuration
8. **Development Workflow**: Pre-commit hooks and quality tools configured

## Module Organization - Clean Architecture Layers

The `coaching_assistant` package follows Clean Architecture principles:

**🏛️ CORE LAYER** (Business Logic - Zero External Dependencies):
- **core/services/**: Use Cases - Pure business logic with repository port injection
- **core/repositories/ports.py**: Repository interface contracts (Protocols)
- **core/models/**: Domain models (gradually moving to pure domain entities)

**🔧 INFRASTRUCTURE LAYER** (External Concerns):
- **infrastructure/db/repositories/**: SQLAlchemy repository implementations
- **infrastructure/db/session.py**: Database session factory management
- **infrastructure/memory_repositories.py**: In-memory repos for unit testing
- **infrastructure/factories.py**: Dependency injection and object creation

**🌐 API LAYER** (HTTP Interface):
- **api/**: HTTP controllers - Only request/response handling
- **api/schemas/**: Pydantic models - I/O boundary only, never in core

**⚙️ SUPPORTING LAYERS**:
- **config/**: Centralized configuration with environment handling
- **tasks/**: Asynchronous background processing (Celery)
- **utils/**: Shared utilities and helper functions

## Migration Tracking

For current migration status and legacy component tracking, see:
- **Migration Status**: `@docs/features/refactor-architecture/migration-status.md`
- **Implementation Plan**: `@docs/features/refactor-architecture/README.md`

## Clean Architecture Layer Differences 🔍

**Understanding the different models and services in each layer is crucial for maintaining architectural consistency:**

### 📋 Models Comparison

**🏛️ CORE MODELS** (`src/coaching_assistant/core/models/`)
- **Purpose**: Pure domain entities representing business concepts
- **Examples**: `User`, `Session`, `Transcript`, `UsageLog`
- **Dependencies**: ZERO external dependencies - only Python standard library and domain logic
- **Characteristics**: Rich domain behavior, business rule validation, pure Python classes
- **Usage**: Used by use cases for business logic operations

**🔧 INFRASTRUCTURE ORM MODELS** (`src/coaching_assistant/infrastructure/db/models/`)
- **Purpose**: SQLAlchemy ORM entities for database persistence
- **Examples**: `UserModel`, `SessionModel`, `UsageLogModel`
- **Dependencies**: SQLAlchemy ORM, database-specific concerns
- **Characteristics**:
  - Contain `to_domain()` method to convert to core domain models
  - Contain `from_domain()` method to create from core domain models
  - Handle database-specific field mappings and relationships
- **Usage**: Used only by repository implementations for data persistence

**📁 LEGACY ROOT MODELS** (`src/coaching_assistant/models/`)
- **Purpose**: Legacy SQLAlchemy models
- **Usage**: Maintained for compatibility - see migration status documentation for transition plans

### ⚙️ Services Comparison

**🏛️ CORE SERVICES** (`src/coaching_assistant/core/services/`)
- **Purpose**: Use Cases - Pure business logic implementing application workflows
- **Examples**: `PlanRetrievalUseCase`, `SessionCreationUseCase`, `UsageTrackingUseCase`
- **Dependencies**: ONLY repository ports and domain models - NO infrastructure
- **Characteristics**:
  - 🚫 **FORBIDDEN**: SQLAlchemy imports, Session objects, direct database access
  - ✅ **ALLOWED**: Repository port injection, domain model operations
  - Single responsibility - one use case per class
- **Usage**: Injected into API controllers via dependency injection

**📁 LEGACY ROOT SERVICES** (`src/coaching_assistant/services/`)
- **Purpose**: Legacy service classes
- **Examples**: `GoogleSTT`, `TranscriptSmoother`, `BillingAnalyticsService`
- **Usage**: Maintained for compatibility - see migration status documentation for modernization plans

### 🔄 Model Transformation Flow

```
HTTP Request (Pydantic Schema)
    ↓ (API Layer converts)
Domain Model (Core)
    ↓ (Repository converts)
ORM Model (Infrastructure)
    ↓ (Database persistence)
```

**Example User Model Flow:**
1. **API receives**: Pydantic `UserCreateRequest`
2. **API converts to**: Core domain `User` model
3. **Use case processes**: Business logic with domain `User`
4. **Repository converts**: Domain `User` → ORM `UserModel`
5. **Database stores**: `UserModel` via SQLAlchemy

### 🎯 Key Guidelines for Layer Usage

**When working with models:**
- 📋 **Core domain models**: For business logic and validation
- 🔧 **ORM models**: Only in repository implementations
- 📁 **Legacy models**: Reference migration documentation for guidance

**When creating services:**
- 🏛️ **Use cases**: For new business logic - inject repository ports
- 📁 **Legacy services**: Reference migration documentation for modernization approach
- Always ensure **dependency direction**: Core ← Infrastructure

**Development Guidelines:**
1. Create new features using Clean Architecture (core/services/, infrastructure/)
2. Keep business logic pure in use cases
3. Use repository pattern for all data access
4. Follow the Critical Rules outlined above