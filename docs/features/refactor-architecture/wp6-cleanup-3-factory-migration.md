# WP6-Cleanup-3: Factory Pattern Migration - Complete Clean Architecture

**Status**: 🔥 **Critical Priority** (Not Started)
**Work Package**: WP6-Cleanup-3 - Factory Pattern Migration Complete
**Epic**: Clean Architecture Cleanup Phase

## Overview

Complete the factory pattern migration that is currently blocking Clean Architecture completion. This removes the last architectural violations and ensures proper dependency injection throughout the system.

## User Value Statement

**As a developer**, I want **consistent dependency injection patterns across all API endpoints** so that **the codebase is maintainable, testable, and follows Clean Architecture principles**.

## Business Impact

- **Technical Debt**: Removes final architecture violations blocking completion
- **Code Quality**: Enables proper testing and maintenance
- **Development Velocity**: Consistent patterns improve development speed

## Critical TODOs Being Resolved

### 🔥 Factory Pattern Completion
- `src/coaching_assistant/infrastructure/factories.py:442`
  ```python
  # TODO: Remove after all API endpoints migrate to factory pattern (WP2-WP4)
  ```
- `src/coaching_assistant/infrastructure/factories.py:457`
  ```python
  # TODO: Add deprecation warning once API migration is complete
  ```

### 🔥 Legacy Model Dependencies (40+ files)
All files importing from `coaching_assistant.models.*` need migration to use factory-injected repositories:
- `src/coaching_assistant/api/v1/dependencies.py:166,178,190` - UserRole imports
- `src/coaching_assistant/api/v1/usage.py:12,13` - User, UsageAnalytics imports
- `src/coaching_assistant/api/v1/plans.py:16` - UserPlan import
- `src/coaching_assistant/core/services/usage_tracking_use_case.py:19` - User, UserPlan imports
- **Plus 35+ other files** with similar legacy imports

## Architecture Compliance Issues Fixed

### Current Violations
- **Mixed Dependency Patterns**: Some endpoints use factories, others use direct DB access
- **Legacy Model Imports**: 40+ files still importing from root models directory
- **Architecture Violations**: Core services importing SQLAlchemy Session directly

### Clean Architecture Solutions
- **Consistent Factory Pattern**: All API endpoints use factory-injected use cases
- **Repository Port Usage**: All data access through repository ports only
- **Legacy Model Elimination**: Remove all imports from `coaching_assistant.models.*`

## Implementation Tasks

### 1. Complete API Endpoint Migration
Migrate remaining endpoints to use factory pattern exclusively:

#### Dependencies Module Migration
- **File**: `src/coaching_assistant/api/v1/dependencies.py`
- **Current Issues**: Direct UserRole imports, mixed patterns
- **Solution**: Use factory-injected user repository for role checking

#### Usage API Migration
- **File**: `src/coaching_assistant/api/v1/usage.py`
- **Current Issues**: Direct User, UsageAnalytics imports
- **Solution**: Use factory-injected repositories and use cases

#### Plans API Migration
- **File**: `src/coaching_assistant/api/v1/plans.py`
- **Current Issues**: Direct UserPlan import
- **Solution**: Use factory-injected plan management use case

#### Admin APIs Migration
- **Files**: `src/coaching_assistant/api/v1/admin.py`, `src/coaching_assistant/api/v1/admin_reports.py`
- **Current Issues**: Direct model imports for admin operations
- **Solution**: Create admin-specific use cases with factory injection

### 2. Core Services Legacy Cleanup
Remove legacy imports from core services:

#### Usage Tracking Use Case
- **File**: `src/coaching_assistant/core/services/usage_tracking_use_case.py`
- **Issue**: Imports User, UserPlan from legacy models
- **Solution**: Use injected user repository, remove direct imports

#### Plan Management Use Case
- **File**: `src/coaching_assistant/core/services/plan_management_use_case.py`
- **Issue**: Imports from legacy models
- **Solution**: Use domain models from core, not legacy models

### 3. Service Layer Migration
Migrate remaining service classes to use repository ports:

#### Legacy Services
- **Files**: `src/coaching_assistant/services/usage_tracker.py`, `src/coaching_assistant/services/permissions.py`
- **Issue**: Direct model imports and database access
- **Solution**: Convert to use cases or migrate to use factory-injected repositories

### 4. Remove Legacy Factory Functions
- **File**: `src/coaching_assistant/infrastructure/factories.py`
- **Requirements**:
  - Remove temporary compatibility functions
  - Add deprecation warnings for any remaining legacy patterns
  - Clean up factory documentation

### 5. Legacy Model Directory Cleanup
After all imports are migrated:
- **Directory**: `src/coaching_assistant/models/`
- **Action**: Mark for deletion or move to legacy package
- **Verification**: No active imports remain

## E2E Demonstration Workflow

### Demo Script: "Clean Architecture API Consistency"

**Pre-requisites**: All API endpoints migrated to factory pattern

1. **Verify API Dependency Injection** - Check all endpoints use factories
   ```bash
   # Should show zero results
   grep -r "from.*\.models\." src/coaching_assistant/api/
   ```
   - Expected: No legacy model imports in API layer

2. **Test User Management Workflow** - GET/POST `/api/v1/users`
   - Verify user operations use repository pattern
   - Expected: All operations work through use cases

3. **Test Plan Management Workflow** - GET `/api/v1/plans/current`
   - Verify plan operations use factory-injected use cases
   - Expected: Clean dependency injection, no direct model access

4. **Test Admin Operations** - GET `/api/v1/admin/reports/daily`
   - Verify admin operations use proper use case pattern
   - Expected: Consistent architecture patterns

5. **Verify Core Services Purity** - Check core layer compliance
   ```bash
   # Should show zero results
   grep -r "SQLAlchemy\|Session\|get_db" src/coaching_assistant/core/services/
   ```
   - Expected: Core services have zero infrastructure dependencies

6. **Factory Pattern Consistency** - Verify all factories work
   ```python
   # Test all factory functions can create use cases
   from coaching_assistant.infrastructure.factories import *
   # All factory functions should work without errors
   ```

## Success Metrics

### Architecture Validation
- ✅ Zero legacy model imports in entire codebase
- ✅ All API endpoints use factory pattern exclusively
- ✅ Core services have zero infrastructure dependencies
- ✅ Repository pattern used for all data access
- ✅ Factory functions provide complete dependency injection

### Code Quality Validation
- ✅ Consistent patterns across all API endpoints
- ✅ Clean separation of concerns maintained
- ✅ Dependency injection working for all use cases
- ✅ Zero architectural violations detected

### Testing Validation
- ✅ Unit tests work with factory-provided dependencies
- ✅ Integration tests use consistent patterns
- ✅ API tests validate factory-injected behavior
- ✅ All existing functionality continues working

## Testing Strategy

### Architectural Compliance Tests (Required)
```bash
# Verify no legacy imports
./scripts/check_architecture.py --check-legacy-imports

# Verify factory pattern usage
./scripts/check_architecture.py --check-factory-usage

# Verify core layer purity
./scripts/check_architecture.py --check-core-dependencies
```

### Unit Tests (Required)
```bash
# Test factory functions
pytest tests/unit/infrastructure/test_factories.py -v

# Test migrated use cases
pytest tests/unit/core/services/ -v
```

### Integration Tests (Required)
```bash
# Test API endpoints with factory pattern
pytest tests/integration/api/ -v

# Test repository implementations
pytest tests/integration/infrastructure/repositories/ -v
```

### E2E Tests (Required)
```bash
# Complete workflow testing
pytest tests/e2e/test_factory_pattern_consistency.py -v
```

## Dependencies

### Blocked By
- **WP6-Cleanup-1**: Speaker role implementation (if using shared factories)

### Blocking
- **Legacy Model Removal**: Cannot remove legacy models until this is complete
- **Architecture Documentation**: Cannot finalize architecture docs until this is done

## Definition of Done

- [ ] Zero imports from `coaching_assistant.models.*` in entire codebase
- [ ] All API endpoints use factory pattern exclusively
- [ ] All TODO comments related to factory migration removed
- [ ] Core services have zero infrastructure dependencies
- [ ] Repository pattern used for all data access
- [ ] Factory functions provide complete dependency injection
- [ ] Architectural compliance tests pass
- [ ] All existing API functionality continues working
- [ ] Code review completed and approved
- [ ] Legacy compatibility functions removed
- [ ] Documentation updated with final architecture patterns

## Risk Assessment

### Technical Risks
- **Medium**: Large-scale refactoring across many files
- **Medium**: Potential for breaking existing functionality
- **Low**: Performance impact (factory overhead minimal)

### Mitigation Strategies
- **Incremental Migration**: Migrate one API module at a time
- **Comprehensive Testing**: Run full test suite after each module migration
- **Rollback Plan**: Keep legacy patterns until full migration verified

## Implementation Approach

### Phase 1: API Layer Migration (Day 1)
- Migrate API endpoints one module at a time
- Verify each module works before proceeding
- Run integration tests after each migration

### Phase 2: Core Services Cleanup (Day 2)
- Remove legacy imports from core services
- Verify business logic continues working
- Run unit tests for all modified use cases

### Phase 3: Factory Cleanup (Day 3)
- Remove temporary compatibility functions
- Add architectural compliance tests
- Verify E2E workflows work correctly

## Delivery Timeline

- **Estimated Effort**: 3 days (1 developer)
- **Critical Path**: API migration → core cleanup → factory finalization
- **Deliverable**: 100% Clean Architecture compliance with zero legacy dependencies

---

## Related Work Packages

- **WP6-Cleanup-1**: May share some factory functions (coordinate if needed)
- **WP6-Cleanup-2**: Independent (can run in parallel)
- **WP6-Cleanup-4**: Enables final legacy model removal

This work package completes the Clean Architecture migration and removes the last technical debt blocking architectural compliance.