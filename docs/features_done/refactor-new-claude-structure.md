# Project Structure Refactoring Plan

## 📋 Overview

This document outlines the plan to refactor the coaching transcript tool to follow Python community best practices as defined in the updated CLAUDE.md. The goal is to move from the current monorepo structure to a more standard Python project layout while maintaining all existing functionality.

## 🎯 Objectives

1. **Standardize Python structure** - Follow `src/` layout best practices
2. **Improve developer experience** - Move configuration files to root level
3. **Maintain zero downtime** - All existing functionality must continue to work
4. **Preserve git history** - Use `git mv` to maintain file history
5. **Update imports systematically** - Ensure all references are updated

## 📊 Current vs Target Structure

### Current Structure
```
coaching_transcript_tool/
├── packages/
│   └── core-logic/
│       ├── src/coaching_assistant/
│       │   ├── api/
│       │   ├── models/
│       │   ├── services/
│       │   ├── tasks/
│       │   ├── utils/
│       │   └── core/
│       ├── alembic/
│       ├── tests/
│       ├── pyproject.toml
│       ├── requirements.txt
│       └── README.md
```

### Target Structure
```
coaching_transcript_tool/
├── src/
│   └── coaching_assistant/
│       ├── __init__.py
│       ├── __main__.py           # NEW: CLI entry point
│       ├── py.typed              # NEW: Type marker
│       ├── version.py            # NEW: Version info
│       ├── exceptions.py         # NEW: Custom exceptions
│       ├── constants.py          # NEW: Constants
│       ├── config/               # MOVED: from core/
│       │   ├── __init__.py
│       │   ├── settings.py       # ENHANCED: Main config
│       │   ├── environment.py    # NEW: Env handling
│       │   └── logging_config.py # NEW: Logging config
│       ├── core/                 # RESTRUCTURED
│       │   ├── services/         # EXISTING
│       │   ├── models/           # EXISTING
│       │   └── repositories/     # NEW: Data access layer
│       ├── api/                  # EXISTING
│       ├── tasks/                # EXISTING
│       └── utils/                # EXISTING
├── tests/                        # MOVED: from packages/core-logic/tests/
│   ├── conftest.py
│   ├── fixtures/                 # NEW: Test data
│   ├── unit/                     # ORGANIZED
│   ├── integration/              # ORGANIZED
│   ├── e2e/                      # ORGANIZED
│   └── performance/              # NEW
├── alembic/                      # MOVED: from packages/core-logic/alembic/
├── logs/                         # NEW: Log directory
├── examples/                     # NEW: Usage examples
├── pyproject.toml                # MOVED: to root
├── requirements.txt              # MOVED: to root
├── requirements-dev.txt          # NEW
├── .env.example                  # NEW
├── .pre-commit-config.yaml       # NEW
├── mypy.ini                      # NEW
└── pytest.ini                   # NEW
```

## 📝 Migration Steps (Using Git Worktree Strategy)

### Phase 1: Preparation and Git Worktree Setup
1. **Create git worktree for refactoring** - Isolated environment for safe changes
2. **Create new configuration files** in root directory
3. **Create standard Python package files**
4. **Set up logging and test infrastructure**
5. **Validate current functionality** in original worktree

### Phase 2: Structure Migration
1. **Move configuration files** to root level
2. **Move source code** from `packages/core-logic/src/` to `src/`
3. **Move tests** from `packages/core-logic/tests/` to `tests/`
4. **Move alembic** from `packages/core-logic/alembic/` to `alembic/`

### Phase 3: Import Path Updates
1. **Update all import statements** throughout the codebase
2. **Update configuration references**
3. **Update deployment scripts**
4. **Update CI/CD configurations**

### Phase 4: Testing and Validation
1. **Run comprehensive test suite**
2. **Validate API endpoints**
3. **Test transcription workflows**
4. **Verify deployment processes**

## 🛠️ Detailed Migration Commands (Git Worktree Strategy)

### Step 1: Set Up Git Worktree

```bash
# Create a new branch for refactoring
git checkout -b refactor-standard-python-structure

# Create a git worktree for the refactoring work
# This creates an isolated working directory
git worktree add ../coaching_transcript_tool_refactor refactor-standard-python-structure

# Switch to the refactor worktree
cd ../coaching_transcript_tool_refactor

# Verify we're in the right place
pwd  # Should show: /path/to/coaching_transcript_tool_refactor
git branch  # Should show: * refactor-standard-python-structure
```

### Step 2: Create New Files in Worktree

```bash
# Now we're working in the isolated worktree
# Create new directories
mkdir -p src/coaching_assistant/config
mkdir -p tests/{fixtures,unit,integration,e2e,performance}
mkdir -p logs examples

# Create new package files
touch src/coaching_assistant/__main__.py
touch src/coaching_assistant/py.typed
touch src/coaching_assistant/version.py
touch src/coaching_assistant/exceptions.py
touch src/coaching_assistant/constants.py

# Create configuration files
touch .env.example
touch .pre-commit-config.yaml
touch mypy.ini
touch pytest.ini
touch requirements-dev.txt
```

### Step 3: Move Configuration Files in Worktree

```bash
# Move configuration files to root
git mv packages/core-logic/pyproject.toml ./
git mv packages/core-logic/requirements.txt ./
git mv packages/core-logic/README.md ./src_README.md  # Rename to avoid conflict
```

### Step 4: Move Source Code in Worktree

```bash
# Move main source code
git mv packages/core-logic/src/coaching_assistant/* src/coaching_assistant/

# Move alembic
git mv packages/core-logic/alembic ./

# Move tests
git mv packages/core-logic/tests/* tests/

# Remove empty packages directory structure
rmdir packages/core-logic/src/coaching_assistant/
rmdir packages/core-logic/src/
rmdir packages/core-logic/tests/
rmdir packages/core-logic/
rmdir packages/
```

### Step 4: Update Import Paths and Configuration Files

The following files need import path updates:

#### FastAPI App Entry Points
- `apps/api-server/main.py`
- `apps/worker/health_server.py`

#### Test Files
- All files in `tests/` directory
- Update imports from `coaching_assistant.` to match new structure

#### Configuration References
- `alembic/env.py`
- CI/CD configurations

#### Makefile Updates (Critical!)
The `Makefile` has **multiple hardcoded paths** that need updating:

```bash
# Lines that need changes in Makefile:
Line 5:  VERSION = $(shell grep -m 1 'version' packages/core-logic/pyproject.toml | cut -d '"' -f 2)
Line 41: $(PYTHON) -m pip install -e packages/core-logic --break-system-packages
Line 63: CELERY_LOG_LEVEL=INFO celery -A coaching_assistant.core.celery_app worker --loglevel=info --concurrency=2 --pool=threads
Line 71: CELERY_LOG_LEVEL=DEBUG celery -A coaching_assistant.core.celery_app worker --loglevel=debug --concurrency=2 --pool=threads
Line 190: pytest packages/core-logic/tests/ -v --color=yes 2>&1 | tee logs/test.log
Line 194: $(PIP) install -r apps/api-server/requirements.txt --break-system-packages
Line 195: $(PIP) install -r apps/cli/requirements.txt --break-system-packages
Line 197: $(PIP) install -e packages/core-logic --break-system-packages
Line 204: $(PYTHON) -m flake8 packages/core-logic/src/ packages/core-logic/tests/ 2>&1 | tee logs/lint.log
```

**Updated Makefile paths:**
```bash
# Change from:
VERSION = $(shell grep -m 1 'version' packages/core-logic/pyproject.toml | cut -d '"' -f 2)
# To:
VERSION = $(shell grep -m 1 'version' pyproject.toml | cut -d '"' -f 2)

# Change from:
$(PYTHON) -m pip install -e packages/core-logic --break-system-packages
# To:
$(PYTHON) -m pip install -e . --break-system-packages

# Change from:
pytest packages/core-logic/tests/ -v --color=yes 2>&1 | tee logs/test.log
# To:
pytest tests/ -v --color=yes 2>&1 | tee logs/test.log

# Change from:
$(PYTHON) -m flake8 packages/core-logic/src/ packages/core-logic/tests/ 2>&1 | tee logs/lint.log
# To:
$(PYTHON) -m flake8 src/ tests/ 2>&1 | tee logs/lint.log
```

#### Docker Files Updates (Critical!)

**1. API Server Dockerfile (`apps/api-server/Dockerfile.api`):**
```dockerfile
# Lines 18, 25, 47 need changes:

# Change from:
COPY packages/core-logic/ ./packages/core-logic/
RUN pip install --prefix=/install ./packages/core-logic/
COPY packages/core-logic/ ./packages/core-logic/

# To:
COPY . ./
RUN pip install --prefix=/install .
# Remove the duplicate copy since we're copying everything
```

**2. CLI Dockerfile (`apps/cli/Dockerfile`):**
```dockerfile
# Lines 17, 24 need changes:

# Change from:
COPY packages/core-logic/ ./packages/core-logic/

# To:
COPY . ./
```

**3. Worker Dockerfiles (`apps/worker/Dockerfile*`):**
Similar changes needed for worker containers.

#### Docker Compose Updates (Critical!)
**File: `docker-compose.yml`**
```yaml
# Line 27 needs change:

# Change from:
      - ./packages/core-logic:/app/packages/core-logic

# To:
      - ./src:/app/src
      - ./alembic:/app/alembic
      - ./pyproject.toml:/app/pyproject.toml
```

**Files: `docker-compose.dev.yml`, `docker-compose.prod.yml`**
Similar volume mapping updates needed.

## 🧪 Testing Strategy (Git Worktree Benefits)

### Pre-Migration Tests (In Original Worktree)
```bash
# Switch back to original working directory to test current state
cd ../coaching_transcript_tool  # Original worktree

# Run full test suite in current structure
make test
cd apps/web && npm test

# Test API endpoints
curl http://localhost:8000/api/health
pytest packages/core-logic/tests/ -v

# Test transcription workflow
python scripts/test_transcription_flow.py

# Document all passing tests as baseline
make test 2>&1 | tee baseline_test_results.log
```

### Post-Migration Tests (In Refactor Worktree)
```bash
# Switch to refactor worktree for testing new structure
cd ../coaching_transcript_tool_refactor

# Test Makefile commands work correctly
make clean           # Should clean without errors
make dev-setup       # Should install dependencies from new paths
make test            # Should run tests from tests/ directory
make lint            # Should lint src/ and tests/ directories
make build           # Should install package from root pyproject.toml

# Test imports work correctly
python -c "from coaching_assistant.core.config import Settings; print('✅ Config import works')"
python -c "from coaching_assistant.api.sessions import router; print('✅ API import works')"
python -c "from coaching_assistant.services.google_stt import GoogleSTTProvider; print('✅ Service import works')"

# Test CLI entry point
python -m coaching_assistant --help

# Test alembic migration
alembic current
alembic check

# Test API server startup
make run-api  # Should start without errors

# Test Celery worker startup
make run-celery  # Should start without module import errors

# Test Docker builds work correctly
make docker-api      # Should build API container successfully
make docker-cli      # Should build CLI container successfully
make docker-worker   # Should build worker container successfully

# Test Docker Compose
docker-compose build # Should build all services
docker-compose up -d api  # Should start API service
curl http://localhost:8000/health  # Should return healthy

# Test transcription end-to-end
# Run actual transcription test with small audio file
```

### Regression Testing Checklist

- [ ] **Authentication**: Google SSO login works
- [ ] **Session Creation**: Can create transcription sessions
- [ ] **File Upload**: Audio file upload to GCS works
- [ ] **Transcription**: Both Google STT and AssemblyAI work
- [ ] **Export**: All export formats (JSON, VTT, SRT, XLSX) work
- [ ] **Speaker Roles**: Speaker role assignment works
- [ ] **Client Management**: CRUD operations for clients work
- [ ] **Coaching Sessions**: CRUD operations for coaching sessions work
- [ ] **Dashboard**: Summary statistics display correctly
- [ ] **Database**: All migrations apply correctly
- [ ] **Celery Tasks**: Background tasks execute properly
- [ ] **Frontend**: All frontend functionality works
- [ ] **Makefile Commands**: All make targets work with new paths
- [ ] **Docker Builds**: All Docker images build successfully
- [ ] **Docker Compose**: Services start and communicate properly
- [ ] **Development Workflow**: Local development setup works
- [ ] **Deployment**: Apps can be deployed successfully

## 🔧 New Configuration Files Content

### `.env.example`
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/coaching_assistant
REDIS_URL=redis://localhost:6379

# Authentication
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type": "service_account"...}

# STT Providers
STT_PROVIDER=google
GOOGLE_STT_MODEL=chirp_2
GOOGLE_STT_LOCATION=asia-southeast1
ASSEMBLYAI_API_KEY=your_api_key_here

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log

# Development
DEBUG=false
ENVIRONMENT=development
```

### `mypy.ini`
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
disallow_untyped_defs = False
disallow_incomplete_defs = False

[mypy-alembic.*]
ignore_errors = True
```

### `pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --cov=src/coaching_assistant
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=85
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
```

### `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-redis]
```

## 🚨 Risk Mitigation

### High-Risk Areas
1. **Import path changes** - Could break existing functionality
2. **Alembic configuration** - Database migration path changes
3. **Makefile dependencies** - Multiple hardcoded paths throughout
4. **Docker build contexts** - Copy commands reference old paths
5. **Docker Compose volumes** - Volume mappings need updating
6. **Development workflow** - Local dev commands may fail
7. **Deployment scripts** - May reference old paths
8. **CI/CD pipelines** - May have hardcoded paths

### Critical Docker & Makefile Dependencies
**Files with hard dependencies on `packages/core-logic/` structure:**
- `Makefile` (10+ references to packages/core-logic/)
- `apps/api-server/Dockerfile.api` (COPY and install commands)
- `apps/cli/Dockerfile` (COPY commands)
- `apps/worker/Dockerfile*` (similar COPY commands)
- `docker-compose.yml` (volume mappings)
- `docker-compose.dev.yml` (volume mappings)
- `docker-compose.prod.yml` (volume mappings)

### Mitigation Strategies (Enhanced with Git Worktree)
1. **Git Worktree Isolation** - Refactor in completely separate directory
2. **Original Environment Preserved** - Can always switch back to working version
3. **Parallel Testing** - Compare old vs new implementations side-by-side
4. **Incremental migration** - Test each phase independently
5. **Easy Rollback** - Simply delete worktree if issues arise
6. **Comprehensive testing** - Test all critical paths in isolated environment

### Git Worktree Safety Benefits
- **Zero Risk to Main Codebase** - Original directory remains untouched
- **Instant Switching** - `cd ../coaching_transcript_tool` to go back to working version
- **Side-by-Side Comparison** - Run services on different ports for testing
- **Easy Cleanup** - Delete worktree directory if refactor fails
- **Full Git History** - All changes tracked, easy to cherry-pick successful parts

### Rollback Plan (Simplified with Worktree)
If issues are discovered:

```bash
# Option 1: Simply delete the refactor worktree
cd ../coaching_transcript_tool  # Go back to original
git worktree remove ../coaching_transcript_tool_refactor
git branch -D refactor-standard-python-structure

# Option 2: Save partial progress and try again
cd ../coaching_transcript_tool_refactor
git add .
git commit -m "WIP: partial refactor progress"
cd ../coaching_transcript_tool
git worktree remove ../coaching_transcript_tool_refactor

# Option 3: Cherry-pick successful changes
cd ../coaching_transcript_tool
git cherry-pick <commit-hash-of-successful-change>
```

### Development During Refactor
```bash
# Continue normal development in original directory
cd ../coaching_transcript_tool
git checkout main  # or your main branch
# Normal development continues here

# Work on refactor in parallel
cd ../coaching_transcript_tool_refactor
# Refactor work continues here

# Test both versions side by side
# Original API on port 8000
cd ../coaching_transcript_tool && make run-api

# Refactored API on port 8001 
cd ../coaching_transcript_tool_refactor && PORT=8001 make run-api
```

## 📅 Timeline (Git Worktree Strategy - Safer but Thorough)

### Phase 1: Preparation and Worktree Setup (0.5 days)
- Create git worktree for isolated refactoring
- Set up new configuration files in worktree
- **Benefit**: Original codebase remains completely untouched
- **New**: Audit all Docker and Makefile dependencies

### Phase 2: Migration in Worktree (1 day)
- Execute file moves in isolated environment
- Update import paths
- **New**: Update Makefile paths (10+ changes)
- **New**: Update all Dockerfile COPY commands
- **New**: Update docker-compose volume mappings
- Update other configurations
- **Benefit**: Can easily revert by deleting worktree

### Phase 3: Parallel Testing (1.5 days)
- **New**: Test both old and new structures side-by-side
- **New**: Run services on different ports for comparison
- **New**: Test all Makefile commands work in refactor worktree
- **New**: Test Docker builds succeed in refactor worktree
- **New**: Test Docker Compose works in refactor worktree
- Run comprehensive tests in both environments
- Fix any issues found in isolated worktree
- **Benefit**: Original environment always available for reference

### Phase 4: Integration and Deployment (1 day)
- Merge successful refactor back to main branch
- Test deployment process
- Update CI/CD if needed
- Monitor production deployment
- Clean up worktree

### Phase 5: Cleanup (0.5 days)
- Remove refactor worktree
- Update documentation
- Verify everything works in merged state

**Total Estimated Time: 4.5 days** (slightly reduced due to reduced risk and parallel testing capabilities)

### Git Worktree Timeline Benefits
- **Reduced Risk**: Original codebase never broken during development
- **Parallel Development**: Can continue normal work while refactoring
- **Easy Rollback**: Delete worktree instead of complex git operations
- **Side-by-Side Testing**: Compare functionality before committing to changes
- **Iterative Approach**: Can restart worktree multiple times if needed

## ✅ Success Criteria

1. **All tests pass** - Both backend and frontend test suites
2. **API functionality preserved** - All endpoints work as before
3. **Transcription workflows work** - Both STT providers function correctly
4. **Database migrations intact** - Alembic works without issues
5. **Deployment successful** - Can deploy to all environments
6. **Performance maintained** - No significant performance regression
7. **Code quality improved** - Better test coverage and type checking

## 📞 Support

If issues arise during migration:
1. Check this document for common solutions
2. Run regression test checklist
3. Review git history for changes
4. Consider rollback if critical issues found

---

## 🎯 Quick Start Guide

If you want to start the refactor right now, here's the minimal command sequence:

```bash
# 1. Create and switch to refactor worktree
git checkout -b refactor-standard-python-structure
git worktree add ../coaching_transcript_tool_refactor refactor-standard-python-structure
cd ../coaching_transcript_tool_refactor

# 2. Create new structure
mkdir -p src/coaching_assistant/{config,core/repositories} tests/{fixtures,unit,integration,e2e,performance} logs examples

# 3. Move files
git mv packages/core-logic/pyproject.toml ./
git mv packages/core-logic/requirements.txt ./
git mv packages/core-logic/src/coaching_assistant/* src/coaching_assistant/
git mv packages/core-logic/alembic ./
git mv packages/core-logic/tests/* tests/

# 4. Create new files
touch src/coaching_assistant/{__main__.py,py.typed,version.py,exceptions.py,constants.py}
touch {.env.example,.pre-commit-config.yaml,mypy.ini,pytest.ini,requirements-dev.txt}

# 5. Test basic functionality
make dev-setup && make test
```

## 📚 Additional Considerations

### Git Worktree Best Practices
- **Branch Naming**: Use descriptive names like `refactor-standard-python-structure`
- **Worktree Location**: Place worktree at same level as original (`../project_refactor`)
- **Multiple Attempts**: Feel free to delete and recreate worktree multiple times
- **Cherry-picking**: Use `git cherry-pick` to bring successful changes back

### Environment Considerations
- **Virtual Environments**: Each worktree can have its own venv
- **IDE Configuration**: Update IDE workspace to include refactor directory
- **Port Conflicts**: Use different ports for parallel service testing
- **Database**: Consider using separate test database for refactor testing

### Performance Tips
- **Parallel Make**: Use `make -j4` for faster builds in refactor worktree
- **Docker Builds**: Use `docker build --parallel` where available
- **Test Subsets**: Run only modified test modules during development

### Common Pitfalls to Avoid
- **Don't forget** to update import statements in test files
- **Remember** to update `PYTHONPATH` in Docker containers
- **Check** that all environment variables work with new structure
- **Verify** that CLI tools work from new package location
- **Update .gitignore** if needed (current .gitignore already handles `logs/`)
- **Test import paths** in both development and Docker environments
- **Validate Alembic** can find database models in new location

### .gitignore Considerations
The current `.gitignore` already handles most refactor requirements:
- ✅ `logs/` - Already ignored
- ✅ `__pycache__/` - Already ignored  
- ✅ `.pytest_cache/` - Already ignored
- ✅ `htmlcov/` - Coverage reports already ignored
- ✅ `.mypy_cache/` - MyPy cache already ignored

No additional .gitignore updates needed for the refactor.

---

**Document Owner**: Development Team  
**Created**: 2025-01-15  
**Last Updated**: 2025-01-15  
**Status**: Ready for Implementation (Git Worktree Strategy)