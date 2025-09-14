# Current Architecture Problems Analysis

## Overview

This document analyzes the specific architectural issues that led to the Clean Architecture refactoring initiative.

## 🔍 Problem Categories

### 1. SQL Operations Scattered Across Layers

#### API Layer Issues
**Direct SQLAlchemy Session injection and query usage:**

- **`api/sessions.py:258`** - Direct `db.query(Session).filter()` usage
  ```python
  # ❌ BAD: Business logic in API layer
  session = db.query(Session).filter(Session.id == session_id).first()
  if not session:
      raise HTTPException(status_code=404, detail="Session not found")
  ```

- **`api/plans.py:27`** - Direct `db.query(PlanConfiguration)` operations
  ```python
  # ❌ BAD: Database queries in API controller
  plan = db.query(PlanConfiguration).filter_by(name=plan_name).first()
  ```

#### Service Layer Issues
**Direct ORM dependencies:**

- **`services/usage_tracking.py:93`** - `self.db.query(User).filter()` 
  ```python
  # ❌ BAD: Service tightly coupled to ORM
  class UsageTrackingService:
      def __init__(self, db: Session):
          self.db = db  # Direct Session dependency
      
      def create_usage_log(self, session_data):
          user = self.db.query(User).filter_by(id=user_id).first()
  ```

- **`core/services/ecpay_service.py:29`** - `db: Session` injection
  ```python
  # ❌ BAD: Core service depends on infrastructure
  def process_payment(db: Session, payment_data):
      subscription = db.query(Subscription).filter_by(id=payment_data.id).first()
  ```

### 2. Mixing of Concerns

#### Business Logic in API Controllers
```python
# ❌ BAD: Business rules in API layer
@router.post("/sessions")
def create_session(request: CreateSessionRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=request.user_id).first()
    
    # Business logic mixed with HTTP concerns
    if user.plan == UserPlan.FREE and user.usage_minutes > 120:
        raise HTTPException(status_code=402, detail="Plan limit exceeded")
    
    if request.file_size > get_plan_limit(user.plan).max_file_size:
        raise HTTPException(status_code=413, detail="File too large")
```

#### Services Tightly Coupled to ORM Models
```python
# ❌ BAD: Service knows about ORM structure
class TranscriptionService:
    def process(self, session_id: UUID):
        session = self.db.query(Session).options(
            joinedload(Session.user),           # ORM-specific loading
            joinedload(Session.usage_logs)      # Knowledge of relationships
        ).filter_by(id=session_id).first()
```

### 3. Lack of Architectural Boundaries

#### Pydantic Schemas Throughout All Layers
```python
# ❌ BAD: API schemas used in service layer
class UsageTrackingService:
    def create_log(self, request: CreateUsageRequest) -> UsageResponse:
        # Service layer using API request/response models
```

#### ORM Models Imported in API Layer
```python
# ❌ BAD: API layer imports ORM models
from ..models.user import User
from ..models.session import Session

@router.get("/users/{id}")
def get_user(id: UUID) -> User:  # Returning ORM model directly
    return db.query(User).get(id)
```

#### No Repository Abstraction Layer
```python
# ❌ BAD: Direct database operations everywhere
def get_user_sessions(user_id: UUID, db: Session):
    return db.query(Session).filter_by(user_id=user_id).all()

def update_session_status(session_id: UUID, status: str, db: Session):
    session = db.query(Session).get(session_id)
    session.status = status
    db.commit()
```

## 📊 Impact Analysis

### Technical Debt Indicators

1. **Testing Difficulty**
   - Services cannot be unit tested without database
   - Complex test setup for business logic validation
   - Slow test execution due to database dependencies

2. **Code Duplication**
   - Same query patterns repeated across multiple files
   - Business rules scattered in different places
   - Error handling inconsistent across layers

3. **Coupling Issues**
   - Changes to database schema require updates in multiple layers
   - API changes affect service layer implementations
   - Cannot swap out ORM or database without major refactoring

### Developer Experience Problems

1. **Cognitive Load**
   - Developers need to understand ORM, business rules, and HTTP concerns together
   - Difficult to locate where specific business rules are implemented
   - Hard to understand data flow through the application

2. **Maintenance Burden**
   - Bug fixes require changes in multiple layers
   - Feature additions touch many files
   - Regression risk high due to tight coupling

3. **Testing Complexity**
   - Unit tests require database setup
   - Mocking is complex and brittle
   - Slow feedback cycle during development

## 🎯 Root Causes

### 1. Lack of Architectural Boundaries
- No clear separation between layers
- Missing abstraction interfaces
- Infrastructure concerns leak into business logic

### 2. Missing Repository Pattern
- Direct database access from multiple layers
- No abstraction over data persistence
- Difficult to test business logic in isolation

### 3. Violation of Dependency Inversion Principle
- High-level modules depend on low-level modules
- Business logic depends on infrastructure details
- Cannot easily change or substitute implementations

### 4. Insufficient Separation of Concerns
- API controllers contain business logic
- Services handle HTTP concerns
- Models mix domain and persistence logic

## 🔧 Specific Code Smells Identified

### Database Session Leakage
```bash
# Found 15+ instances of direct Session usage outside repositories
grep -r "Session.*=" src/coaching_assistant/api/
grep -r "db\\.query" src/coaching_assistant/
```

### Business Logic in Wrong Layer
```bash
# Found business rules in API layer
grep -r "plan.*limit" src/coaching_assistant/api/
grep -r "raise.*HTTPException" src/coaching_assistant/services/
```

### ORM Knowledge Outside Infrastructure
```bash
# Found SQLAlchemy imports in business layer
grep -r "from sqlalchemy" src/coaching_assistant/core/
grep -r "joinedload" src/coaching_assistant/services/
```

### Missing Error Boundaries
```bash
# Found mixed error handling patterns
grep -r "HTTPException" src/coaching_assistant/services/
grep -r "try.*except" src/coaching_assistant/api/
```

## 💡 Solution Requirements

Based on this analysis, the Clean Architecture refactoring must address:

1. **Create Clear Boundaries** - Repository ports, use cases, API boundaries
2. **Implement Dependency Inversion** - Abstractions, not concretions
3. **Separate Business Logic** - Pure domain logic in use cases
4. **Abstract Data Access** - Repository pattern with implementations
5. **Enable Testing** - In-memory repositories, isolated unit tests

## 📈 Success Metrics

To validate that these problems are solved:

- [ ] Zero SQLAlchemy imports in `core/services/`
- [ ] All unit tests run without database connection
- [ ] Business logic fully testable in isolation
- [ ] Clear separation between HTTP, business, and data concerns
- [ ] Consistent error handling patterns across layers
- [ ] Reduced coupling between components
- [ ] Faster test execution and development feedback

---

**Status**: Problems identified and analyzed  
**Solution**: Clean Architecture implementation in 3 phases  
**Next**: [Phase 1: Foundation Setup](./phase-1-foundation.md)