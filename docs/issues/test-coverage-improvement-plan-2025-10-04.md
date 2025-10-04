# Test Coverage Improvement Plan - 2025-10-04

## Current Status (After Phase 5)

- **Test Results**: 610 passed, 0 failed, 0 errors
- **Warning Count**: 905 warnings
- **Code Coverage**: 46% (target: 85%)
- **Test Execution Time**: 5-6 seconds

## Warning Analysis

### Warning Breakdown (905 total)

**By Category**:
1. **ResourceWarning: unclosed database** (~850 warnings, 94%)
   - Source: SQLAlchemy internal + pytest-cov SQLite connections
   - Location: SQLAlchemy internals, coverage library
   - **Impact**: None - Test-only, properly managed in production
   - **Action**: Not actionable - library internal behavior

2. **DeprecationWarning: datetime.utcnow()** (~50 warnings, 5.5%)
   - Source: SQLAlchemy library code (not our code)
   - Location: `sqlalchemy/sql/schema.py:3624`
   - **Impact**: Low - Already fixed in our code
   - **Action**: Wait for SQLAlchemy update

3. **Other warnings** (~5 warnings, 0.5%)
   - Various pytest and test setup warnings
   - **Impact**: Minimal
   - **Action**: Monitor but not critical

### Warning Priority Assessment

✅ **CONCLUSION**: All warnings are from external libraries or test infrastructure
- ❌ **No actionable warnings in our production code**
- ✅ **Our code is clean** - all datetime.utcnow() already fixed
- ✅ **Test infrastructure is sound**
- **Focus shift recommended**: Warnings → Coverage improvement

## Coverage Analysis

### Critical Low-Coverage Modules (<50%)

**Priority 1: Core Business Logic Services (High Risk)**
| Module | Coverage | Priority | Reason |
|--------|----------|----------|---------|
| `usage_tracking_use_case.py` | 18% | 🔴 CRITICAL | Payment/billing errors could cause revenue loss |
| `coaching_session_management_use_case.py` | 20% | 🔴 CRITICAL | Session data integrity issues |
| `transcript_upload_use_case.py` | 20% | 🔴 CRITICAL | File upload errors, data loss risk |
| `client_management_use_case.py` | 20% | 🔴 CRITICAL | Client data consistency |
| `plan_management_use_case.py` | 29% | 🔴 HIGH | Subscription/billing logic |
| `billing_analytics_use_case.py` | 34% | 🔴 HIGH | Revenue reporting accuracy |
| `ecpay_service.py` | 40% | 🔴 HIGH | Payment gateway integration |

**Priority 2: Data Access Layer (Medium Risk)**
| Module | Coverage | Priority | Reason |
|--------|----------|----------|---------|
| `infrastructure/db/session.py` | 0% | 🟠 HIGH | Database session management |
| `memory_repositories.py` | 0% | 🟠 MEDIUM | Test/dev fallback |
| `user_repository.py` | 16% | 🟠 HIGH | User data integrity |
| `coach_profile_repository.py` | 14% | 🟠 HIGH | Profile data integrity |
| `usage_analytics_repository.py` | 22% | 🟠 MEDIUM | Analytics accuracy |
| `session_repository.py` | 25% | 🟠 MEDIUM | Session persistence |

**Priority 3: Service Layer (Lower Risk)**
| Module | Coverage | Priority | Reason |
|--------|----------|----------|---------|
| `lemur_transcript_smoother.py` | 21% | 🟡 MEDIUM | AI integration, error handling |
| `plan_configuration_service.py` | 32% | 🟡 LOW | Configuration management |

## Improvement Strategy

### Phase 1: Warning Acceptance (Current)
**Status**: ✅ COMPLETED
- All warnings analyzed and classified
- No actionable warnings in production code
- Focus shifted to coverage improvement

### Phase 2: Error Handling Coverage (High Priority)

**Goal**: Increase coverage from 46% → 65% by testing error paths

**Approach**: Test exception handling and edge cases in critical modules

#### 2.1 Payment & Billing Critical Path (Priority 1)

**Target Modules**:
1. **`usage_tracking_use_case.py`** (18% → 60%)
   - Database failure scenarios
   - Invalid usage data handling
   - Concurrent update conflicts
   - Usage limit violations
   - Cost calculation edge cases

2. **`ecpay_service.py`** (40% → 70%)
   - Payment gateway timeouts
   - Invalid payment data
   - Webhook signature verification failures
   - Refund/cancellation errors
   - Network failures

3. **`billing_analytics_use_case.py`** (34% → 65%)
   - Missing data scenarios
   - Calculation overflow/underflow
   - Date range edge cases
   - Aggregation errors

**Expected Impact**:
- Test count: +90 tests
- Coverage increase: ~15%
- Time investment: 2-3 days

#### 2.2 Data Integrity Critical Path (Priority 1)

**Target Modules**:
1. **`coaching_session_management_use_case.py`** (20% → 60%)
   - Session creation failures
   - Update conflicts
   - Deletion cascades
   - Invalid state transitions

2. **`transcript_upload_use_case.py`** (20% → 60%)
   - File upload failures
   - Invalid file formats
   - Storage errors
   - Concurrent uploads

3. **`client_management_use_case.py`** (20% → 60%)
   - Duplicate client detection
   - Invalid data validation
   - Relationship integrity

**Expected Impact**:
- Test count: +80 tests
- Coverage increase: ~12%
- Time investment: 2-3 days

#### 2.3 Repository Error Handling (Priority 2)

**Target Modules**:
1. **`user_repository.py`** (16% → 50%)
   - Database constraint violations
   - Concurrent update detection
   - Query failures

2. **`coach_profile_repository.py`** (14% → 50%)
   - Profile validation
   - Image upload errors
   - Data consistency

3. **`session_repository.py`** (25% → 55%)
   - Transaction rollback scenarios
   - Foreign key violations

**Expected Impact**:
- Test count: +60 tests
- Coverage increase: ~8%
- Time investment: 1-2 days

### Phase 3: Happy Path Coverage (Medium Priority)

**Goal**: Coverage 65% → 75%

**Approach**: Add tests for normal operation flows in low-coverage services

**Target Modules**:
- `plan_management_use_case.py` (29% → 60%)
- `lemur_transcript_smoother.py` (21% → 50%)
- `plan_configuration_service.py` (32% → 60%)

**Expected Impact**:
- Test count: +40 tests
- Coverage increase: ~10%
- Time investment: 1-2 days

### Phase 4: Edge Cases & Integration (Low Priority)

**Goal**: Coverage 75% → 85%

**Approach**: Test rare scenarios and integration points

**Target Areas**:
- API boundary validation
- Multi-user concurrency scenarios
- Performance edge cases
- Resource cleanup

**Expected Impact**:
- Test count: +30 tests
- Coverage increase: ~10%
- Time investment: 1-2 days

## Implementation Roadmap

### Week 1: Payment & Billing Critical Path
- **Days 1-3**: `usage_tracking_use_case.py` error handling
  - Database failure mocking
  - Usage limit violation tests
  - Cost calculation edge cases
  - Target: 18% → 60% (+42%)

- **Days 4-5**: `ecpay_service.py` error handling
  - Payment gateway timeout simulation
  - Webhook validation tests
  - Network failure scenarios
  - Target: 40% → 70% (+30%)

**Deliverable**: ~90 new error handling tests, +15% coverage

### Week 2: Data Integrity Critical Path
- **Days 1-2**: `coaching_session_management_use_case.py`
  - Session lifecycle error tests
  - State transition validation
  - Target: 20% → 60% (+40%)

- **Days 3-4**: `transcript_upload_use_case.py`
  - File upload error scenarios
  - Storage failure handling
  - Target: 20% → 60% (+40%)

- **Day 5**: `client_management_use_case.py`
  - Duplicate detection tests
  - Validation error handling
  - Target: 20% → 60% (+40%)

**Deliverable**: ~80 new tests, +12% coverage

### Week 3: Repository Layer & Polish
- **Days 1-2**: Repository error handling
  - Database constraint violation tests
  - Concurrent update scenarios
  - Target: +8% coverage

- **Days 3-4**: Happy path coverage
  - Normal operation flows
  - Integration tests
  - Target: +10% coverage

- **Day 5**: Review and documentation
  - Update test documentation
  - Performance benchmarking
  - CI/CD optimization

**Deliverable**: ~100 new tests, +18% coverage

## Success Metrics

### Coverage Targets
- **Week 1 End**: 46% → 61% (+15%)
- **Week 2 End**: 61% → 73% (+12%)
- **Week 3 End**: 73% → 85%+ (+12%+)

### Quality Metrics
- **Test Reliability**: 100% pass rate maintained
- **Test Speed**: <10 seconds for full suite
- **Error Detection**: 90%+ error path coverage in critical modules

### Business Impact
- **Risk Reduction**: Payment/billing error paths fully tested
- **Data Integrity**: Session/client management error handling verified
- **Confidence**: Safe deployments with comprehensive error coverage

## Test Writing Guidelines

### Error Handling Test Pattern
```python
def test_service_handles_database_failure():
    """Test that service gracefully handles database failures."""
    # Arrange
    service = ServiceUnderTest(mock_failed_db)

    # Act & Assert
    with pytest.raises(ServiceError) as exc_info:
        service.perform_critical_operation()

    assert "database" in str(exc_info.value).lower()
    assert exc_info.value.code == ErrorCode.DATABASE_ERROR
```

### Coverage Priority Rules
1. **Error paths before happy paths** in critical services
2. **Exception handling** in all repository methods
3. **Edge cases** for business logic calculations
4. **Concurrent scenarios** for state management
5. **Integration boundaries** for external services

## Risks & Mitigation

### Risk 1: Test Maintenance Burden
**Mitigation**:
- Use factories and fixtures for test data
- Parametrize similar test cases
- Document test patterns

### Risk 2: Slow Test Execution
**Mitigation**:
- Keep unit tests fast (<1s each)
- Use in-memory databases
- Mock external dependencies

### Risk 3: False Confidence
**Mitigation**:
- Test actual error conditions, not just mocks
- Include integration tests for critical paths
- Regular production error log review

## Next Steps

1. ✅ Review and approve this plan
2. Start Week 1: Payment & Billing Critical Path
3. Daily: Run tests and update coverage metrics
4. Weekly: Review progress and adjust priorities
5. Continuous: Document patterns and learnings

---

*Generated: 2025-10-04*
*Status: Ready for Implementation*
