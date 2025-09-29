# Test Suite Improvement Plan - 2025-09-29

## Current Status
- **Test Results**: 52 failed, 531 passed, 3 skipped, 1326 warnings, 24 errors
- **Command**: `make test` (runs unit tests + database integration tests)
- **Total Test Files**: ~79 files (46 unit + 33 integration)

## Test Scope Analysis

### What `make test` Currently Runs:
```bash
pytest tests/unit/ tests/integration/database/ \
    tests/integration/test_transcript_smoother_integration.py \
    -v --color=yes
```

**Included**:
- ✅ Unit tests (`tests/unit/`) - 46 files
- ✅ Database integration tests (`tests/integration/database/`)
- ✅ Transcript smoother integration test
- ✅ SQLite in-memory database testing

**Excluded** (run separately):
- ❌ API tests (`make test-server`) - requires running API server
- ❌ E2E tests (`tests/e2e/`) - browser automation
- ❌ Frontend tests (`cd apps/web && npm test`)
- ❌ Payment tests (`make test-payment`) - requires authentication

## Critical Issues Identified

### 1. ECPay Service Dependency Injection (24 Errors)
**Error Pattern**: `ECPaySubscriptionService.__init__() missing 3 required positional arguments`

**Affected Files**:
- `tests/unit/test_ecpay_api_response_validation.py` (12 errors)
- `tests/unit/test_merchant_trade_no_generation.py` (7 errors)
- Related ECPay test files

**Root Cause**:
- Service constructor changed to require: `settings`, `ecpay_client`, `notification_service`
- Tests still using old constructor signature

**Solution**:
```python
# Current broken test setup
service = ECPaySubscriptionService()  # Missing args

# Fixed test setup with mocks
@pytest.fixture
def ecpay_service(mock_settings, mock_ecpay_client, mock_notification_service):
    return ECPaySubscriptionService(
        settings=mock_settings,
        ecpay_client=mock_ecpay_client,
        notification_service=mock_notification_service
    )
```

### 2. Repository Transaction Management (4 Failures)
**Failed Tests**:
- `test_subscription_repository_transaction_fix.py` (4 tests)

**Error Pattern**: Transaction/commit handling issues in repository tests

**Root Cause**:
- Repository methods expect transaction management
- Tests not providing proper database session context

**Solution**:
- Add proper database session fixtures
- Mock transaction behavior in unit tests
- Ensure proper commit/rollback in test teardown

### 3. Enum Conversion Issues (2 Failures)
**Failed Tests**:
- `test_enum_conversions.py::TestSpeakerRoleConversion`

**Root Cause**:
- Domain enum to database enum conversion broken
- SpeakerRole enum mapping issues

**Solution**:
- Fix enum conversion utilities
- Update test data to match current enum values
- Verify enum mapping consistency

### 4. Contract Violations (6 Failures)
**Categories**:
- User model attribute access issues (3 tests)
- Function signature enforcement (2 tests)
- Import compatibility (1 test)

**Root Cause**:
- User model API changes
- Missing attributes or changed method signatures

### 5. Miscellaneous Service Issues (16 Failures)
**Categories**:
- Receipt generation tests (1 failure)
- Session management tests (2 failures)
- Billing analytics (1 failure)
- Single speaker warnings (multiple failures)
- Various service integration issues

## Warning Analysis (1326 Warnings)

### 1. Datetime Deprecation Warnings (~1300 warnings)
**Pattern**: `datetime.datetime.utcnow() is deprecated`

**Affected Files**:
- `src/coaching_assistant/core/models/user.py:118,120`
- `src/coaching_assistant/core/models/session.py:70`
- `src/coaching_assistant/core/models/transcript.py:153`
- Many test files using datetime.utcnow()

**Solution**:
```python
# Replace this
datetime.datetime.utcnow()

# With this
datetime.datetime.now(datetime.UTC)
```

### 2. Pytest Configuration Warnings (~20 warnings)
**Issues**:
- Unknown pytest marks: `@pytest.mark.integration`
- Test classes with `__init__` constructors
- Collection warnings

**Solution**:
```python
# In pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow running",
]

# Fix test classes
class TestSomething:  # Remove __init__ method
    pass
```

## Regression Prevention Strategy

### Risk Classification

#### 🟢 SAFE FIXES (Test-Only Changes - No Regression Risk)
- **ECPay Service Test Mocks** - Update test fixtures only
- **Import Path Updates** - Fix test imports to use `src.` prefix
- **Repository Transaction Mocks** - Update mock behavior in tests
- **Pytest Configuration** - Configuration file changes only
- **SpeakerRole Enum Tests** - Remove `.OTHER` references (intentionally removed)

#### 🟡 MEDIUM RISK (Minor Production Changes)
- **Enum Conversion Utilities** - If production code needs updates

#### 🔴 HIGH RISK (Production Code Changes - Requires Full Verification)
- **Datetime Deprecation** - 24 production files affected
- **Service Logic Changes** - Any changes to business logic

### Safety Protocol

**Before ANY production code change:**
1. Create git branch for isolation
2. Document current behavior
3. Identify all affected components

**After ANY production code change:**
1. Run `make lint` (mandatory)
2. Run `make test` (verify no new failures)
3. Use subagent to start API server
4. Run smoke tests on critical endpoints
5. Verify API responses unchanged

**If ANY doubt about impact:**
- ❌ STOP and ask for review
- ❌ Don't proceed with change
- ✅ Document the concern and alternative approaches

## Improved Action Plan

### Phase 1: Safe Test Fixes (High Priority - No Regression Risk)
1. **Fix ECPay Service Tests** (24 errors → 0)
   - ✅ Test-only changes
   - Update mock fixtures for 5 required parameters:
     ```python
     @pytest.fixture
     def ecpay_service(mock_user_repo, mock_subscription_repo, mock_settings, mock_ecpay_client, mock_notification_service):
         return ECPaySubscriptionService(
             user_repo=mock_user_repo,
             subscription_repo=mock_subscription_repo,
             settings=mock_settings,
             ecpay_client=mock_ecpay_client,
             notification_service=mock_notification_service
         )
     ```

2. **Fix Import Path Issues** (2 failures → 0)
   - ✅ Test-only changes
   - Update from: `from coaching_assistant.api.auth`
   - Update to: `from src.coaching_assistant.api.v1.auth`

3. **Fix Repository Transaction Tests** (4 failures → 0)
   - ✅ Test-only changes
   - Fix mock session behavior
   - Update test assertions for repository calls

4. **Fix SpeakerRole Enum Tests** (2 failures → 0)
   - ✅ Test-only changes
   - Remove `SpeakerRole.OTHER` references (confirmed intentional removal)

5. **Clean Pytest Configuration** (20+ warnings → 0)
   - ✅ Configuration-only changes
   - Register custom pytest marks in `pyproject.toml`
   - Remove `__init__` methods from test classes

### Phase 2: Production Code Changes (Lower Priority - Full Verification Required)
6. **Update Datetime Usage** (1300+ warnings → 0)
   - ⚠️ Affects 24 production files (14 core models + 10 services)
   - Replace: `datetime.datetime.utcnow()`
   - With: `datetime.datetime.now(datetime.UTC)`
   - **Verification Required:**
     - Run `make lint`
     - Start API server with subagent
     - Run smoke tests on timestamp-dependent endpoints
     - Verify database timestamp formats unchanged

### Phase 3: Remaining Issues (Case-by-Case Review)
7. **Fix Remaining Service Tests** (16 failures → TBD)
   - Receipt generation
   - Session management
   - Billing analytics
   - **Each requires individual assessment for regression risk**

## Expected Outcomes

**After Implementation**:
- ✅ **Test Results**: 0 failed, 583+ passed, 3 skipped, <50 warnings, 0 errors
- ✅ **CI Reliability**: More stable GitHub Actions runs
- ✅ **Developer Experience**: Faster local testing
- ✅ **Code Quality**: Cleaner deprecation warnings

## Implementation Timeline

**Estimated Effort**: 2-3 days
- **Phase 1**: 4-6 hours (critical fixes)
- **Phase 2**: 2-3 hours (warnings cleanup)
- **Phase 3**: 2-3 hours (enum/contract fixes)
- **Phase 4**: 3-4 hours (remaining issues)

## Implementation Strategy

### Phase 1 Execution (Safe Test Fixes)
**Goal**: Reduce from 52 failures to ~15 failures (no regression risk)

**Verification After Each Fix**:
1. Run `make test` after each individual fix
2. Document error count reduction
3. Commit changes with clear descriptions
4. No production code verification needed (test-only changes)

### Phase 2 Execution (Production Code Changes)
**Goal**: Reduce warnings from 1300+ to <50 (requires full verification)

**Mandatory Safety Steps**:
1. Create feature branch before any production changes
2. Run `make lint` after each production file change
3. Run `make test` to ensure no new failures
4. Use subagent to start API server: `make run-api`
5. Run smoke tests on critical endpoints:
   - User authentication
   - Session creation
   - Timestamp-dependent operations
6. Verify API responses match expected formats
7. Document any behavioral changes

### Rollback Plan
**If any production change causes issues**:
1. Revert specific commits
2. Document the issue
3. Consult before proceeding
4. Consider alternative approaches

## Files to Modify

### Phase 1: Safe Test-Only Changes
**🟢 No Regression Risk - Test Files Only**:
- `tests/unit/test_ecpay_api_response_validation.py` - Fix service constructor mocks
- `tests/unit/test_merchant_trade_no_generation.py` - Fix service constructor mocks
- `tests/unit/infrastructure/repositories/test_subscription_repository_transaction_fix.py` - Fix mock behavior
- `tests/unit/models/test_user_plan_limits_contract.py` - Fix import paths
- `tests/unit/api/test_plan_limits_dependency_injection.py` - Fix import paths
- `tests/unit/infrastructure/test_enum_conversions.py` - Remove SpeakerRole.OTHER
- `pyproject.toml` - Add pytest markers
- Various test classes - Remove `__init__` methods

### Phase 2: Production Code Changes (Lower Priority)
**🔴 High Risk - Requires Full Verification**:
- `src/coaching_assistant/core/models/user.py` - datetime.utcnow() → datetime.now(UTC)
- `src/coaching_assistant/core/models/session.py` - datetime fixes
- `src/coaching_assistant/core/models/transcript.py` - datetime fixes
- `src/coaching_assistant/core/models/subscription.py` - datetime fixes
- 20+ other service and model files - datetime deprecation fixes

### Phase 3: Case-by-Case Review
**🟡 Medium Risk - Individual Assessment Required**:
- Various service test files with specific business logic failures
- Repository integration tests
- Service integration tests

## Success Metrics

### Phase 1 Targets (Safe Test Fixes)
1. **Error Reduction**: 24 errors → 0 errors ✅ No regression risk
2. **Failure Reduction**: 52 failures → ~15 failures ✅ No regression risk
3. **Test Reliability**: Consistent test results ✅ No regression risk

### Phase 2 Targets (Production Code Changes)
4. **Warning Reduction**: 1326 warnings → <50 warnings ⚠️ Requires verification
5. **Behavior Preservation**: All API responses unchanged ⚠️ Critical requirement
6. **Database Compatibility**: Timestamp formats preserved ⚠️ Critical requirement

### Overall Goals
7. **CI Stability**: Consistent green builds
8. **Test Speed**: Maintain current performance (~8 seconds)
9. **Developer Experience**: Cleaner test output and fewer distractions

## Critical Success Criteria

### Must-Have (Phase 1)
- ✅ All ECPay service constructor errors resolved
- ✅ All import path errors resolved
- ✅ Repository transaction test mocks working
- ✅ No new test failures introduced

### Must-Verify (Phase 2)
- ⚠️ API server starts successfully after datetime changes
- ⚠️ All timestamp-dependent endpoints return expected formats
- ⚠️ Database writes preserve expected timestamp formats
- ⚠️ No functional regressions in user-facing features

---
*Generated: 2025-09-29*
*Updated: 2025-09-29 (with regression prevention)*
*Status: Implementation Ready with Safety Protocols*