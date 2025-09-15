# Phase 2: API Layer Migration 🔄 READY TO START

## Overview

Phase 2 addresses critical API structure issues and implements Clean Architecture by consolidating inconsistent API organization and removing direct Session dependencies.

**Duration**: 1-2 weeks  
**Status**: 🔄 **IN PROGRESS** - Phase 2.0 Complete, Phase 2.1 Ready  
**Prerequisites**: ✅ Phase 1 completed

## Critical Issues Identified

### Current Problems
1. **Mixed API versioning**: Files scattered between `/api/` root and `/api/v1/`
2. **Duplicate endpoints**: `/api/plans` and `/api/v1/plans` coexist causing conflicts
3. **Inconsistent prefixes**: Some routers define prefixes, others rely on main.py
4. **Architecture violations**: 19 API files directly use SQLAlchemy/Session
5. **No clean separation**: Business logic mixed with HTTP concerns

### Files Requiring Migration
**Priority 1 - Critical Path APIs**:
- `api/sessions.py` - Session management (transcription core)
- `api/plans.py` + `api/v1/plans.py` - Duplicate plans endpoints to consolidate
- `api/v1/subscriptions.py` - Subscription management

**Files to Move to `/api/v1/`**:
- admin.py, admin_reports.py, auth.py, billing_analytics.py
- clients.py, coach_profile.py, coaching_sessions.py
- plan_limits.py, sessions.py, summary.py
- transcript_smoothing.py, usage.py, usage_history.py, user.py

## Objectives

1. **Consolidate API Structure** - Move all endpoints to `/api/v1/` for consistency
2. **Resolve Duplicate Endpoints** - Merge conflicting plans routes
3. **Update API Endpoints** - Migrate to use factory-created use cases
4. **Remove Session Dependencies** - Eliminate direct SQLAlchemy Session injection
5. **Implement DI Pattern** - Use FastAPI dependency injection properly
6. **Maintain Backward Compatibility** - Ensure all existing functionality works

## Progress Tracking

### ✅ Phase 2.0: API Structure Consolidation **COMPLETED**

**Status**: All objectives achieved successfully  
**Completion Date**: Current  
**Git Commit**: `2638300` - "refactor: consolidate API structure and resolve duplicate endpoints"

#### Completed Tasks:
- ✅ **Resolved duplicate plans endpoints** - Merged `/api/plans.py` into `/api/v1/plans.py` with backwards compatibility
- ✅ **Moved 13+ API files** to `/api/v1/` structure for consistency
- ✅ **Updated main.py** - All router imports and prefix configuration updated
- ✅ **Created `/api/v1/dependencies.py`** - FastAPI dependency injection foundation ready
- ✅ **Removed duplicate routers** - Eliminated conflicting route registrations
- ✅ **Standardized API structure** - Clean separation between root `/api/` and versioned `/api/v1/`

#### API Structure Achieved:
```
/api/           # Core services (health, format, debug, dependencies)
/api/v1/        # All business logic endpoints (admin, auth, billing, etc.)
/api/webhooks/  # External integrations (ecpay)
/admin/reports/ # Admin reporting
```

### 🔄 Phase 2.1: Clean Architecture Migration **READY TO START**

**Next**: Begin migration of Priority 1 endpoints to Clean Architecture

## Implementation Steps

### Step 2.0: API Structure Consolidation (Week 1, Days 1-2) ✅ **COMPLETED**

#### 2.0.1: Resolve Duplicate Plans Endpoints
- **Merge** `/api/plans.py` functionality into `/api/v1/plans.py`
- **Consolidate** endpoints:
  - GET `/api/v1/plans` (list all plans) 
  - GET `/api/v1/plans/current` (user's current plan)
  - GET `/api/v1/plans/compare` (plan comparison)
  - POST `/api/v1/plans/validate` (validate plan limits)
- **Remove** the old `/api/plans.py` file
- **Update** main.py to remove duplicate router

#### 2.0.2: Move API Files to `/api/v1/` Structure
**Files to relocate** (maintaining all functionality):
- `admin.py` → `v1/admin.py`
- `auth.py` → `v1/auth.py`
- `billing_analytics.py` → `v1/billing_analytics.py`
- `clients.py` → `v1/clients.py`
- `coach_profile.py` → `v1/coach_profile.py`
- `coaching_sessions.py` → `v1/coaching_sessions.py`
- `plan_limits.py` → `v1/plan_limits.py`
- `sessions.py` → `v1/sessions.py`
- `summary.py` → `v1/summary.py`
- `transcript_smoothing.py` → `v1/transcript_smoothing.py`
- `usage.py` → `v1/usage.py`
- `usage_history.py` → `v1/usage_history.py`
- `user.py` → `v1/user.py`

#### 2.0.3: Standardize Router Definitions
- **Remove** all hardcoded prefixes from APIRouter() constructors
- **Centralize** prefix management in main.py
- **Update** all import statements in main.py

### Step 2.1: Clean Architecture Migration (Week 1-2, Days 3-7)

**Priority 1 - Critical Path APIs**:
- `api/v1/sessions.py` - Session management (transcription core)
- `api/v1/plans.py` - Plan configuration and limits (consolidated)
- `api/v1/subscriptions.py` - Subscription management

**Priority 2 - Secondary APIs**:
- `api/v1/clients.py` - Client management
- `api/v1/coaching_sessions.py` - Coaching session tracking
- `api/v1/usage.py` - Usage tracking

**Priority 3 - Remaining APIs**:
- All other endpoints with Session dependencies

### Step 2.2: Create FastAPI Dependencies

**Target**: `src/coaching_assistant/api/dependencies.py`

Create FastAPI dependency functions:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from ..infrastructure.factories import UsageTrackingServiceFactory
from ..core.services.usage_tracking_use_case import CreateUsageLogUseCase

def get_usage_log_use_case(
    db: Session = Depends(get_db)
) -> CreateUsageLogUseCase:
    """Dependency to inject CreateUsageLogUseCase."""
    return UsageTrackingServiceFactory.create_usage_log_use_case(db)

def get_user_usage_use_case(
    db: Session = Depends(get_db)
) -> GetUserUsageUseCase:
    """Dependency to inject GetUserUsageUseCase."""
    return UsageTrackingServiceFactory.create_user_usage_use_case(db)
```

### Step 2.3: Update API Endpoints Pattern

**Before** (Direct Session usage):
```python
@router.post(\"/sessions\")
def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    # ❌ Direct database operations
    user = db.query(User).filter_by(id=request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=\"User not found\")
    
    # Business logic mixed with API logic
    if user.plan == UserPlan.FREE and user.usage_minutes > 120:
        raise HTTPException(status_code=402, detail=\"Plan limit exceeded\")
```

**After** (Clean dependency injection):
```python
@router.post(\"/sessions\")
def create_session(
    request: CreateSessionRequest,
    use_case: CreateUsageLogUseCase = Depends(get_usage_log_use_case)
):
    try:
        # ✅ Delegate to use case
        result = use_case.execute(request)
        return CreateSessionResponse.from_domain(result)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Step 2.4: Implementation Timeline

#### Week 1: Structure Consolidation
**Days 1-2**: API Structure Reorganization
- Resolve duplicate plans endpoints
- Move all API files to `/api/v1/` structure
- Update router definitions and main.py

**Days 3-4**: Priority 1 Clean Architecture Migration
1. **Sessions API** (`api/v1/sessions.py`)
   - Most critical for transcription workflow
   - Update endpoints: `POST /sessions`, `GET /sessions/{id}`, `PATCH /sessions/{id}`

2. **Plans API** (`api/v1/plans.py`)
   - User plan validation and limits (consolidated)
   - Update endpoints: `GET /plans`, `GET /plans/current`, `GET /plans/compare`, `POST /plans/validate`

**Days 5-7**: Priority 1 Completion
3. **Subscriptions API** (`api/v1/subscriptions.py`)
   - Billing and subscription management
   - Update all subscription-related endpoints

#### Week 2: Secondary APIs
**Days 8-10**: Priority 2 APIs
- `api/v1/clients.py` - Client management
- `api/v1/coaching_sessions.py` - Coaching session tracking  
- `api/v1/usage.py` - Usage tracking

**Days 11-14**: Remaining APIs and Testing
- All other endpoints with Session dependencies
- Comprehensive testing and validation
- Performance benchmarking

### Step 2.5: Testing Strategy

For each migrated endpoint:

1. **Unit Tests**: Test use case logic in isolation
2. **Integration Tests**: Test API endpoints with real database
3. **Contract Tests**: Ensure API response format unchanged
4. **Performance Tests**: Validate no regression in response times

```python
# Example test structure
def test_create_session_use_case():
    # Unit test - use in-memory repositories
    user_repo = create_in_memory_user_repository()
    usage_log_repo = create_in_memory_usage_log_repository()
    session_repo = create_in_memory_session_repository()
    
    use_case = CreateUsageLogUseCase(user_repo, usage_log_repo, session_repo)
    # Test business logic without database

def test_create_session_api_endpoint(client):
    # Integration test - with real database
    response = client.post(\"/sessions\", json=test_data)
    assert response.status_code == 200
```

## Implementation Commands

### Setup
```bash
# Create feature branch
git checkout -b feature/clean-architecture-phase-2

# Backup current state
git add -A
git commit -m "backup: pre-phase-2 state"
```

### Phase 2.0: API Structure Consolidation
```bash
# Step 1: Merge duplicate plans endpoints
# Read current functionality from both files
cat src/coaching_assistant/api/plans.py
cat src/coaching_assistant/api/v1/plans.py

# Merge into single consolidated plans API
# Edit src/coaching_assistant/api/v1/plans.py (consolidate all endpoints)

# Remove old plans file
rm src/coaching_assistant/api/plans.py

# Step 2: Move API files to v1 structure  
cd src/coaching_assistant/api

# Move files to v1/ directory
mv admin.py v1/
mv auth.py v1/
mv billing_analytics.py v1/ 
mv clients.py v1/
mv coach_profile.py v1/
mv coaching_sessions.py v1/
mv plan_limits.py v1/
mv sessions.py v1/
mv summary.py v1/
mv transcript_smoothing.py v1/
mv usage.py v1/
mv usage_history.py v1/
mv user.py v1/

# Step 3: Update router definitions (remove hardcoded prefixes)
# Edit each moved file to remove prefix from APIRouter()

# Step 4: Update main.py imports and router registration
# Edit src/coaching_assistant/main.py
```

### Phase 2.1: Clean Architecture Migration
```bash
# Step 1: Create comprehensive dependencies file
# Edit src/coaching_assistant/api/v1/dependencies.py

# Step 2: Priority 1 APIs - Update to use Clean Architecture
# Edit src/coaching_assistant/api/v1/sessions.py
# Edit src/coaching_assistant/api/v1/plans.py  
# Edit src/coaching_assistant/api/v1/subscriptions.py

# Step 3: Priority 2 APIs
# Edit src/coaching_assistant/api/v1/clients.py
# Edit src/coaching_assistant/api/v1/coaching_sessions.py
# Edit src/coaching_assistant/api/v1/usage.py

# Test after each major change
make test
make test-server
make architecture-check
```

### Validation Commands
```bash
# Architecture compliance check
python scripts/check_architecture.py

# Verify no SQLAlchemy imports in API layer
grep -r "from sqlalchemy" src/coaching_assistant/api/
grep -r "Session" src/coaching_assistant/api/

# Test all endpoints still work
make test
make test-server
```

## Success Criteria

### ✅ Functional Requirements
- [ ] All API endpoints return same response formats
- [ ] All existing tests pass without modification
- [ ] No behavioral changes from user perspective
- [ ] Error handling maintains same HTTP status codes

### ✅ Architectural Requirements  
- [ ] **Consistent API structure** - All endpoints in `/api/v1/` with standardized routing
- [ ] **No duplicate endpoints** - Single consolidated plans API
- [ ] **No direct Session injection** in API endpoints
- [ ] **All business logic delegated** to use cases
- [ ] **FastAPI dependency injection** used consistently
- [ ] **API layer contains only HTTP concerns**

### ✅ Quality Requirements
- [ ] API response times remain within 5% of baseline
- [ ] Memory usage doesn't increase significantly
- [ ] All architectural rules compliance (see `architectural-rules.md`)
- [ ] Code review checklist passes

## Risk Mitigation

### Technical Risks

**Risk**: API behavior changes during migration
- **Mitigation**: Comprehensive integration tests before/after
- **Rollback**: Keep original endpoints temporarily during transition

**Risk**: Performance degradation
- **Mitigation**: Benchmark each endpoint before/after migration
- **Rollback**: Revert to direct Session if performance issues

**Risk**: Dependency injection complexity
- **Mitigation**: Start with simple endpoints, document patterns
- **Rollback**: Use compatibility wrappers during transition

### Business Risks

**Risk**: Service disruption during deployment
- **Mitigation**: Deploy with feature flags, gradual rollout
- **Rollback**: Immediate rollback plan ready

**Risk**: Breaking existing clients
- **Mitigation**: Maintain exact API contract
- **Rollback**: API versioning if needed

## Testing Plan

### Before Migration
```bash
# Capture baseline performance
make benchmark-api

# Run full test suite
make test
make test-server
make test-integration

# Document current behavior
curl -X POST /api/sessions -d @test-data.json > baseline-response.json
```

### During Migration
```bash
# Test each migrated endpoint
pytest tests/api/test_sessions.py -v
pytest tests/integration/test_sessions_workflow.py -v

# Validate architectural compliance
make architecture-check

# Performance regression test
make benchmark-api-compare
```

### After Migration
```bash
# Full regression test
make test-all

# Load testing (if applicable)
make load-test

# Architecture validation
make architecture-check
python scripts/check_architecture.py
```

## Validation Checklist

### Code Review Requirements
- [ ] **No SQLAlchemy imports** in updated API files
- [ ] **No Session parameters** in endpoint functions
- [ ] **FastAPI dependencies** used for all use case injection
- [ ] **Exception handling** converts domain exceptions properly
- [ ] **Response models** use `.from_domain()` pattern consistently

### Architecture Compliance
- [ ] All database operations go through use cases
- [ ] No business logic in API endpoint functions
- [ ] Clear separation between HTTP concerns and business logic
- [ ] Dependency injection follows established patterns

## Example Implementation

### Sessions API Migration

**File**: `src/coaching_assistant/api/sessions.py`

**Before**:
```python
@router.post(\"/sessions/{session_id}/transcribe\")
async def start_transcription(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=\"Session not found\")
    
    # Business logic in API layer ❌
    if session.status != SessionStatus.UPLOADED:
        raise HTTPException(status_code=400, detail=\"Invalid session status\")
    
    # Direct service instantiation ❌
    usage_service = UsageTrackingService(db)
    usage_log = usage_service.create_usage_log(session)
```

**After**:
```python
@router.post(\"/sessions/{session_id}/transcribe\")
async def start_transcription(
    session_id: UUID,
    session_use_case: SessionUseCase = Depends(get_session_use_case),
    usage_use_case: CreateUsageLogUseCase = Depends(get_usage_log_use_case)
):
    try:
        # Business logic delegated to use cases ✅
        session = session_use_case.get_by_id(session_id)
        usage_log = usage_use_case.execute(session)
        
        return TranscriptionResponse.from_domain(usage_log)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Next Phase

Upon completion of Phase 2:

👉 **[Phase 3: Domain Models](./phase-3-domain-models.md)**
- Move ORM models to infrastructure layer
- Create pure domain models in core layer
- Complete Clean Architecture separation

---

**Status**: 🔄 **READY TO START**  
**Prerequisites**: Phase 1 completed ✅  
**Estimated Duration**: 1-2 weeks  
**Next Phase**: [Phase 3: Domain Models](./phase-3-domain-models.md)