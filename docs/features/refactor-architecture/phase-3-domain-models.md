# Phase 3: Domain Model Separation ✅ COMPLETED

## Overview

Phase 3 completes the Clean Architecture transformation by separating domain models from ORM models and moving infrastructure concerns to the appropriate layer.

**Duration**: 2-3 weeks
**Status**: ✅ **COMPLETED** (2025-09-15)
**Prerequisites**: ✅ Phase 1 + ✅ Phase 2

## Objectives

1. **Create Pure Domain Models** - Business entities without ORM dependencies
2. **Move ORM Models** - Relocate SQLAlchemy models to infrastructure layer
3. **Update Use Cases** - Migrate to use pure domain models
4. **Complete Separation** - Achieve full Clean Architecture compliance

## Implementation Steps

### Step 3.1: Analyze Current Models

**Current State**: Models in `src/coaching_assistant/models/`
- `user.py` - User entity with SQLAlchemy decorators
- `session.py` - Session entity with ORM relationships
- `usage_log.py` - Usage tracking with database constraints
- `subscription.py` - Subscription and billing models

**Target State**: Separate domain and ORM models
```
src/coaching_assistant/
├── core/
│   └── models/                    # Pure domain models
│       ├── user.py               # Business rules only
│       ├── session.py            # Domain logic
│       └── usage_log.py          # Business validation
└── infrastructure/
    └── db/
        └── models/               # ORM models (SQLAlchemy)
            ├── user_model.py    # Database persistence
            ├── session_model.py # DB relationships
            └── usage_log_model.py # DB constraints
```

### Step 3.2: Create Pure Domain Models

**Target**: `src/coaching_assistant/core/models/`

Create business-focused models without infrastructure dependencies:

```python
# core/models/user.py - Pure domain model
@dataclass
class User:
    id: Optional[UUID] = None
    email: str = ""
    plan: UserPlan = UserPlan.FREE
    usage_minutes: int = 0
    created_at: Optional[datetime] = None
    
    def can_create_session(self) -> bool:
        """Business rule: Check if user can create new session."""
        limits = self.get_plan_limits()
        return self.usage_minutes < limits.monthly_minutes
    
    def get_plan_limits(self) -> PlanLimits:
        """Business rule: Get plan-specific limits."""
        return PlanLimits.for_plan(self.plan)
    
    def upgrade_plan(self, new_plan: UserPlan) -> None:
        """Business rule: Upgrade user plan with validation."""
        if new_plan.value <= self.plan.value:
            raise ValueError("Cannot downgrade plan")
        self.plan = new_plan
```

### Step 3.3: Create ORM Models in Infrastructure

**Target**: `src/coaching_assistant/infrastructure/db/models/`

Keep SQLAlchemy-specific concerns in infrastructure:

```python
# infrastructure/db/models/user_model.py - ORM model
from sqlalchemy import Column, String, Integer, DateTime, Enum
from .base import Base

class UserModel(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    plan = Column(Enum(UserPlan), default=UserPlan.FREE)
    usage_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ORM relationships
    sessions = relationship("SessionModel", back_populates="user")
    usage_logs = relationship("UsageLogModel", back_populates="user")
    
    def to_domain(self) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=UUID(self.id) if self.id else None,
            email=self.email,
            plan=self.plan,
            usage_minutes=self.usage_minutes,
            created_at=self.created_at
        )
    
    @classmethod
    def from_domain(cls, user: User) -> 'UserModel':
        """Convert domain model to ORM model."""
        return cls(
            id=str(user.id) if user.id else None,
            email=user.email,
            plan=user.plan,
            usage_minutes=user.usage_minutes,
            created_at=user.created_at
        )
```

### Step 3.4: Update Repository Implementations

**Target**: `src/coaching_assistant/infrastructure/db/repositories/`

Update repositories to handle domain ↔ ORM conversion:

```python
# infrastructure/db/repositories/user_repository.py
class SQLAlchemyUserRepository(UserRepoPort):
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get domain model by ID."""
        orm_user = self.session.get(UserModel, str(user_id))
        return orm_user.to_domain() if orm_user else None
    
    def save(self, user: User) -> User:
        """Save domain model."""
        if user.id:
            # Update existing
            orm_user = self.session.get(UserModel, str(user.id))
            if orm_user:
                orm_user.email = user.email
                orm_user.plan = user.plan
                orm_user.usage_minutes = user.usage_minutes
            else:
                raise ValueError(f"User {user.id} not found")
        else:
            # Create new
            orm_user = UserModel.from_domain(user)
            self.session.add(orm_user)
        
        self.session.flush()
        return orm_user.to_domain()
```

### Step 3.5: Update Use Cases

**Target**: `src/coaching_assistant/core/services/`

Update use cases to work with pure domain models:

```python
# core/services/usage_tracking_use_case.py
class CreateUsageLogUseCase:
    def execute(self, session: Session, ...) -> UsageLog:
        # Get domain user (not ORM model)
        user = self.user_repo.get_by_id(session.user_id)
        if not user:
            raise ValueError(f"User not found: {session.user_id}")
        
        # Business rule validation using domain model
        if not user.can_create_session():
            raise DomainException("User has exceeded plan limits")
        
        # Pure domain logic
        usage_log = UsageLog.create_for_session(session, user)
        
        # Save through repository (handles ORM conversion)
        return self.usage_log_repo.save(usage_log)
```

### Step 3.6: Migration Strategy

#### Phase 3.1: Create Domain Models (Week 1)
1. Create `core/models/` directory structure
2. Implement pure domain models for core entities:
   - User domain model with business rules
   - Session domain model with validation logic
   - UsageLog domain model with calculation methods
3. Unit test domain models without database

#### Phase 3.2: Create ORM Models in Infrastructure (Week 1)
1. Create `infrastructure/db/models/` directory
2. Move existing SQLAlchemy models with conversions:
   - UserModel with `to_domain()` / `from_domain()`
   - SessionModel with relationship mapping
   - UsageLogModel with constraint handling
3. Test ORM ↔ Domain conversions

#### Phase 3.3: Update Repository Layer (Week 2)
1. Update all repository implementations
2. Handle domain ↔ ORM model conversions
3. Test repository operations with new models
4. Update in-memory repositories for domain models

#### Phase 3.4: Update Use Cases (Week 2-3)
1. Migrate use cases to use domain models
2. Move business logic from ORM models to domain models
3. Update all business rule validations
4. Comprehensive testing of business logic

#### Phase 3.5: Update API Layer (Week 3)
1. Ensure API serialization works with domain models
2. Update response model conversions
3. Test all API endpoints with new model structure
4. Performance regression testing

## Success Criteria

### ✅ Domain Model Requirements
- [ ] All business rules implemented in domain models
- [ ] No SQLAlchemy imports in `core/models/`
- [ ] Domain models are framework-agnostic
- [ ] Rich domain behavior, not anemic models

### ✅ ORM Model Requirements
- [ ] All SQLAlchemy concerns in `infrastructure/db/models/`
- [ ] Proper conversion methods between domain and ORM
- [ ] Database relationships and constraints maintained
- [ ] No business logic in ORM models

### ✅ Architecture Compliance
- [ ] Clear separation between domain and infrastructure
- [ ] Use cases work with domain models only
- [ ] Repositories handle domain ↔ ORM conversion
- [ ] No circular dependencies between layers

### ✅ Quality Requirements
- [ ] All existing functionality preserved
- [ ] Performance within 5% of baseline
- [ ] 90%+ test coverage for domain models
- [ ] Architecture rules compliance

## Risk Mitigation

### Technical Risks

**Risk**: Complex model relationships
- **Mitigation**: Start with simple models, handle relationships incrementally
- **Rollback**: Keep both model types during transition

**Risk**: Conversion performance overhead
- **Mitigation**: Benchmark conversions, optimize if needed
- **Rollback**: Direct ORM usage if performance critical

**Risk**: Data integrity during migration
- **Mitigation**: Extensive testing, database validation
- **Rollback**: Database rollback scripts ready

### Business Risks

**Risk**: Extended development time
- **Mitigation**: Phased approach, parallel development
- **Rollback**: Feature freeze if timeline critical

**Risk**: Regression in existing functionality
- **Mitigation**: Comprehensive regression testing
- **Rollback**: Quick rollback to Phase 2 state

## Testing Strategy

### Domain Model Tests
```python
# Test pure business logic
def test_user_can_create_session():
    user = User(plan=UserPlan.FREE, usage_minutes=100)
    assert user.can_create_session() is True
    
    user.usage_minutes = 150  # Exceed FREE plan limit
    assert user.can_create_session() is False

def test_user_plan_upgrade():
    user = User(plan=UserPlan.FREE)
    user.upgrade_plan(UserPlan.PRO)
    assert user.plan == UserPlan.PRO
    
    with pytest.raises(ValueError):
        user.upgrade_plan(UserPlan.FREE)  # Cannot downgrade
```

### ORM Conversion Tests
```python
def test_user_domain_orm_conversion():
    domain_user = User(
        id=uuid4(),
        email="test@example.com",
        plan=UserPlan.PRO
    )
    
    # Domain -> ORM
    orm_user = UserModel.from_domain(domain_user)
    assert orm_user.email == domain_user.email
    
    # ORM -> Domain
    converted_back = orm_user.to_domain()
    assert converted_back.id == domain_user.id
    assert converted_back.plan == domain_user.plan
```

### Integration Tests
```python
def test_repository_with_domain_models():
    user_repo = SQLAlchemyUserRepository(db_session)
    
    # Save domain model
    domain_user = User(email="test@example.com")
    saved_user = user_repo.save(domain_user)
    
    # Retrieve as domain model
    retrieved_user = user_repo.get_by_id(saved_user.id)
    assert isinstance(retrieved_user, User)
    assert retrieved_user.email == "test@example.com"
```

## Implementation Commands

### Setup
```bash
# Create feature branch
git checkout -b feature/clean-architecture-phase-3

# Create domain models directory
mkdir -p src/coaching_assistant/core/models

# Move ORM models to infrastructure
mkdir -p src/coaching_assistant/infrastructure/db/models
```

### Migration Commands
```bash
# Step 1: Create domain models
# Create core/models/user.py, session.py, usage_log.py

# Step 2: Create ORM models in infrastructure
# Create infrastructure/db/models/user_model.py, etc.

# Step 3: Update repositories for model conversion
# Update all repository implementations

# Step 4: Update use cases to use domain models
# Update core/services/*.py

# Test after each step
make test
make test-integration
make architecture-check
```

## Benefits Achieved

### 🎯 Pure Business Logic
- Domain models contain only business rules
- No framework coupling in core domain
- Rich domain behavior instead of anemic models

### 🎯 Clean Separation
- Clear boundary between domain and infrastructure
- ORM concerns isolated to infrastructure layer
- Business logic independent of database structure

### 🎯 Enhanced Testability
- Domain logic testable without database
- Fast unit tests for business rules
- Clear test boundaries between layers

### 🎯 Framework Independence
- Core business logic portable between frameworks
- Easy to change ORM or database technology
- Domain model evolution independent of infrastructure

## Next Steps After Completion

Upon completion of Phase 3, the Clean Architecture implementation will be complete:

### ✅ Architecture Fully Implemented
- Repository pattern with clear interfaces
- Use cases containing pure business logic
- Domain models with rich behavior
- Infrastructure properly separated

### ✅ Ready for Advanced Patterns
- CQRS (Command Query Responsibility Segregation)
- Event sourcing for audit trails
- Domain events for decoupling
- Specification pattern for complex queries

### ✅ Continuous Improvement
- Architecture validation automation
- Performance monitoring and optimization
- Documentation and team training
- Best practices documentation

---

**Status**: 📋 **FUTURE**  
**Prerequisites**: Phase 1 ✅ + Phase 2 completion  
**Estimated Duration**: 2-3 weeks  
**Completion**: Full Clean Architecture implementation