# Architectural Rules & Review Guidelines

## Overview
This reference captures the Clean Architecture Lite guardrails for the coaching transcript tool. It documents the desired dependency flow, highlights the current hybrid exceptions, and outlines what reviewers should block during code review.

## Current Snapshot (2025-09-17)
- **Domain models** live in `src/coaching_assistant/core/models/` for sessions, usage logs, transcripts, and users. Plans / subscriptions use cases still import legacy ORM enums for compatibility (`src/coaching_assistant/core/services/plan_management_use_case.py:19`, `src/coaching_assistant/core/services/subscription_management_use_case.py:19`).
- **Repository ports** in `core/repositories/ports.py` define the contracts; SQLAlchemy implementations in `infrastructure/db/repositories/` handle domain ↔ legacy conversion (e.g. `infrastructure/db/repositories/user_repository.py:12`).
- **API layer**: Plans, plan-limits, subscriptions, and most session endpoints already depend on factories (`src/coaching_assistant/api/v1/plans.py:1`, `src/coaching_assistant/api/v1/subscriptions.py:1`), but there are still 88 direct `Depends(get_db)` injections across v1 endpoints (`rg "Depends(get_db" src/coaching_assistant/api/v1 | wc -l`).
- **Known legacy services**: `core/services/admin_daily_report.py:9` and `core/services/ecpay_service.py:11` still depend on SQLAlchemy sessions and legacy ORM until WP5/WP6 removes them.
- **Tests**: Factory, session, and subscription use cases have unit/integration/e2e coverage (`tests/unit/services/test_session_management_use_case.py`, `tests/unit/services/test_subscription_management_use_case.py`, `tests/e2e/test_subscription_flows_e2e.py`). Plans use cases lack dedicated unit tests; behaviour is guarded by integration/e2e suites.

## Architectural Boundaries
| Layer | Allowed Dependencies | Current Notes |
|-------|----------------------|---------------|
| **Core services** (`core/services/`) | Domain models, repository ports, settings, Python stdlib | Do **not** add new SQLAlchemy or HTTP clients. Existing legacy exceptions limited to `admin_daily_report.py` and `ecpay_service.py` (must keep `# LEGACY` comment and cleanup task).
| **Repository ports** (`core/repositories/ports.py`) | Domain models only | Contracts already reference domain dataclasses. Keep interfaces lean; add new ports before repositories.
| **Infrastructure** (`infrastructure/db/*`) | SQLAlchemy, external clients, environment adapters | Responsible for domain ↔ ORM conversion. Commit/rollback must stay here.
| **API (`api/v1`)** | FastAPI, Pydantic, injected use cases, response serializers | New endpoints must avoid `Depends(get_db)`; legacy endpoints may keep it temporarily but require a TODO to migrate and an entry in the relevant WP doc.

### Known Legacy Exceptions
| Path | Reason | Follow-up |
|------|--------|-----------|
| `src/coaching_assistant/core/services/admin_daily_report.py` | Generates analytics directly with SQLAlchemy queries. | Replace with reporting use case + repository queries (WP5/WP6).
| `src/coaching_assistant/core/services/ecpay_service.py` | ECPay SDK still expects ORM objects & direct session access. | Introduce infrastructure client adapter during WP5, then swap service to use ports.
| `src/coaching_assistant/api/v1/**` (88 matches) | Legacy endpoints keep direct DB access. | Each refactor should reduce this count; document exceptions inside the corresponding WP doc.

## Code Review Checklist

### Blocker Checks (❌ reject PR)
```bash
# Core services must not pull SQLAlchemy or direct ORM operations
rg "from sqlalchemy" src/coaching_assistant/core/services
rg "\.query\(" src/coaching_assistant/core/services
rg "\.commit\(\)" src/coaching_assistant/core/services
```
- [ ] No new SQLAlchemy imports or session parameters in `core/services/*` (legacy files must retain `# LEGACY` comment and open task).
- [ ] Use cases never call `.query()`, `.add()`, `.commit()`, or external HTTP clients directly.
- [ ] API endpoints do not introduce new ad-hoc business logic; domain exceptions are mapped to HTTP responses.
- [ ] Repository implementations stay free of business rules and implement their port signatures.

### API Layer Review
- [ ] Prefer `api/v1/dependencies.py` factories for all new use case wiring.
- [ ] Legacy endpoints that still inject `db: Session = Depends(get_db)` include a TODO pointing to the migration work package.
- [ ] Incoming/outgoing DTOs are mapped at the API boundary (no ORM objects leaked).

### Repository Review
- [ ] Implementation returns domain models (see `infrastructure/db/repositories/session_repository.py`).
- [ ] Transactions use `session.flush()` where identity is needed; commits remain responsibility of the calling unit of work.
- [ ] Exceptions are wrapped into domain/runtime errors before leaving the infrastructure layer.

### Use Case Review
- [ ] Single responsibility and clear inputs/outputs.
- [ ] Dependencies injected by constructor (no global session access).
- [ ] Business validations remain in use case/domain (e.g. plan limits in `core/services/session_management_use_case.py`).

## File Organisation Rules
```
src/coaching_assistant/
├── core/
│   ├── models/            # Domain dataclasses & enums
│   ├── repositories/      # Port definitions
│   └── services/          # Use cases (pure business logic)
├── infrastructure/
│   ├── db/repositories/   # SQLAlchemy adapters (domain ↔ ORM)
│   ├── db/session.py      # DB session management helpers
│   ├── factories.py       # Dependency injection factories
│   └── memory_repositories.py
└── api/
    └── v1/                # FastAPI routers (HTTP only)
```
| Naming | Convention |
|--------|------------|
| Use cases | `*UseCase` (e.g. `SessionCreationUseCase`) |
| Repository implementations | `SQLAlchemy*Repository` |
| Ports | `*Port` |
| Factories | `*Factory` |

## Testing Requirements
1. **Use case tests** must run with in-memory repositories or mocks (see `tests/unit/services/test_session_management_use_case.py`).
2. **Repository tests** may use transactional database fixtures (`tests/integration/test_session_repository.py`).
3. **API tests** should live under `tests/integration/api/` and exercise request/response contracts.
4. **Unit suites** must not require a real database; fail-fast when a new dependency sneaks in.

Example:
```python
# ✅ GOOD: Pure use case test with in-memory repos
use_case = SessionCreationUseCase(session_repo, user_repo, plan_config_repo)
result = use_case.execute(user_id=user.id, title="Weekly sync")

# ❌ BAD: Use case initialised with real Session
use_case = SessionCreationUseCase(db_session)
```

## Migration Guidelines
- **Phase 1** *(done, see `./done/phase-1-foundation-done.md`)*: established ports + pilot use case, kept APIs untouched.
- **Phase 2** *(done, see `./done/phase-2-api-migration-done.md`)*: routed APIs through factories; many legacy endpoints still hold direct DB access.
- **Phase 3** *(in progress – `phase-3-domain-models.md`)*: finishing domain ↔ ORM split, eliminating `Depends(get_db)` usage, and providing plan/subscription domain models.
- **Phase 4–6**: track per work package (WP4 sessions vertical, WP5 domain/ORM convergence, WP6 cleanup & guardrails).

During migration keep compatibility wrappers (e.g. `infrastructure/factories.get_usage_tracking_service`) but mark them as deprecated and reference the sunset plan.

## Quality Gates & Automation
```bash
# Suggested checks before merging
make lint
make test-unit
make test-integration
pytest tests/e2e -m "not slow"
rg "Depends(get_db" src/coaching_assistant/api/v1   # ensure number trends downward
rg "from sqlalchemy" src/coaching_assistant/core/services
```
Add a pre-commit hook for architecture drift detection (`scripts/check_architecture.py`) when ready.

## Examples
```python
# ❌ BAD: SQLAlchemy usage inside a new use case
class CreateUsageLogUseCase:
    def __init__(self, db: Session):  # Direct session dependency
        self.db = db
    def execute(self, session_data):
        user = self.db.query(User).first()  # ORM logic leaks into business layer

# ✅ GOOD: Use case depends on ports
class CreateUsageLogUseCase:
    def __init__(self, user_repo: UserRepoPort, usage_log_repo: UsageLogRepoPort):
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo
```

### Legacy Bridge (allowed temporarily)
```python
# LEGACY: admin daily report still needs direct SQLAlchemy access.
# Track removal in WP6.
from sqlalchemy.orm import Session
class AdminDailyReportService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
```
Annotate such sections with `# LEGACY` and link to the follow-up item in the relevant work package.
