# Success Metrics for Clean Architecture Refactoring

## Snapshot (2025-09-17)
The table below captures the measurable indicators we track while migrating toward Clean Architecture Lite. Update the "Current" column whenever a new measurement is taken.

### Architecture Compliance
| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| SQLAlchemy imports inside `core/services` | 0 files | 2 files (`admin_daily_report.py`, `ecpay_service.py`) – 5 matches (`rg "from sqlalchemy" src/coaching_assistant/core/services`) | ⚠️ | Legacy services pending removal in WP5/WP6. No new occurrences allowed.
| Direct `Depends(get_db)` in `api/v1` | Trend ↓ toward 0 | 88 matches (`rg "Depends(get_db" src/coaching_assistant/api/v1 | wc -l`) | ⚠️ | Plans/Subscriptions refactored; most other endpoints still legacy. Track decrease per work package.
| Business logic in API endpoints | None | Manual review required | ⚠️ | New endpoints must delegate to use cases. Flag during code review.

### Testing & Quality
| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| Unit coverage for use cases | >90% core coverage | Not recalculated (run `pytest --cov=src/coaching_assistant/core`) | ⏳ | Last verified before WP3; rerun after major merges.
| Plans use case unit tests | Exists & green | ❌ Not yet implemented | ⚠️ | Behaviour currently guarded by integration/e2e tests (`tests/integration/api/test_plan_*`, `tests/e2e/test_plan_*`). Add dedicated unit tests.
| Session & Subscription use case tests | Exists & green | ✅ (`tests/unit/services/test_session_management_use_case.py`, `tests/unit/services/test_subscription_management_use_case.py`) | ✅ | Maintain when adding new use cases.
| Factory regression tests | Exists & green | ✅ (`tests/unit/infrastructure/test_factory_circular_reference.py`) | ✅ | Extend when adding new factories.

### Continuous Delivery
| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| `make lint`, `make test-unit`, `make test-integration` | Green on main before release | Needs rerun on latest changes | ⏳ | Record command output in PR description.
| E2E smoke (`pytest tests/e2e -m "not slow"`) | Run before deploy | Needs rerun | ⏳ | Prioritize tests covering Plans/Subscriptions/Sessions flows.
| Frontend lint & test (`apps/web`) | Green before deploy | Needs rerun | ⏳ | Required when API schema changes impact UI.

### Developer Experience
| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| Files touched per feature (vertical slice) | ≤3 primary layers | Varies by WP (Plans ~3, legacy endpoints >3) | ⚠️ | Continue reducing once API legacy dependencies are removed.
| Time to locate business rule | <5 min | Anecdotally improved for Sessions/Subscriptions | 🙂 | Document business rules in use case docstrings to sustain clarity.

### Business Impact (informational)
| Metric | Target | Current | Status | Notes |
|--------|--------|---------|--------|-------|
| Production bugs tied to architecture regression | ↓ 50% vs pre-refactor | Pending observation | ⏳ | Track via incident log once enough data points exist.
| Regression bugs per release | ↓ 40% | Pending observation | ⏳ | Link release notes to automated test runs.

## Measurement Commands
```bash
# Architecture drift
rg "from sqlalchemy" src/coaching_assistant/core/services
rg "Depends(get_db" src/coaching_assistant/api/v1 | wc -l

# Test coverage snapshot
pytest --cov=src/coaching_assistant/core --cov-report=term-missing

# CI-style smoke (backend)
make lint && make test-unit && make test-integration
pytest tests/e2e -m "not slow"

# Frontend checks
cd apps/web && npm run lint && npm run test && npm run build
```

Update this document after each major work package to keep stakeholders aware of progress and outstanding risks.
