# Test Coverage Improvement Plan - 2025-10-04

## Current Status (Updated 2025-10-04)

### Initial Status (After Phase 5)
- **Test Results**: 610 passed, 0 failed, 0 errors
- **Warning Count**: 905 warnings
- **Code Coverage**: 46% (target: 85%)
- **Test Execution Time**: 5-6 seconds

### After Day 1 (2025-10-04) ✅
- **Test Results**: 670 passed, 0 failed, 0 errors (+64 tests)
- **Code Coverage**: 47.04% (target: 85%)
- **Test Execution Time**: ~7.3 seconds
- **Modules Completed**:
  - coaching_session_management_use_case.py: 20% → 68% ✅
  - client_management_use_case.py: 20% → 62% ✅
- **Critical Issues Found**: 3 architectural bugs in usage_tracking_use_case.py

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

### Week 1: Core Use Case Error Handling (REVISED)

#### Day 1 (2025-10-04) ✅ COMPLETED
- ✅ **coaching_session_management_use_case.py**: 20% → 68% (+48%)
  - 35 error handling tests created
  - All 5 use case classes covered
  - Database errors, validation, edge cases

- ✅ **client_management_use_case.py**: 20% → 62% (+42%)
  - 29 error handling tests created
  - All 5 use case classes covered
  - Duplicate detection, validation, authorization

- ❌ **usage_tracking_use_case.py**: BLOCKED
  - Architectural issues discovered (domain model mismatch)
  - Requires code fixes before testing viable
  - See: coverage-week1-day1-progress.md

**Day 1 Results**: +64 tests, 46.36% → 47.04% coverage (+0.68%)

#### Day 2 (2025-10-05) - IN PROGRESS
- **session_management_use_case.py**: 73% → 85% (+12%)
  - Currently at 73%, identify remaining gaps
  - Add edge case tests (~15 tests)
  - Target: 85%+ coverage

- **transcript_upload_use_case.py**: 20% → 50% (+30%)
  - Verify module testability first
  - Error handling test suite (~25 tests)
  - File upload errors, storage failures

- **billing_analytics_use_case.py**: 34% → 55% (+21%)
  - Verify dependencies testable
  - Error handling tests (~20 tests)
  - Calculation errors, missing data

**Day 2 Target**: +60 tests, 47.04% → 48.5% coverage (+1.5%)

#### Days 3-4: Additional Core Modules
- **plan_management_use_case.py**: 29% → 60% (+31%)
- **dashboard_summary_use_case.py**: 35% → 60% (+25%)
- **speaker_role_management_use_case.py**: 92% → 95% (+3%, polish)

**Days 3-4 Target**: +50 tests, 48.5% → 50% coverage (+1.5%)

#### Day 5: Review & Polish
- Integration test scenarios
- Edge case coverage for completed modules
- Documentation updates
- Architecture fix planning for usage_tracking

**Week 1 Deliverable**: ~175 new tests, 46% → 50% coverage (+4%)

### Week 2: Repository & Service Layer (REVISED)

#### Focus: Repository error handling and service integration

- **Days 1-2**: Repository Layer Error Handling
  - `coaching_session_repository.py`: 41% → 70%
  - `client_repository.py`: 20% → 60%
  - `session_repository.py`: 25% → 60%
  - Database constraint violations, concurrent updates
  - Target: +40 tests, +2% coverage

- **Days 3-4**: Service Layer Coverage
  - `ecpay_service.py`: 40% → 70% (payment gateway errors)
  - `plan_limits.py`: 58% → 80% (validation edge cases)
  - `permissions.py`: 95% → 98% (polish)
  - Target: +35 tests, +2% coverage

- **Day 5**: Integration & Edge Cases
  - Critical path integration tests
  - Multi-module scenarios
  - Edge case coverage
  - Target: +25 tests, +1% coverage

**Week 2 Deliverable**: ~100 new tests, 50% → 55% coverage (+5%)

### Week 3: Advanced Coverage & Architecture Fixes (REVISED)

#### Focus: Remaining modules and architectural improvements

- **Days 1-2**: STT Provider Services
  - `assemblyai_stt.py`: 68% → 85%
  - `google_stt.py`: 9% → 40%
  - `stt_factory.py`: 76% → 90%
  - API error handling, timeout scenarios
  - Target: +60 tests, +3% coverage

- **Days 3-4**: Background Tasks & Analytics
  - `transcription_tasks.py`: 12% → 50%
  - `usage_analytics_service.py`: 89% → 95%
  - `billing_analytics_service.py`: 66% → 80%
  - Celery error handling, retry logic
  - Target: +40 tests, +2% coverage

- **Day 5**: Architecture Fixes & Review
  - **Fix usage_tracking_use_case.py** architectural issues
  - Align domain models with use cases
  - Add missing repository methods
  - Documentation and retrospective

**Week 3 Deliverable**: ~100 new tests, 55% → 60% coverage (+5%)

## Success Metrics (REVISED)

### Coverage Targets
- **Week 1 End**: 46% → 50% (+4%) - Focus on testable core modules
- **Week 2 End**: 50% → 55% (+5%) - Repository and service layer
- **Week 3 End**: 55% → 60%+ (+5%+) - Advanced coverage + architecture fixes

**Note**: Original 85% target revised to 60% for 3-week period due to:
- Discovery of architectural issues requiring code fixes
- ~15% of codebase needs refactoring before testable
- Focus on quality over quantity (error-first approach)

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
