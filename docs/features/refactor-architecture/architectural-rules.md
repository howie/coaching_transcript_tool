# Architectural Rules & Review Guidelines

## Overview

This document defines the strict architectural rules and code review guidelines for our Clean Architecture implementation. These rules ensure proper separation of concerns and maintainable, testable code.

## Architectural Boundaries

### Dependency Rules

1. **Core Layer Dependencies**
   - `core/services/` (Use Cases) → ONLY depend on `core/repositories/ports.py` and domain models
   - 🚫 **FORBIDDEN**: Direct SQLAlchemy imports, Session objects, ORM models
   - 🚫 **FORBIDDEN**: Any infrastructure dependencies (HTTP clients, external APIs)
   - ✅ **ALLOWED**: Domain models, repository ports, Python standard library

2. **API Layer Dependencies**
   - `api/` → Can depend on use cases, Pydantic schemas, but NOT infrastructure
   - 🚫 **FORBIDDEN**: Direct database session injection
   - 🚫 **FORBIDDEN**: Direct ORM model usage
   - ✅ **ALLOWED**: FastAPI, Pydantic, dependency injection of use cases

3. **Infrastructure Layer Dependencies**
   - `infrastructure/` → Can depend on external libraries, implements ports
   - ✅ **ALLOWED**: SQLAlchemy, Redis, HTTP clients, any external dependency
   - ✅ **ALLOWED**: Repository port implementations

## Code Review Checklist

### Critical Violations (❌ Reject Immediately)

```bash
# These patterns should NEVER appear in core/services/
grep -r "from sqlalchemy" src/coaching_assistant/core/services/
grep -r "Session" src/coaching_assistant/core/services/  
grep -r "\.query\(" src/coaching_assistant/core/services/
grep -r "\.filter\(" src/coaching_assistant/core/services/
grep -r "\.commit\(\)" src/coaching_assistant/core/services/
```

- [ ] **No SQLAlchemy imports** in `core/services/*`
- [ ] **No Session objects** passed to use cases
- [ ] **No ORM queries** in business logic
- [ ] **No database commits** in use cases (handled by repositories)
- [ ] **No external API calls** directly from use cases

### API Layer Review (🔍 Required)

- [ ] Controllers only handle HTTP concerns (request/response)
- [ ] Pydantic schemas converted to DTOs at boundary
- [ ] No business logic in API endpoints
- [ ] All use cases injected via dependency injection
- [ ] Error handling converts domain exceptions to HTTP responses

### Repository Review (🔍 Required)

- [ ] All repositories implement their respective port interface
- [ ] SQLAlchemy repositories handle all ORM concerns
- [ ] In-memory repositories provided for testing
- [ ] Repository exceptions properly handled and converted
- [ ] No business logic in repository implementations

### Use Case Review (🔍 Required)

- [ ] Single responsibility principle followed
- [ ] Clear input/output types defined
- [ ] Business rules enforced within use case
- [ ] Repository dependencies injected via constructor
- [ ] No infrastructure concerns leaked

## File Organization Rules

### Directory Structure Enforcement

```
src/coaching_assistant/
├── core/
│   ├── services/          # Use Cases - PURE business logic
│   ├── repositories/      # Port interfaces ONLY
│   │   └── ports.py       # Repository contracts
│   └── models/            # Domain models (eventually)
├── infrastructure/
│   ├── db/
│   │   ├── models/        # ORM models (future)
│   │   ├── repositories/  # SQLAlchemy implementations
│   │   └── session.py     # Database session management
│   ├── memory_repositories.py  # In-memory test implementations
│   └── factories.py       # Dependency injection factories
└── api/                   # HTTP interface layer
```

### Naming Conventions

- **Use Cases**: End with `UseCase` (e.g., `CreateUsageLogUseCase`)
- **Repositories**: End with `Repository` (e.g., `SQLAlchemyUserRepository`)
- **Ports**: End with `Port` (e.g., `UserRepoPort`)
- **Factories**: End with `Factory` (e.g., `UsageTrackingServiceFactory`)

## Testing Requirements

### Unit Test Rules

1. **Use Case Tests** → MUST use in-memory repositories
2. **Repository Tests** → Can use test database OR in-memory
3. **API Tests** → Integration tests with real dependencies
4. **No Database** → In unit tests for business logic

### Test Structure Example

```python
# ✅ GOOD - Use case test with in-memory repos
def test_create_usage_log_use_case():
    user_repo = create_in_memory_user_repository()
    usage_log_repo = create_in_memory_usage_log_repository()
    session_repo = create_in_memory_session_repository()
    
    use_case = CreateUsageLogUseCase(
        user_repo=user_repo,
        usage_log_repo=usage_log_repo,
        session_repo=session_repo,
    )
    
    # Test business logic without database

# ❌ BAD - Direct database dependency in unit test
def test_create_usage_log_with_db(db_session):
    service = UsageTrackingService(db_session)  # Violates isolation
```

## Migration Guidelines

### Phase-by-Phase Rules

**Phase 1** (Current):
- ✅ Create ports and infrastructure
- ✅ Migrate one service as pilot
- 🚫 Do not change existing API endpoints yet

**Phase 2** (Next):
- ✅ Update API endpoints to use factories
- ✅ Remove direct Session dependencies
- 🚫 Do not change model imports yet

**Phase 3** (Future):
- ✅ Move ORM models to infrastructure
- ✅ Create pure domain models
- ✅ Complete separation

### Backward Compatibility

During migration, maintain backward compatibility:

```python
# ✅ GOOD - Compatibility wrapper during migration
def get_usage_tracking_service(db_session: Session) -> CreateUsageLogUseCase:
    """Legacy compatibility function."""
    return UsageTrackingServiceFactory.create_usage_log_use_case(db_session)
```

## Code Quality Gates

### Pre-commit Hooks

```bash
# Add these checks to .pre-commit-config.yaml
- repo: local
  hooks:
  - id: architecture-check
    name: Architecture boundary check
    entry: scripts/check_architecture.py
    language: python
    files: ^src/coaching_assistant/(core|api|infrastructure)/
```

### CI/CD Pipeline Checks

```bash
# Architecture validation in CI
make architecture-check
make test-unit  # Must pass without database
make test-integration  # With database dependencies
```

## Violation Examples

### ❌ BAD Examples

```python
# VIOLATION: SQLAlchemy in use case
class CreateUsageLogUseCase:
    def __init__(self, db: Session):  # ❌ Direct Session dependency
        self.db = db
    
    def execute(self, session_data):
        user = self.db.query(User).filter_by(id=user_id).first()  # ❌ Direct ORM

# VIOLATION: Business logic in API controller
@router.post("/usage")
def create_usage_log(request: UsageRequest, db: Session = Depends(get_db)):
    if request.duration > plan_limits[user.plan]:  # ❌ Business logic in API
        raise HTTPException(status_code=400, detail="Limit exceeded")
    
    user = db.query(User).filter_by(id=request.user_id).first()  # ❌ Direct DB query
```

### ✅ GOOD Examples

```python
# CORRECT: Clean use case with repository injection
class CreateUsageLogUseCase:
    def __init__(self, user_repo: UserRepoPort, usage_log_repo: UsageLogRepoPort):
        self.user_repo = user_repo  # ✅ Port dependency
        self.usage_log_repo = usage_log_repo
    
    def execute(self, session_data):
        user = self.user_repo.get_by_id(user_id)  # ✅ Through repository

# CORRECT: Clean API controller
@router.post("/usage")
def create_usage_log(
    request: UsageRequest, 
    use_case: CreateUsageLogUseCase = Depends(get_usage_log_use_case)
):
    try:
        result = use_case.execute(request)  # ✅ Delegate to use case
        return UsageResponse.from_domain(result)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Review Process

### Pull Request Template

```markdown
## Architecture Compliance ✅

- [ ] Core services have no SQLAlchemy imports
- [ ] API endpoints use dependency injection
- [ ] All database operations go through repositories
- [ ] Unit tests use in-memory repositories
- [ ] No business logic in API controllers
- [ ] Repository interfaces properly implemented

## Migration Checklist

- [ ] Backward compatibility maintained
- [ ] Existing tests still pass
- [ ] New tests added for use cases
- [ ] Documentation updated
```

### Automated Checks

```python
# scripts/check_architecture.py - Run in CI
import ast
import sys
from pathlib import Path

def check_core_dependencies():
    """Ensure core services have no SQLAlchemy imports."""
    core_services = Path("src/coaching_assistant/core/services").glob("*.py")
    violations = []
    
    for file_path in core_services:
        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "sqlalchemy" in node.module:
                    violations.append(f"{file_path}:{node.lineno}")
    
    if violations:
        print("❌ Architecture violations found:")
        for violation in violations:
            print(f"  {violation}")
        sys.exit(1)
    
    print("✅ Architecture compliance verified")

if __name__ == "__main__":
    check_core_dependencies()
```

## Enforcement Tools

### Makefile Targets

```makefile
# Add to Makefile
.PHONY: architecture-check
architecture-check:
	@echo "🔍 Checking architecture compliance..."
	@python scripts/check_architecture.py
	@echo "✅ Architecture rules verified"

.PHONY: test-architecture
test-architecture:
	@echo "🧪 Running architecture tests..."
	@pytest tests/architecture/ -v
	@echo "✅ Architecture tests passed"
```

These rules ensure we maintain clean, testable, and maintainable architecture throughout the codebase evolution.