# Clean Architecture Compliance Cleanup

## Status: Planning Phase
**Created**: 2025-09-29
**Priority**: High - Architecture Debt Reduction
**Impact**: Test Suite Reliability + Code Maintainability

## Problem Statement

Several services in the codebase violate clean architecture principles by directly injecting `Session` objects instead of using the repository pattern. This creates tight coupling between business logic and infrastructure, making testing difficult and violating the dependency inversion principle.

### Current Architectural Violations

**Services directly using `Session`**:
1. `BillingAnalyticsService` (`src/coaching_assistant/services/billing_analytics_service.py:24`)
2. `UsageAnalyticsService` (`src/coaching_assistant/services/usage_analytics_service.py:23`)
3. `PermissionsService` (`src/coaching_assistant/services/permissions.py:16`)
4. `UsageTracker` (`src/coaching_assistant/services/usage_tracker.py:24`)
5. `UsageTrackingService` (`src/coaching_assistant/services/usage_tracking.py:77`)

**According to CLAUDE.md architecture rules**:
- ❌ Core services: ZERO SQLAlchemy imports or Session dependencies
- ❌ Repository pattern: All data access through repository ports
- ❌ Dependency direction: Core ← Infrastructure

## Comprehensive Plan: Test Improvements + Architecture Cleanup

### Phase 1: Complete Critical Test Fixes (No Production Changes) ⚡
**Goal**: Complete remaining safe test fixes from Phase 3 (reduce 40→25 failures)

**Current Status** (from test-improvement-2025-09-29.md):
- Test Failures: 52 → 40 (23% reduction, 12 tests fixed)
- Test Errors: 24 → 0 (100% elimination)
- Test Warnings: 1326 → 736 (44% reduction)

**Remaining Work**:
- [ ] Fix usage analytics service tests (6 failures) - Domain model attribute issues
- [ ] Fix SQLAlchemy/Database mock issues (12 failures) - Complex query mocking
- [ ] Fix ECPay/Payment service tests (14 failures) - Business logic complexity
- [ ] Fix session management tests (3 failures) - Service integration issues
- [ ] Fix LeMUR/AI processing tests (5 failures) - External service dependencies

**Risk Level**: 🟢 Safe - Test-only changes, no production code modification

### Phase 2: Architecture Compliance Fixes 🏗️
**Goal**: Fix services violating clean architecture principles

#### 2.1 Create Missing Repository Interfaces
- [ ] Create `BillingAnalyticsRepositoryPort` interface
- [ ] Create `UsageHistoryRepositoryPort` interface
- [ ] Create `UsageLogRepositoryPort` interface
- [ ] Create `PermissionRepositoryPort` interface
- [ ] Extend existing repository ports as needed

#### 2.2 Implement Repository Adapters
- [ ] Implement `SQLAlchemyBillingAnalyticsRepository`
- [ ] Implement `SQLAlchemyUsageHistoryRepository`
- [ ] Implement `SQLAlchemyUsageLogRepository`
- [ ] Implement `SQLAlchemyPermissionRepository`
- [ ] Create in-memory implementations for testing

#### 2.3 Refactor Services to Use Repositories
- [ ] **BillingAnalyticsService**: Replace `Session` with repository interfaces
- [ ] **UsageAnalyticsService**: Replace `Session` with repository interfaces
- [ ] **PermissionsService**: Replace `Session` with repository interfaces
- [ ] **UsageTracker**: Replace `Session` with repository interfaces
- [ ] **UsageTrackingService**: Replace `Session` with repository interfaces

#### 2.4 Update Dependency Injection
- [ ] Update FastAPI dependencies to inject repositories
- [ ] Update service factories to wire repositories
- [ ] Update test fixtures to use in-memory repositories

**Risk Level**: 🔴 High - Production code changes requiring full verification

### Phase 3: Validate Architecture Compliance 🔍
**Goal**: Ensure all architectural rules are followed

#### 3.1 Architecture Compliance Checks
- [ ] Run `scripts/check_architecture.py` (if exists)
- [ ] Verify no services directly import `sqlalchemy.orm.Session`
- [ ] Verify core services have zero SQLAlchemy dependencies
- [ ] Verify all data access goes through repository ports

#### 3.2 Test Suite Validation
- [ ] All unit tests use in-memory repositories
- [ ] Integration tests use real database repositories
- [ ] No test directly mocks SQLAlchemy Session
- [ ] All repository interfaces have both implementations

#### 3.3 Documentation Updates
- [ ] Update architecture examples in `docs/claude/architecture.md`
- [ ] Update service patterns in project documentation
- [ ] Create migration guide for other teams

**Risk Level**: 🟡 Medium - Verification and documentation

## Implementation Strategy

### Safety Protocol
**Before ANY production code change:**
1. Create feature branch for isolation
2. Document current behavior and APIs
3. Identify all affected components and tests

**After ANY production code change:**
1. Run `make lint` (mandatory)
2. Run `make test` (verify no new failures)
3. Start API server and run smoke tests
4. Verify API responses unchanged
5. Check database operations still work

### Rollback Plan
**If any production change causes issues:**
1. Revert specific commits
2. Document the issue and alternative approaches
3. Consult before proceeding

## Expected Outcomes

### After Phase 1 (Test Fixes)
- **Test Results**: 40 → 25 failed tests (38% improvement)
- **Test Reliability**: More stable test runs
- **Developer Experience**: Faster debugging

### After Phase 2 (Architecture Fixes)
- **Architecture**: 100% clean architecture compliance
- **Testability**: All services easily unit testable
- **Maintainability**: Decoupled business logic from infrastructure
- **Future Development**: Easier to add new data sources

### After Phase 3 (Validation)
- **Documentation**: Clear architectural patterns
- **Team Knowledge**: Migration guide for future development
- **Quality Assurance**: Automated architecture compliance checks

## Technical Details

### Repository Pattern Implementation

**Before (Violation)**:
```python
class BillingAnalyticsService:
    def __init__(self, db: Session):  # ❌ Direct Session dependency
        self.db = db

    def get_analytics(self):
        return self.db.query(BillingAnalytics).all()  # ❌ Direct SQLAlchemy
```

**After (Compliant)**:
```python
class BillingAnalyticsService:
    def __init__(self, billing_repo: BillingAnalyticsRepositoryPort):  # ✅ Repository port
        self.billing_repo = billing_repo

    def get_analytics(self):
        return self.billing_repo.find_all()  # ✅ Repository interface
```

### Testing Strategy
- **Unit Tests**: Use in-memory repository implementations
- **Integration Tests**: Use real SQLAlchemy repository implementations
- **API Tests**: Full stack with database

## Success Metrics

### Phase 1 Targets
- **Test Failures**: 40 → 25 failures (38% improvement)
- **Error Reduction**: Maintain 0 errors
- **Warning Reduction**: Continue reducing warnings

### Phase 2 Targets
- **Architecture Compliance**: 0 services directly using Session
- **Repository Coverage**: 100% data access through repositories
- **Test Coverage**: Maintain >85% coverage after refactoring

### Phase 3 Targets
- **Documentation**: Complete migration guide
- **Automation**: Architecture compliance checks in CI
- **Team Adoption**: Clear patterns for future development

## Dependencies

### Prerequisites
- Current test improvement work (Phase 3 from test-improvement-2025-09-29.md)
- Understanding of existing repository implementations
- Review of current dependency injection patterns

### Potential Blockers
- Complex queries in services that are hard to abstract
- Performance implications of additional abstraction layer
- Existing integration test dependencies

## Timeline Estimate

**Total Effort**: 4-5 days

- **Phase 1**: 1-2 days (complete test fixes)
- **Phase 2**: 2-3 days (architecture refactoring)
- **Phase 3**: 1 day (validation and documentation)

## Next Steps

1. **Complete Phase 1**: Continue with remaining test fixes from test-improvement-2025-09-29.md
2. **Analyze Services**: Deep dive into each violating service to understand refactoring complexity
3. **Design Repositories**: Create interface definitions for missing repository ports
4. **Implement Incrementally**: Start with simplest service (PermissionsService) as proof of concept

---

**Related Documents**:
- `docs/issues/test-improvement-2025-09-29.md` - Current test improvement progress
- `docs/claude/architecture.md` - Clean architecture principles
- `CLAUDE.md` - Project architectural rules