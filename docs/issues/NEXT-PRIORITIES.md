# Test Coverage Improvement - Next Priorities

**Current Status**: 49.06% coverage (813 tests passing)
**Updated**: 2025-10-04
**Week 1 Achievement**: 98% of 50% target ✅

---

## Week 1 Results Summary

✅ **Outstanding Success**:
- Coverage: 46.36% → 49.06% (+2.70%)
- Tests: 670 → 813 (+143 tests)
- 10 modules significantly improved
- 2 modules at 100% coverage
- 8 modules at 85%+ coverage

**Week 1 Documentation**: Archived to `docs/issues/archive/`

---

## Next Improvement Opportunities

### Category 1: High-Value Service Layer (Week 2 Priority)

**High Impact, Testable Modules**:

1. **lemur_transcript_smoother.py** (21% → 60% target)
   - 882 total lines, 699 uncovered
   - AI transcript smoothing logic
   - Error handling for API failures
   - **Impact**: Critical feature for transcript quality
   - **Effort**: High (complex AI integration)
   - **Priority**: 🔴 HIGH

2. **ecpay_service.py** (40% → 70% target)
   - 497 total lines, 300 uncovered
   - Payment gateway integration
   - Webhook handling, refunds, cancellations
   - **Impact**: Revenue/billing critical
   - **Effort**: Medium (external API mocking)
   - **Priority**: 🔴 CRITICAL

3. **plan_configuration_service.py** (32% → 65% target)
   - 222 total lines, 152 uncovered
   - Plan management and configuration
   - Feature flag logic
   - **Impact**: High (subscription management)
   - **Effort**: Low (mostly business logic)
   - **Priority**: 🟠 HIGH

4. **billing_analytics_service.py** (66% → 85% target)
   - 303 total lines, 104 uncovered
   - Analytics calculations and aggregations
   - Revenue reporting
   - **Impact**: Medium (analytics accuracy)
   - **Effort**: Low (calculation logic)
   - **Priority**: 🟡 MEDIUM

### Category 2: Repository Layer (Week 2 Priority)

**Data Access Layer - Critical for Data Integrity**:

1. **coaching_session_repository.py** (41% → 70% target)
   - 173 total lines, 102 uncovered
   - Session CRUD operations
   - **Effort**: Medium (database mocking)
   - **Priority**: 🔴 HIGH

2. **user_repository.py** (16% → 60% target)
   - 193 total lines, 163 uncovered
   - User data access
   - **Effort**: Medium
   - **Priority**: 🔴 HIGH

3. **coach_profile_repository.py** (14% → 60% target)
   - 197 total lines, 170 uncovered
   - Profile management
   - **Effort**: Medium
   - **Priority**: 🟠 HIGH

4. **session_repository.py** (25% → 60% target)
   - 96 total lines, 72 uncovered
   - Session persistence
   - **Effort**: Low (smaller module)
   - **Priority**: 🟠 MEDIUM

5. **client_repository.py** (20% → 60% target)
   - 110 total lines, 88 uncovered
   - Client data management
   - **Effort**: Low
   - **Priority**: 🟠 MEDIUM

### Category 3: Background Tasks (Week 2-3)

**Celery Tasks - Asynchronous Operations**:

1. **transcription_tasks.py** (12% → 50% target)
   - 216 total lines, 191 uncovered
   - Transcription job processing
   - **Impact**: Critical feature
   - **Effort**: High (Celery mocking)
   - **Priority**: 🔴 HIGH

2. **subscription_maintenance_tasks.py** (13% → 50% target)
   - 154 total lines, 134 uncovered
   - Subscription lifecycle management
   - **Impact**: High (billing)
   - **Effort**: Medium
   - **Priority**: 🟠 HIGH

3. **admin_report_tasks.py** (18% → 50% target)
   - 193 total lines, 158 uncovered
   - Admin reporting jobs
   - **Impact**: Medium
   - **Effort**: Medium
   - **Priority**: 🟡 MEDIUM

### Category 4: API Layer (Week 3)

**FastAPI Route Handlers - Lower Priority**:

Note: API layer testing often requires integration tests or E2E tests rather than unit tests. Consider if this is worth the effort vs. focusing on service/repository layers.

1. **api/v1/sessions.py** (22% → 50% target)
   - 547 total lines, 424 uncovered
   - Session management endpoints
   - **Priority**: 🟡 LOW (integration test territory)

2. **api/v1/coaching_sessions.py** (24% → 50% target)
   - 414 total lines, 314 uncovered
   - Coaching session endpoints
   - **Priority**: 🟡 LOW

3. **api/v1/transcript_smoothing.py** (22% → 50% target)
   - 401 total lines, 313 uncovered
   - Transcript smoothing endpoints
   - **Priority**: 🟡 LOW

### Category 5: Architectural Issues (Requires Code Fixes First)

**Modules That Need Refactoring**:

1. **usage_tracking_use_case.py** (20% coverage)
   - ⚠️ **BLOCKED**: Architectural issues discovered in Week 1
   - Requires domain model alignment
   - Repository method additions needed
   - **Action**: Fix architecture before testing

2. **services/usage_tracker.py** (0% coverage)
   - 137 lines, completely untested
   - Likely architectural issues
   - **Action**: Investigate and fix

3. **infrastructure/memory_repositories.py** (0% coverage)
   - 171 lines, test/dev fallback
   - **Action**: Low priority (dev only)

4. **cli/admin.py** (0% coverage)
   - 161 lines, CLI tools
   - **Action**: Low priority (manual testing)

---

## Recommended Week 2 Plan

### Goal: 49.06% → 55% (+5.94%)

**Priority Order**:

#### Week 2 Day 1-2: Payment Critical Path
1. **ecpay_service.py**: 40% → 70% (+30%)
   - Payment gateway errors, webhooks, refunds
   - ~60 tests
   - **Expected gain**: +1.8%

2. **plan_configuration_service.py**: 32% → 65% (+33%)
   - Plan logic and feature flags
   - ~40 tests
   - **Expected gain**: +0.9%

**Day 1-2 Target**: +100 tests, +2.7% coverage

#### Week 2 Day 3-4: Repository Layer
3. **coaching_session_repository.py**: 41% → 70% (+29%)
   - CRUD operations, constraints
   - ~35 tests
   - **Expected gain**: +0.6%

4. **user_repository.py**: 16% → 60% (+44%)
   - User data access
   - ~50 tests
   - **Expected gain**: +1.0%

5. **coach_profile_repository.py**: 14% → 60% (+46%)
   - Profile management
   - ~50 tests
   - **Expected gain**: +0.9%

**Day 3-4 Target**: +135 tests, +2.5% coverage

#### Week 2 Day 5: Cleanup & Review
- Polish remaining gaps
- Integration test scenarios
- Documentation updates
- Week 2 summary

**Week 2 Total Expected**: +235 tests, 49.06% → 55% (+5.94%)

---

## Recommended Week 3 Plan

### Goal: 55% → 60% (+5%)

**Priority Order**:

#### Week 3 Day 1-2: AI/Transcript Services
1. **lemur_transcript_smoother.py**: 21% → 60% (+39%)
   - AI integration testing
   - Error handling, API failures
   - ~100 tests
   - **Expected gain**: +3.3%

#### Week 3 Day 3-4: Background Tasks
2. **transcription_tasks.py**: 12% → 50% (+38%)
   - Celery task testing
   - ~50 tests
   - **Expected gain**: +1.0%

3. **subscription_maintenance_tasks.py**: 13% → 50% (+37%)
   - Subscription lifecycle
   - ~40 tests
   - **Expected gain**: +0.6%

#### Week 3 Day 5: Architecture Fixes
4. **Fix usage_tracking_use_case.py architectural issues**
   - Align domain models
   - Add repository methods
   - Then add tests: 20% → 60%
   - **Expected gain**: +0.8% (if fixed)

**Week 3 Total Expected**: +190 tests, 55% → 60% (+5%)

---

## Long-Term Strategy (Beyond Week 3)

### Target: 60% → 85%

**Remaining Major Gaps**:

1. **Assemblyai STT Service**: 68% → 85% (+17%)
   - ~50 tests, +0.6% coverage

2. **Repository Layer Polish**: Various modules 60% → 80%
   - ~80 tests, +1.5% coverage

3. **API Layer (if needed)**: 22-40% → 60%
   - Consider integration tests instead
   - ~200 tests, +3% coverage

4. **Background Tasks Polish**: 50% → 75%
   - ~60 tests, +1% coverage

5. **Utility Modules**: Various
   - gcs_uploader: 14% → 60%
   - chinese_converter: 62% → 85%
   - ~40 tests, +0.5% coverage

**Long-term Path**: 60% → 70% → 80% → 85%
- Months 2-3: Focus on remaining services and repositories
- Months 4-6: Polish, integration tests, E2E coverage

---

## Success Metrics

### Week 2 Targets
- **Coverage**: 49.06% → 55% (+5.94%)
- **Tests**: 813 → ~1048 (+235)
- **Modules at 85%+**: 8 → 11 (+3)
- **Pass Rate**: 100% maintained

### Week 3 Targets
- **Coverage**: 55% → 60% (+5%)
- **Tests**: 1048 → ~1238 (+190)
- **Modules at 85%+**: 11 → 14 (+3)
- **Pass Rate**: 100% maintained

### Quality Metrics
- **Test Speed**: <10 seconds for full suite
- **Zero Regressions**: All existing tests passing
- **Error Coverage**: 90%+ in critical modules
- **Documentation**: Complete test patterns documented

---

## Key Principles (From Week 1 Success)

1. ✅ **Error-First Testing**: Test error paths before happy paths
2. ✅ **Domain Model Verification**: Check models before writing tests
3. ✅ **Strategic Module Selection**: Target testable, high-impact modules first
4. ✅ **Quality Over Quantity**: Maintain 100% pass rate
5. ✅ **Avoid Broken Code**: Document architectural issues, don't waste time testing broken modules

---

**Status**: Ready for Week 2
**Next Action**: Begin ecpay_service.py error handling tests
