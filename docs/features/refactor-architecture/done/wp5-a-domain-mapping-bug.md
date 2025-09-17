# WP5-A: Domain Mapping Bug - UserPlan Enum Handling in Clean Architecture

## Bug Report

**Issue**: API endpoint `/api/plans/current` returns 500 Internal Server Error
**Error**: `'UserPlan.STUDENT' is not among the defined enum values`
**Root Cause**: Improper enum-to-string conversion in infrastructure layer

## Executive Summary

The system experiences a critical failure in the domain-to-ORM mapping layer where SQLAlchemy receives Python enum objects instead of their string values. This violates Clean Architecture principles and causes database query failures.

## Architecture Analysis

### Current State - Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  /api/plans/current endpoint                                │
│  • Receives HTTP request                                    │
│  • Injects use cases via dependency injection               │
│  • Returns HTTP response                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Calls with user.id (UUID)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 Core Layer (Use Cases)                       │
│  PlanRetrievalUseCase.get_user_current_plan()              │
│  • Business logic only                                      │
│  • Works with domain models (User with UserPlan enum)       │
│  • No infrastructure dependencies ✅                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Passes UserPlan.STUDENT (enum)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            Infrastructure Layer (Repositories)               │
│  PlanConfigurationRepository.get_by_plan_type()             │
│  • SQLAlchemy ORM operations                                │
│  • Should convert domain enums → DB strings ❌              │
│  • Currently passes enum directly to SQLAlchemy ❌          │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy receives enum object
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                     │
│  • Expects string values: 'student', 'free', 'pro'         │
│  • Receives: UserPlan.STUDENT (Python object repr)          │
│  • Throws: Enum value error ❌                              │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Call Flow Analysis

### 1. API Request Flow
```python
# apps/web makes request
GET /api/plans/current
Authorization: Bearer <token>

# API endpoint (line 148-158)
@router.get("/plans/current")
async def get_current_plan_status(
    current_user: User = Depends(get_current_user_dependency),  # User has plan=UserPlan.STUDENT
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(...)
):
    plan_info = plan_retrieval_use_case.get_user_current_plan(current_user.id)
```

### 2. Use Case Processing
```python
# plan_management_use_case.py (line 53-69)
def get_user_current_plan(self, user_id: UUID):
    user = self.user_repo.get_by_id(user_id)  # Returns User with plan=UserPlan.STUDENT
    plan_config = self.plan_config_repo.get_by_plan_type(user.plan)  # Passes enum ❌
```

### 3. Repository Query Failure
```python
# plan_configuration_repository.py (line 18-25)
def get_by_plan_type(self, plan_type: UserPlan):  # Receives UserPlan.STUDENT enum
    orm_plan = (
        self.db_session.query(PlanConfigurationModel)
        .filter(PlanConfigurationModel.plan_type == plan_type)  # ❌ Enum passed to SQLAlchemy
        .first()
    )
```

### 4. SQLAlchemy Processing
```python
# SQLAlchemy tries to convert:
# UserPlan.STUDENT → 'UserPlan.STUDENT' (string representation)
# But database expects: 'student' (enum value)
# Result: "'UserPlan.STUDENT' is not among the defined enum values"
```

## Clean Architecture Violations Identified

### 1. ❌ Incomplete Domain-to-ORM Conversion
**Location**: Infrastructure repositories
**Issue**: Repositories receive domain enums but don't convert to database values
**Principle Violated**: Infrastructure should handle all persistence concerns

### 2. ❌ Leaky Abstraction
**Location**: Repository interfaces
**Issue**: Core layer must know that infrastructure needs special handling
**Principle Violated**: Core should be independent of infrastructure details

### 3. ✅ Correct Separation (Positive)
**Location**: Core services
**Achievement**: No SQLAlchemy imports, no database dependencies
**Principle Followed**: Dependency inversion properly implemented

## Comprehensive Fix Plan

### Phase 1: Infrastructure Layer Fixes

#### A. PlanConfigurationRepository (`plan_configuration_repository.py`)
```python
# Line 22 - Fix enum comparison
# BEFORE:
.filter(PlanConfigurationModel.plan_type == plan_type)

# AFTER:
.filter(PlanConfigurationModel.plan_type == (
    plan_type.value if isinstance(plan_type, UserPlan) else plan_type
))
```

#### B. UserRepository (`user_repository.py`)
Multiple locations need enum-to-value conversion:

```python
# Line 92 - _create_orm_user method
# BEFORE:
plan=user.plan,
role=user.role,

# AFTER:
plan=user.plan.value if isinstance(user.plan, UserPlan) else user.plan,
role=user.role.value if isinstance(user.role, UserRole) else user.role,

# Line 183 - save method (update existing)
# BEFORE:
orm_user.plan = user.plan
orm_user.role = user.role

# AFTER:
orm_user.plan = user.plan.value if isinstance(user.plan, UserPlan) else user.plan
orm_user.role = user.role.value if isinstance(user.role, UserRole) else user.role

# Line 270 - get_by_plan method
# BEFORE:
.filter(UserModel.plan == plan)

# AFTER:
.filter(UserModel.plan == (plan.value if isinstance(plan, UserPlan) else plan))

# Line 291 - count_by_plan method
# Same pattern as line 270

# Line 309 - get_by_role method
# BEFORE:
.filter(UserModel.role == role)

# AFTER:
.filter(UserModel.role == (role.value if isinstance(role, UserRole) else role))

# Line 359 - update_plan method
# BEFORE:
orm_user.plan = new_plan

# AFTER:
orm_user.plan = new_plan.value if isinstance(new_plan, UserPlan) else new_plan

# Line 403 - get_admin_users method
# BEFORE:
.filter(UserModel.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))

# AFTER:
.filter(UserModel.role.in_([UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]))
```

### Phase 2: Testing Strategy

#### A. Unit Tests for Repository Conversion
```python
def test_user_repository_enum_conversion():
    """Test that repository correctly converts enums to values."""
    user = DomainUser(plan=UserPlan.STUDENT, role=UserRole.USER)
    orm_user = repo._create_orm_user(user)
    assert orm_user.plan == "student"  # String value, not enum
    assert orm_user.role == "user"     # String value, not enum

def test_plan_config_repository_enum_query():
    """Test that repository queries with enum values."""
    # Should convert UserPlan.STUDENT to "student" for query
    result = repo.get_by_plan_type(UserPlan.STUDENT)
    assert result is not None
```

#### B. Integration Tests
```python
def test_api_plans_current_with_student_plan():
    """End-to-end test for STUDENT plan users."""
    # Create user with STUDENT plan
    # Call /api/plans/current
    # Verify 200 response (not 500)
```

### Phase 3: Architecture Improvements

#### A. Create Conversion Helper
```python
# src/coaching_assistant/infrastructure/db/converters.py
class EnumConverter:
    """Centralized enum-to-value conversion for ORM operations."""

    @staticmethod
    def to_db_value(enum_or_value):
        """Convert enum to database value."""
        if isinstance(enum_or_value, enum.Enum):
            return enum_or_value.value
        return enum_or_value

    @staticmethod
    def to_db_values(enum_list):
        """Convert list of enums to database values."""
        return [EnumConverter.to_db_value(e) for e in enum_list]
```

#### B. Update Repository Base Class
```python
class SQLAlchemyRepository:
    """Base repository with common conversion logic."""

    def _enum_to_value(self, enum_or_value):
        """Convert enum to value for database operations."""
        return enum_or_value.value if isinstance(enum_or_value, enum.Enum) else enum_or_value
```

## Database Schema Verification

### Current PostgreSQL Enum Type
```sql
-- Database has correct lowercase values
CREATE TYPE userplan AS ENUM ('free', 'student', 'pro', 'enterprise', 'coaching_school');
CREATE TYPE userrole AS ENUM ('user', 'staff', 'admin', 'super_admin');
```

### ORM Model Configuration
```python
# plan_configuration_model.py (line 27-32)
plan_type = Column(
    SQLEnum(UserPlan, values_callable=lambda x: [e.value for e in x]),
    unique=True,
    nullable=False,
    index=True,
)
```

## Impact Analysis

### Affected Components
1. **User Repository**: 8 methods need enum conversion
2. **Plan Configuration Repository**: 1 method needs enum conversion
3. **API Endpoints**: `/api/plans/current`, `/api/plans/compare`, `/api/plans/validate`
4. **Use Cases**: No changes needed (correctly using enums)

### Risk Assessment
- **High Risk**: Production API currently failing for non-FREE users
- **Medium Risk**: Data integrity if enums saved incorrectly
- **Low Risk**: Performance impact (minimal conversion overhead)

## Success Metrics

### Immediate (After Fix)
- [ ] `/api/plans/current` returns 200 for STUDENT plan users
- [ ] No `'UserPlan.STUDENT' is not among the defined enum values` errors
- [ ] All existing tests pass

### Long-term (Architecture Health)
- [ ] Clean separation between domain enums and database values
- [ ] Infrastructure handles all persistence concerns
- [ ] Core layer remains database-agnostic

## Implementation Checklist

### Day 1 - Critical Fixes
- [ ] Fix `plan_configuration_repository.py` line 22
- [ ] Fix `user_repository.py` enum conversions
- [ ] Deploy hotfix to production

### Day 2 - Testing
- [ ] Add unit tests for enum conversion
- [ ] Add integration test for STUDENT plan
- [ ] Verify all plan types work correctly

### Day 3 - Architecture Cleanup
- [ ] Create EnumConverter helper class
- [ ] Refactor repositories to use helper
- [ ] Document enum handling pattern

## Lessons Learned

### What Went Wrong
1. **Incomplete WP5 Implementation**: Domain-to-ORM conversion wasn't fully implemented
2. **Missing Tests**: No tests for non-FREE plan types
3. **Assumption Error**: Assumed SQLAlchemy would handle enum conversion automatically

### What Went Right
1. **Clean Architecture Structure**: Made bug easy to isolate
2. **Proper Layering**: Core services unaffected, fix only needed in infrastructure
3. **Type Safety**: Python enums caught the issue at runtime vs silent failure

### Future Prevention
1. **Comprehensive Testing**: Test all enum values, not just defaults
2. **Conversion Layer**: Explicit conversion at infrastructure boundaries
3. **Code Review Focus**: Check domain-to-persistence mappings carefully

## References

- Original WP5 Implementation: `docs/features/refactor-architecture/workpackages/wp5-domain-orm-convergence.md`
- Clean Architecture Rules: `docs/features/refactor-architecture/architectural-rules.md`
- Error Logs: User report showing `'UserPlan.STUDENT'` error
- Database Migration: `alembic/versions/04a3991223d9_add_student_and_coaching_school_plans.py`

## Appendix: Error Stack Trace

```
Error: 'UserPlan.STUDENT' is not among the defined enum values.
Enum name: userplan.
Possible values: ['free', 'student', 'pro', 'enterprise', 'coaching_school'].

Location: plan_configuration_repository.py:22
Query: PlanConfigurationModel.plan_type == UserPlan.STUDENT
Expected: PlanConfigurationModel.plan_type == 'student'
```

---

## Status Update - 2025-01-17

### ✅ Code Fixes Implemented
- **Infrastructure Layer**: All repository enum conversions fixed
- **Use Case Layer**: Fixed dataclass access patterns for PlanLimits/PlanFeatures/PlanPricing
- **Import Dependencies**: Corrected core services to use domain models instead of legacy models

### 🚨 **CRITICAL**: Verification Required

**Current Status**: Code changes implemented but **NOT VERIFIED** with real authentication.

**Next Actions Required**:

#### 1. **Create Test Authentication Token** (P0 - Critical)
```bash
# Create temporary test token for STUDENT plan user
# Document token creation method and expiry
```

#### 2. **Real API Verification** (P0 - Critical)
```bash
# Test with actual authentication
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/plans/current

# Must verify:
# - 200 OK status (not 500)
# - Complete JSON response with plan data
# - Correct plan limits and features
```

#### 3. **Multiple Plan Type Testing** (P1 - High)
- Test with FREE plan users
- Test with PRO plan users
- Test with STUDENT plan users
- Document actual responses for each

#### 4. **End-to-End Frontend Testing** (P1 - High)
- Start frontend dev server
- Login with STUDENT plan user
- Navigate to billing/plans page
- Verify no console errors
- Verify plan data displays correctly

### 🔧 **Technical Debt to Address**

#### Phase 4: Architecture Improvements (P2 - Medium)
- [ ] Create centralized `EnumConverter` helper class
- [ ] Refactor all repositories to use common conversion patterns
- [ ] Add integration tests for all enum conversion scenarios
- [ ] Document enum handling patterns in architecture docs

#### Phase 5: Testing Infrastructure (P2 - Medium)
- [ ] Create automated test suite for authenticated API endpoints
- [ ] Add plan-specific test users in test database
- [ ] Implement temporary token generation for testing
- [ ] Add enum conversion unit tests

### 📋 **Verification Checklist**

**Before marking as RESOLVED**:
- [ ] ✅ Real authenticated API call returns 200 OK
- [ ] ✅ JSON response contains complete plan data
- [ ] ✅ Multiple plan types tested successfully
- [ ] ✅ Frontend displays plan information without errors
- [ ] ✅ No enum conversion errors in logs
- [ ] ✅ Evidence documented per CLAUDE.md standards

### 🎯 **Success Criteria**

The bug is considered **RESOLVED** only when:
1. **Real authenticated users** can access `/api/v1/plans/current`
2. **Complete plan data** is returned (not just 401/200 status)
3. **All plan types** (FREE, STUDENT, PRO) work correctly
4. **Frontend integration** works without console errors
5. **Evidence documented** according to API Testing Standards

### 📝 **API Testing Standards Compliance**

Per new CLAUDE.md rules, verification must include:
- **Endpoint Tested**: `/api/v1/plans/current`
- **User Tested**: [specific user email] ([plan type])
- **Authentication**: [token type and expiry]
- **Response Status**: 200 OK
- **Response Data**: [complete JSON response]
- **Before Fix**: 500 Internal Server Error
- **After Fix**: [actual working response]

---

**Document Status**: 🟡 Code Implemented - Verification Pending
**Next Action**: Create test authentication token and verify with real API calls
**Author**: Clean Architecture Team
**Created**: 2025-01-17
**Updated**: 2025-01-17
**Priority**: P0 - Must verify before claiming resolution