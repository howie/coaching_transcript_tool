# Clean Architecture Migration Patterns

## Overview

This guide documents proven patterns and lessons learned from migrating to Clean Architecture. These patterns help avoid common pitfalls and ensure smooth transitions.

## Mixed Model Strategy

### The Problem

Domain models and Infrastructure models serve different purposes but use similar names, causing confusion and runtime errors.

**Symptoms**:
- `ValidationError: Input should be 'student' [type=enum, input_value=<UserPlan.STUDENT: 'student'>]`
- SQLAlchemy operations failing with domain models
- Type mismatches between layers

### The Solution: Explicit Dual Imports

Use explicit aliases to distinguish between domain and infrastructure models:

```python
# ✅ Clear separation with explicit aliases
from ...core.models.user import User as DomainUser, UserPlan  # Business logic
from ...models.user import User  # SQLAlchemy queries only

# SQLAlchemy operations use infrastructure model
stmt = select(User).where(User.email == email)
result = await db.execute(stmt)
user = result.scalar_one_or_none()

# Business logic uses domain model
domain_user = DomainUser(
    id=user.id,
    email=user.email,
    plan=UserPlan(user.plan)  # Convert infrastructure enum
)
```

**Key Rules**:
1. **Infrastructure Models**: Use for SQLAlchemy queries and ORM operations
2. **Domain Models**: Use for business logic and use cases
3. **Explicit Aliases**: Always use `DomainUser` vs `User` to prevent confusion
4. **Layer Boundary**: Convert at repository layer, not in use cases

## Enum Value Extraction at Boundaries

### The Problem

Pydantic models expect enum string values, but receive enum object instances from infrastructure layer.

```python
# ❌ This fails
return UserProfileResponse(
    plan=current_user.plan,  # <UserPlan.STUDENT: 'student'>
    # Pydantic expects: 'student'
)
```

### The Solution: Value Extraction

Always extract `.value` when crossing architectural boundaries:

```python
# ✅ Extract enum values at API boundary
return UserProfileResponse(
    plan=current_user.plan.value if hasattr(current_user.plan, 'value') else current_user.plan,
    subscription_status=current_user.subscription_status.value,
)
```

**Pattern for API Responses**:
```python
def _to_api_response(domain_obj):
    """Convert domain object to API response format."""
    return {
        "id": domain_obj.id,
        "status": domain_obj.status.value,  # Extract enum value
        "type": domain_obj.type.value if domain_obj.type else None,  # Handle None
    }
```

## Repository Pattern for Testability

### In-Memory Repositories for Unit Tests

One of the biggest benefits of Clean Architecture is fast, isolated unit testing.

**Before (Direct Database Access)**:
```python
def test_session_creation():
    # Requires real database, slow, stateful
    db = TestingSessionLocal()
    user = User(email="test@example.com")
    db.add(user)
    db.commit()

    service = SessionService(db)
    result = service.create_session(user.id)

    assert result.success
```

**After (Repository Pattern)**:
```python
def test_session_creation():
    # Fast, no database, isolated
    user_repo = InMemoryUserRepository([test_user])
    session_repo = InMemorySessionRepository()

    use_case = SessionCreationUseCase(session_repo, user_repo)
    result = use_case.execute(user_id=test_user.id, title="Test Session")

    assert result.success
    assert session_repo.sessions[0].title == "Test Session"
```

**Benefits**:
- ⚡ **Speed**: Tests run in milliseconds, not seconds
- 🔒 **Reliability**: No database state dependencies between tests
- 🎯 **Clarity**: Test failures clearly indicate business logic issues
- 🧪 **Isolation**: Each test has independent data

### In-Memory Repository Template

```python
class InMemoryUserRepository(UserRepositoryPort):
    """In-memory user repository for testing."""

    def __init__(self, initial_users: List[DomainUser] = None):
        self.users = {u.id: u for u in (initial_users or [])}

    async def get_by_id(self, user_id: str) -> Optional[DomainUser]:
        return self.users.get(user_id)

    async def save(self, user: DomainUser) -> DomainUser:
        self.users[user.id] = user
        return user

    async def delete(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
```

## Gradual Migration Strategy

### Don't Do "Big Bang" Migrations

**❌ Risky Approach**: Replace all models at once
```python
# Trying to change everything simultaneously
- from ...models.user import User
+ from ...core.models.user import User  # Breaks everything!
```

**✅ Safe Approach**: Gradual transition with compatibility layers

### The Five-Phase Migration Pattern

#### Phase 1: Create New Interface
```python
# Define repository port
class UserRepositoryPort(Protocol):
    async def get_by_id(self, user_id: str) -> Optional[DomainUser]: ...
    async def save(self, user: DomainUser) -> DomainUser: ...
```

#### Phase 2: Implement Bridge with Legacy Models
```python
# Bridge implementation using legacy infrastructure
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[DomainUser]:
        # Use legacy infrastructure model for query
        from ...models.user import User as LegacyUser
        user = self.db.query(LegacyUser).filter_by(id=user_id).first()

        if not user:
            return None

        # Convert to domain model
        return self._to_domain(user)

    def _to_domain(self, legacy_user) -> DomainUser:
        """Manual conversion from legacy to domain model."""
        return DomainUser(
            id=legacy_user.id,
            email=legacy_user.email,
            plan=UserPlan(legacy_user.plan),  # Handle enum conversion
            # ... other fields
        )
```

#### Phase 3: Migrate Use Cases
```python
# Update use cases to use injected dependencies
class SessionCreationUseCase:
    def __init__(
        self,
        session_repo: SessionRepositoryPort,
        user_repo: UserRepositoryPort  # Injected dependency
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
```

#### Phase 4: Update API Endpoints
```python
# Use dependency injection
@router.post("/sessions")
async def create_session(
    data: SessionCreateRequest,
    use_case: SessionCreationUseCase = Depends(get_session_creation_use_case)
):
    result = await use_case.execute(data)
    return result
```

#### Phase 5: Replace Implementation (When Stable)
Only after Phases 1-4 are stable and tested, replace the bridge with pure implementation.

### Key Insight
**Temporary compatibility layers are worth the complexity for system stability.**

## Data Format Evolution

### Legacy Data Format Handling

When migrating, old data formats must be handled gracefully.

**Problem**: Enum values stored as strings in database, but code expects enum instances.

```python
# Database has: plan = "STUDENT" (string)
# Code expects: plan = UserPlan.STUDENT (enum)
```

**Solution**: Robust conversion in repository layer

```python
def _convert_plan_enum(self, stored_value) -> UserPlan:
    """Handle both legacy string and enum formats."""
    if isinstance(stored_value, str):
        try:
            return UserPlan(stored_value)  # String → Enum conversion
        except ValueError:
            logger.warning(f"Unknown plan value: {stored_value}, defaulting to FREE")
            return UserPlan.FREE

    if isinstance(stored_value, UserPlan):
        return stored_value  # Already proper enum

    # Handle None or unexpected types
    return UserPlan.FREE
```

**Key Principles**:
1. **Defensive Conversion**: Handle multiple input formats
2. **Repository Responsibility**: Data format conversion belongs in infrastructure layer
3. **Backward Compatibility**: New code must handle old data indefinitely
4. **Graceful Degradation**: Provide sensible defaults for unknown values

## Import Naming Discipline

### The Problem: Name Collisions

```python
# ❌ Ambiguous imports causing confusion
from sqlalchemy.orm import Session  # Database session
from coaching_assistant.core.models.transcript import Session  # Domain model
# Which Session is which?
```

### The Solution: Explicit Aliases

```python
# ✅ Clear, unambiguous imports
from sqlalchemy.orm import Session as SQLAlchemySession
from coaching_assistant.core.models.transcript import Session as TranscriptionSession

def create_transcript(
    db: SQLAlchemySession,  # Clear: database session
    session: TranscriptionSession  # Clear: domain model
):
    pass
```

**Naming Conventions**:
- `SQLAlchemySession` / `DBSession` for database sessions
- `TranscriptionSession` / `CoachingSession` for domain sessions
- `DomainUser` / `UserDomain` when legacy `User` exists
- `InfrastructureModel` prefix for legacy models during migration

## Exception Handling Across Layers

### Domain Exceptions

Define business rule violations as domain exceptions:

```python
# src/coaching_assistant/core/exceptions.py
class DomainException(Exception):
    """Base exception for domain layer."""
    pass

class PlanLimitExceededException(DomainException):
    """User has exceeded their plan limits."""

    def __init__(self, plan: str, limit_type: str, limit: int):
        self.plan = plan
        self.limit_type = limit_type
        self.limit = limit
        super().__init__(
            f"Plan {plan} limit exceeded: {limit_type}={limit}"
        )

    def to_dict(self):
        return {
            "plan": self.plan,
            "limit_type": self.limit_type,
            "limit": self.limit
        }
```

### API Layer Translation

Translate domain exceptions to HTTP responses:

```python
# src/coaching_assistant/api/v1/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(PlanLimitExceededException)
async def handle_plan_limit(request: Request, exc: PlanLimitExceededException):
    return JSONResponse(
        status_code=400,
        content={
            "error": "plan_limit_exceeded",
            "message": str(exc),
            "details": exc.to_dict()
        }
    )
```

**Benefits**:
- **Consistent Error Handling**: Same domain exceptions everywhere
- **Clear Semantics**: Error type indicates business rule violation
- **Easy Testing**: Business logic errors easy to test in isolation
- **Proper CORS**: Exception handlers include CORS middleware processing

## Business Logic Centralization

### Before: Scattered Business Rules

```python
# ❌ Business rules scattered across layers

# In API endpoint
@router.post("/sessions")
async def create_session(...):
    if user.plan == "FREE" and session_count >= 5:
        raise HTTPException(400, "Plan limit exceeded")

# In different service
class NotificationService:
    def process_cancellation(self, user):
        if user.subscription.status == "CANCELLED":
            send_cancellation_email(user)

# In another controller
@router.get("/transcripts")
async def get_transcripts(...):
    if user.plan == "FREE":
        return transcripts[:5]  # Same rule, different place
```

### After: Centralized in Use Cases

```python
# ✅ All business rules in one place

class SessionCreationUseCase:
    def __init__(self, session_repo, user_repo, plan_service):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.plan_service = plan_service

    async def execute(self, user_id: str, session_data: dict):
        user = await self.user_repo.get_by_id(user_id)

        # All business rules centralized
        self._validate_plan_limits(user)
        self._check_subscription_status(user)
        self._validate_session_data(session_data)

        # Create session
        session = Session.create(user_id, session_data)
        return await self.session_repo.save(session)

    def _validate_plan_limits(self, user):
        """Single place for plan limit validation."""
        limits = self.plan_service.get_limits(user.plan)
        current_count = self.session_repo.count_by_user(user.id)

        if current_count >= limits.max_sessions:
            raise PlanLimitExceededException(
                user.plan, "max_sessions", limits.max_sessions
            )
```

**Benefits**:
- ✅ **Consistency**: Same rules applied everywhere
- ✅ **Testability**: Business rules easily unit tested
- ✅ **Maintainability**: Changes made in one place
- ✅ **Discoverability**: Easy to find where business logic lives

## Performance Considerations

### Repository Pattern Overhead

**Concern**: Does the abstraction layer impact performance?

**Reality**: Negligible overhead, with benefits

```python
# Performance measurement results:
# - Direct DB query: 15ms
# - Through repository: 15.2ms
# - Overhead: <1ms per request (0.2ms)
```

**Additional Benefits**:
- **Query Optimization**: Repository pattern encouraged better query design
- **Caching**: Centralized data access enables effective caching
- **Monitoring**: Single point for performance metrics

### Domain Model Conversion Cost

**Analysis**: Converting between ORM and domain models does add computational cost.

**Mitigation Strategies**:

```python
# 1. Selective Conversion - only convert needed fields
def _to_domain_light(self, orm_user):
    """Lightweight conversion for list operations."""
    return DomainUser(
        id=orm_user.id,
        email=orm_user.email,
        # Skip expensive relationships
    )

# 2. Lazy Loading - convert related objects only when accessed
@property
def sessions(self):
    if not self._sessions:
        self._sessions = [self._convert_session(s) for s in self._orm_user.sessions]
    return self._sessions

# 3. Caching - cache converted objects
@lru_cache(maxsize=128)
def get_user_with_plan(self, user_id: str):
    return self._to_domain(self._get_orm_user(user_id))
```

## Testing Strategy

### Test Pyramid for Clean Architecture

```
        E2E Tests (Few)
       /              \
      API Tests (Some)
     /                  \
Use Case Tests (Many, with in-memory repos)
```

**Unit Tests (Use Cases)**:
```python
def test_session_creation_respects_plan_limits():
    # Arrange
    user = DomainUser(id="1", plan=UserPlan.FREE)
    user_repo = InMemoryUserRepository([user])
    session_repo = InMemorySessionRepository()

    # Create max sessions
    for i in range(5):
        session_repo.save(Session(user_id="1", title=f"Session {i}"))

    use_case = SessionCreationUseCase(session_repo, user_repo)

    # Act & Assert
    with pytest.raises(PlanLimitExceededException) as exc:
        use_case.execute(user_id="1", title="Exceeds limit")

    assert exc.value.plan == "FREE"
    assert exc.value.limit == 5
```

**Integration Tests (Repository)**:
```python
@pytest.mark.integration
async def test_user_repository_round_trip(db_session):
    # Test with real database
    repo = UserRepository(db_session)

    user = DomainUser(id="test-1", email="test@example.com")
    saved = await repo.save(user)

    retrieved = await repo.get_by_id("test-1")
    assert retrieved.email == "test@example.com"
```

**E2E Tests (API)**:
```python
@pytest.mark.e2e
async def test_complete_session_workflow(test_client):
    # Test complete user journey
    response = await test_client.post("/api/v1/sessions", json={...})
    assert response.status_code == 201

    session_id = response.json()["id"]
    response = await test_client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
```

## Common Pitfalls and Solutions

### Pitfall 1: Trying to Use Domain Models in SQLAlchemy Queries

```python
# ❌ This fails
from ...core.models.user import User as DomainUser
stmt = select(DomainUser).where(DomainUser.email == email)  # Error!
```

**Solution**: Use infrastructure models for queries, convert to domain after:
```python
# ✅ This works
from ...models.user import User  # Infrastructure model
stmt = select(User).where(User.email == email)
result = await db.execute(stmt)
orm_user = result.scalar_one_or_none()

# Convert to domain model
domain_user = DomainUser(id=orm_user.id, email=orm_user.email)
```

### Pitfall 2: Forgetting Enum Value Extraction

```python
# ❌ Pydantic validation fails
return UserResponse(plan=user.plan)  # Enum object
```

**Solution**: Extract value at boundary:
```python
# ✅ Pydantic accepts string
return UserResponse(plan=user.plan.value)
```

### Pitfall 3: Business Logic in Repository

```python
# ❌ Business rules leaking into infrastructure
class UserRepository:
    async def save(self, user):
        if user.plan == UserPlan.FREE and user.session_count > 5:
            raise Exception("Limit exceeded")  # Wrong layer!
        # ...
```

**Solution**: Keep repositories simple, validate in use case:
```python
# ✅ Business rules in use case
class SessionCreationUseCase:
    async def execute(self, user_id, data):
        user = await self.user_repo.get_by_id(user_id)
        self._validate_plan_limits(user)  # Business logic here
        # ...
```

## Summary: Key Principles

1. **Mixed Model Strategy**: Use infrastructure models for SQLAlchemy, domain models for business logic
2. **Explicit Naming**: Use clear aliases to prevent confusion
3. **Value Extraction**: Extract enum values at architectural boundaries
4. **Gradual Migration**: Use compatibility layers, never "big bang"
5. **Centralized Logic**: Keep business rules in use cases, not scattered
6. **Test with Repositories**: Use in-memory repos for fast, isolated tests
7. **Layer Responsibility**: Each layer handles its own concerns
8. **Backward Compatibility**: Handle legacy data formats gracefully

Following these patterns ensures smooth Clean Architecture adoption while maintaining system stability.