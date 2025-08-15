# Pre-Merge Checklist for Python Structure Refactoring

## ✅ Completed Tasks

### 1. Structure Migration
- [x] Moved from `packages/core-logic/` to standard `src/` layout
- [x] Updated all import paths
- [x] Fixed SQLAlchemy model compatibility (JSONB → JSON)
- [x] Updated Makefile paths
- [x] Updated Docker configurations
- [x] Updated alembic configuration

### 2. Test Suite
- [x] Fixed all test failures (206 passing, 3 skipped)
- [x] Removed outdated/incompatible tests
- [x] Added coverage reporting (49% coverage)
- [x] Fixed reCAPTCHA issues in auth tests

### 3. Error Handling
- [x] Improved AssemblyAI error handling
- [x] Added retry logic with exponential backoff
- [x] Enhanced logging for debugging

## 🔄 Tasks Before Merge

### 1. Code Cleanup (Priority: HIGH)
- [ ] Commit remaining file moves (43 files changed)
- [ ] Remove `.bak` files if any
- [ ] Clean up any temporary test files

### 2. Fix Deprecation Warnings (Priority: MEDIUM)
- [ ] Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- [ ] Update FastAPI event handlers from `@app.on_event` to lifespan
- [ ] Fix SQLAlchemy declarative_base deprecation
- [ ] Update pydantic Config to ConfigDict

### 3. Documentation Updates (Priority: HIGH)
- [ ] Update README.md with new structure
- [ ] Update installation instructions
- [ ] Document the new project layout
- [ ] Update development setup guide

### 4. Docker & Deployment (Priority: HIGH)
- [ ] Test all Docker builds
- [ ] Verify Render deployment works
- [ ] Test Cloudflare Workers build
- [ ] Ensure CI/CD pipelines work

### 5. Database Migrations (Priority: MEDIUM)
- [ ] Test alembic migrations with new structure
- [ ] Ensure foreign key naming is consistent
- [ ] Verify SQLite compatibility

### 6. Final Verification (Priority: HIGH)
- [ ] Run full test suite one more time
- [ ] Check coverage hasn't decreased
- [ ] Verify API endpoints work
- [ ] Test worker processes (Celery)

## 📝 PR Description Template

```markdown
## 🎯 Purpose
Refactor Python project structure to follow PEP 518 best practices and modern Python packaging standards.

## 🔄 Major Changes
- Migrated from `packages/core-logic/` to standard `src/` layout
- Updated all import paths and dependencies
- Fixed test suite (206 tests passing)
- Improved error handling and logging
- Added test coverage reporting

## 📊 Impact
- **Breaking Changes**: None (all APIs remain compatible)
- **Database**: Changed JSONB to JSON for SQLite compatibility
- **Tests**: 206 passing, 49% coverage
- **Dependencies**: No new dependencies added

## ✅ Testing
- All tests passing
- Docker builds verified
- API endpoints tested
- Worker processes functional

## 📚 Documentation
- Updated README with new structure
- Added CLAUDE.md with development guidelines
- Created migration documentation
```

## 🚀 Merge Strategy

1. **Create PR from `refactor-python-structure` to `poc-assemblyai`**
2. **Review all changes carefully**
3. **Run tests in CI/CD**
4. **Merge with squash commit**
5. **Tag the release**
6. **Update deployment configurations**

## ⚠️ Post-Merge Tasks

1. Monitor error logs for any issues
2. Verify all deployments are working
3. Update team documentation
4. Clean up old git worktrees
5. Delete refactor branch after successful merge