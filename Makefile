.PHONY: clean clean-frontend build install docker docker-run test lint dev-frontend build-frontend build-frontend-cf install-frontend deploy-frontend preview-frontend dev-all build-all install-all

# Variables
PACKAGE_NAME = coaching_transcript_tool
VERSION = $(shell python3 -c "import json; print(json.load(open('version.json'))['version'])" 2>/dev/null || grep -m 1 'version' pyproject.toml | cut -d '"' -f 2)
DOCKER_API_IMAGE = $(PACKAGE_NAME)-api:$(VERSION)
DOCKER_CLI_IMAGE = $(PACKAGE_NAME)-cli:$(VERSION)
DOCKER_API_LATEST = $(PACKAGE_NAME)-api:latest
DOCKER_CLI_LATEST = $(PACKAGE_NAME)-cli:latest
PYTHON = uv run python
UV = uv

# Fix for zsh make compatibility
SHELL := /bin/bash

# Default target
all: clean build

# Clean all build artifacts (backend + frontend)
clean: clean-frontend
	@echo "Cleaning Python build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Clean frontend build artifacts
clean-frontend:
	@echo "Cleaning frontend build artifacts..."
	rm -rf apps/web/.next/
	rm -rf apps/web/.turbo/
	rm -rf apps/web/.vercel/
	rm -rf apps/web/.open-next/
	rm -rf apps/web/.wrangler/
	rm -rf apps/web/out/
	rm -rf apps/web/tsconfig.tsbuildinfo

# Build the package
build: clean
	@echo "Setting up uv environment..."
	$(UV) sync
	@echo "Installing core logic package..."
	$(UV) pip install -e .
	@echo "Installing api-server dependencies..."
	$(UV) pip install -r apps/api-server/requirements.txt

# Install the package locally
install: build
	@echo "Installation complete."

# Start API server
run-api: install
	@mkdir -p logs
	@echo "Starting API server..."
	@echo "📝 Logs will be saved to logs/api.log (via Python logging)"
	@echo "🎨 Terminal output has colors, file output is clean"
	cd apps/api-server && $(PYTHON) main.py

# Start Celery worker
run-celery: install
	@mkdir -p logs
	@echo "Starting Celery worker..."
	@echo "📝 Logs will be saved to logs/celery.log (via unified Python logging)"
	@echo "🎨 Terminal output has Celery-style colors, file output is clean"
	CELERY_LOG_LEVEL=INFO celery -A coaching_assistant.core.celery_app worker --loglevel=info --concurrency=2 --pool=threads

# Start Celery worker with debug logging
run-celery-debug: install
	@mkdir -p logs
	@echo "Starting Celery worker with debug logging..."
	@echo "📝 Logs will be saved to logs/celery-debug.log (via unified Python logging)"
	@echo "🎨 Terminal output has Celery-style colors, file output is clean"
	CELERY_LOG_LEVEL=DEBUG celery -A coaching_assistant.core.celery_app worker --loglevel=debug --concurrency=2 --pool=threads

# Frontend Development
dev-frontend:
	@mkdir -p logs
	@echo "Starting frontend development server..."
	@echo "Logs will be saved to logs/frontend-dev.log (with colors preserved)"
	@if [ ! -d "apps/web/.next" ]; then \
		echo "  → .next directory not found, running initial build..."; \
		cd apps/web && FORCE_COLOR=1 npm run build 2>&1 | tee ../../logs/frontend-build.log; \
	fi
	@cd apps/web && FORCE_COLOR=1 npm run dev 2>&1 | tee ../../logs/frontend-dev.log

# File-based targets for efficient building
apps/web/.next/BUILD_ID: apps/web/app/* apps/web/components/* apps/web/lib/* apps/web/next.config.js apps/web/package.json
	@mkdir -p logs
	@echo "🔨 Building Next.js frontend..."
	@echo "📋 Production build configuration:"
	@echo "  NODE_ENV=production"
	@echo "  NEXT_PUBLIC_API_URL=https://api.doxa.com.tw"
	@echo "📝 Build logs will be saved to logs/frontend-build.log (with colors preserved)"
	@if [ -f apps/web/.env.local ]; then \
		echo "  → Temporarily moving .env.local for production build"; \
		mv apps/web/.env.local apps/web/.env.local.tmp; \
	fi
	cd apps/web && NODE_ENV=production NEXT_PUBLIC_API_URL=https://api.doxa.com.tw FORCE_COLOR=1 npm run build 2>&1 | tee ../../logs/frontend-build.log
	@if [ -f apps/web/.env.local.tmp ]; then \
		echo "  → Restoring .env.local"; \
		mv apps/web/.env.local.tmp apps/web/.env.local; \
	fi

apps/web/.open-next/worker.js: apps/web/.next/BUILD_ID
	@mkdir -p logs
	@echo "☁️  Building frontend for Cloudflare Workers..."
	@echo "📋 Cloudflare Workers build configuration:"
	@echo "  NODE_ENV=production"
	@echo "  NEXT_PUBLIC_API_URL=https://api.doxa.com.tw (inherited from Next.js build)"
	@echo "📝 Cloudflare Workers build logs will be saved to logs/frontend-cf-build.log"
	@if [ -f apps/web/.env.local ]; then \
		echo "  → Temporarily moving .env.local for production build"; \
		mv apps/web/.env.local apps/web/.env.local.tmp; \
	fi
	cd apps/web && NODE_ENV=production FORCE_COLOR=1 npm run build:cf 2>&1 | tee ../../logs/frontend-cf-build.log
	@if [ -f apps/web/.env.local.tmp ]; then \
		echo "  → Restoring .env.local"; \
		mv apps/web/.env.local.tmp apps/web/.env.local; \
	fi

# Convenience targets that depend on files
build-frontend: apps/web/.next/BUILD_ID

build-frontend-cf: apps/web/.open-next/worker.js

install-frontend:
	@echo "Installing frontend dependencies..."
	cd apps/web && npm install

# Cloudflare Workers Deployment
deploy-frontend:
	@echo "🚀 Deploying frontend to Cloudflare Workers..."
	@echo "📋 Production environment configuration:"
	@echo "  NODE_ENV=production"
	@echo "  NEXT_PUBLIC_API_URL=https://api.doxa.com.tw"
	@echo ""
	@echo "📦 Preparing deployment environment..."
	@if [ -f apps/web/.env.local ]; then \
		echo "  → Backing up .env.local to .env.local.bak"; \
		mv apps/web/.env.local apps/web/.env.local.bak; \
	fi
	@echo "🔧 Starting deployment process..."
	cd apps/web && NODE_ENV=production NEXT_PUBLIC_API_URL=https://api.doxa.com.tw npm run deploy
	@if [ -f apps/web/.env.local.bak ]; then \
		echo "  → Restoring .env.local from backup"; \
		mv apps/web/.env.local.bak apps/web/.env.local; \
	fi
	@echo "✅ Frontend deployment complete!"

deploy-frontend-only: build-frontend-cf
	@echo "🚀 Deploying frontend to Cloudflare Workers (without rebuild)..."
	@echo "📋 Using pre-built configuration with NEXT_PUBLIC_API_URL=https://api.doxa.com.tw"
	cd apps/web && npm run deploy:only
	@echo "✅ Deployment complete!"

preview-frontend: build-frontend-cf
	@mkdir -p logs
	@echo "Starting Cloudflare Workers preview..."
	@echo "Logs will be saved to logs/frontend-preview.log"
	cd apps/web && FORCE_COLOR=1 npx wrangler dev 2>&1 | tee ../../logs/frontend-preview.log

# Unified Development Experience
dev-all:
	@echo "Starting full-stack development..."
	@echo "Note: Run 'make run-api' and 'make dev-frontend' in separate terminals"

build-all: build build-frontend
	@echo "Building all services..."

install-all: install install-frontend
	@echo "Installing all dependencies..."

# Build Docker images
docker-api:
	docker build -t $(DOCKER_API_IMAGE) -t $(DOCKER_API_LATEST) -f apps/api-server/Dockerfile.api .

docker-cli:
	docker build -t $(DOCKER_CLI_IMAGE) -t $(DOCKER_CLI_LATEST) -f apps/cli/Dockerfile .

docker-worker:
	docker build -t $(PACKAGE_NAME)-worker:$(VERSION) -t $(PACKAGE_NAME)-worker:latest -f apps/worker/Dockerfile .

docker-worker-cloudrun:
	docker build -t $(PACKAGE_NAME)-worker-cloudrun:$(VERSION) -t $(PACKAGE_NAME)-worker-cloudrun:latest -f apps/worker/Dockerfile.cloudrun .

docker: docker-api docker-cli docker-worker

# Run the CLI Docker container with volume mapping
docker-run-cli:
	@echo "Running CLI Docker container..."
	@echo "Example usage:"
	@echo "  make docker-run-cli INPUT=./input.vtt OUTPUT=./output.md"
	@echo "  make docker-run-cli INPUT=./input.vtt OUTPUT=./output.xlsx FORMAT=excel"
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Error: INPUT and OUTPUT parameters are required"; \
		echo "Example: make docker-run-cli INPUT=./input.vtt OUTPUT=./output.md"; \
		exit 1; \
	fi
	docker run -it --rm \
		-v $(shell pwd)/$(INPUT):/data/input.vtt:ro \
		-v $(shell pwd)/$(dir $(OUTPUT)):/data/output \
		$(DOCKER_CLI_IMAGE) format-command /data/input.vtt /data/output/$(notdir $(OUTPUT)) $(if $(FORMAT),--format $(FORMAT))

# Backward compatibility
docker-run: docker-run-cli

# Run standalone tests (unit + database integration tests that don't need API server)
test: dev-setup
	@mkdir -p logs
	@echo "Running standalone tests (unit + database integration)..."
	@echo "Test logs will be saved to logs/test.log (with colors preserved)"
	@echo ""
	@echo "🧪 Unit Tests - Fast, isolated tests"
	@echo "🗄️  Database Integration Tests - Tests with SQLite in-memory DB"
	@echo "⚠️  Excluding: E2E tests, API tests, frontend tests (use 'make test-server' for those)"
	@echo ""
	pytest tests/unit/ tests/integration/database/ \
		tests/integration/test_transcript_smoother_integration.py \
		-v --color=yes 2>&1 | tee logs/test.log

# Run unit tests only (fastest)
test-unit: dev-setup
	@mkdir -p logs
	@echo "Running unit tests only..."
	@echo "🧪 Fast, isolated unit tests"
	pytest tests/unit/ -v --color=yes 2>&1 | tee logs/test-unit.log

# Run database integration tests only
test-db: dev-setup
	@mkdir -p logs
	@echo "Running database integration tests..."
	@echo "🗄️  Tests using SQLite in-memory database"
	pytest tests/integration/database/ \
		tests/integration/test_transcript_smoother_integration.py \
		-v --color=yes 2>&1 | tee logs/test-db.log

# Run server-dependent tests (requires API server to be running)
test-server: dev-setup
	@mkdir -p logs
	@echo "Running server-dependent tests..."
	@echo "⚠️  These tests require the API server to be running at localhost:8000"
	@echo "   Start server with: make run-api (in another terminal)"
	@echo ""
	@echo "🌐 API Integration Tests"
	@echo "🔗 ECPay Integration Tests"  
	@echo "🎭 E2E Tests"
	@echo "🖥️  Frontend Tests"
	pytest tests/integration/api/ \
		tests/integration/test_ecpay_*.py \
		tests/integration/test_lemur_integration.py \
		tests/integration/test_webhook_retry_scenarios.py \
		tests/e2e/ \
		tests/frontend/ \
		tests/compatibility/ \
		-v --color=yes 2>&1 | tee logs/test-server.log

# Run payment system tests (requires API server and authentication)
test-payment: dev-setup
	@mkdir -p logs
	@echo "Running payment system tests..."
	@echo "⚠️  These tests require API server and authentication setup"
	@echo "   See: tests/AUTHENTICATION_SETUP.md for setup instructions"
	@echo ""
	python tests/run_payment_qa_tests.py --suite all 2>&1 | tee logs/test-payment.log

# Run all tests (standalone + server-dependent)
test-all: dev-setup
	@mkdir -p logs
	@echo "Running all tests (standalone + server-dependent)..."
	@echo "⚠️  Server-dependent tests will fail if API server is not running"
	pytest tests/ -v --color=yes 2>&1 | tee logs/test-all.log

# Run standalone tests with coverage report
coverage: dev-setup
	@mkdir -p logs htmlcov
	@echo "Running standalone tests with coverage analysis..."
	@echo "============================================"
	@echo "Coverage report will be saved to:"
	@echo "  - Terminal output: logs/coverage.log"
	@echo "  - HTML report: htmlcov/index.html"
	@echo "============================================"
	@$(PIP) install pytest-cov --break-system-packages 2>/dev/null || true
	@pytest tests/unit/ tests/integration/database/ \
		tests/integration/test_database_models.py \
		tests/integration/test_transcript_smoother_integration.py \
		--cov=src/coaching_assistant \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=term:skip-covered \
		--color=yes \
		-v 2>&1 | tee logs/coverage.log
	@echo ""
	@echo "============================================"
	@echo "Coverage Summary:"
	@grep "^TOTAL" logs/coverage.log || echo "Coverage calculation complete"
	@echo "============================================"
	@echo "📊 View detailed HTML report: open htmlcov/index.html"

# Run all tests with coverage report (requires API server)
coverage-all: dev-setup
	@mkdir -p logs htmlcov
	@echo "Running all tests with coverage analysis..."
	@echo "⚠️  Server-dependent tests require API server at localhost:8000"
	@echo "============================================"
	@$(PIP) install pytest-cov --break-system-packages 2>/dev/null || true
	@pytest tests/ \
		--cov=src/coaching_assistant \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=term:skip-covered \
		--color=yes \
		-v 2>&1 | tee logs/coverage-all.log
	@echo ""
	@echo "============================================"
	@echo "📊 View detailed HTML report: open htmlcov/index.html"

# Install development dependencies
dev-setup:
	@echo "Setting up development environment with uv..."
	$(UV) sync --dev
	$(UV) pip install -r apps/api-server/requirements.txt
	$(UV) pip install -r apps/cli/requirements.txt
	$(UV) pip install setuptools wheel build pytest
	$(UV) pip install -e .

# Run linting and formatting with Ruff
lint: dev-setup
	@mkdir -p logs
	@echo "Running Ruff linting and formatting..."
	@echo "Lint logs will be saved to logs/lint.log"
	@echo ""
	@echo "🔧 Formatting code with Ruff..."
	$(UV) run ruff format src/ apps/ tests/ 2>&1 | tee logs/lint.log
	@echo ""
	@echo "🔍 Checking linting rules with Ruff..."
	$(UV) run ruff check src/ apps/ tests/ --fix 2>&1 | tee -a logs/lint.log
	@echo ""
	@echo "📊 Final statistics:"
	$(UV) run ruff check src/ apps/ tests/ --statistics 2>&1 | tee -a logs/lint.log

# Run architecture compliance checks
check-architecture: dev-setup
	@mkdir -p logs
	@echo "Running Clean Architecture compliance checks..."
	@echo "Architecture check logs will be saved to logs/architecture-check.log"
	$(PYTHON) scripts/check_architecture.py 2>&1 | tee logs/architecture-check.log

# Run enum conversion tests
test-enum-conversions: dev-setup
	@mkdir -p logs
	@echo "Running enum conversion tests..."
	@echo "📝 Testing domain ↔ database enum conversions"
	pytest tests/unit/infrastructure/test_enum_conversions.py -v --color=yes 2>&1 | tee logs/test-enum-conversions.log

# Run repository layer tests
test-repository-layers: dev-setup
	@mkdir -p logs
	@echo "Running repository layer conversion tests..."
	@echo "📝 Testing repository _to_domain() and _from_domain() methods"
	pytest tests/integration/repositories/test_repository_conversions.py -v --color=yes 2>&1 | tee logs/test-repository-layers.log

# Run API parameter validation tests
test-api-parameters: dev-setup
	@mkdir -p logs
	@echo "Running API endpoint parameter validation tests..."
	@echo "📝 Testing dependency injection and response function parameters"
	pytest tests/api/test_dependency_injection.py -v --color=yes 2>&1 | tee logs/test-api-parameters.log

# Run all architecture compliance tests
test-architecture: test-enum-conversions test-repository-layers test-api-parameters check-architecture
	@echo "✅ All architecture compliance tests completed"
	@echo "📊 Check logs/ directory for detailed results"

# Create a distribution package
dist: clean
	$(UV) pip install setuptools wheel build
	$(UV) run python -m build

# Install the package from the distribution
dist-install: dist
	$(UV) pip install dist/*.whl

# Create aliases for zsh compatibility
make-lint:
	/usr/bin/make lint

make-test-unit:
	/usr/bin/make test-unit

# Version Management
version-check:
	@echo "Checking version consistency across all files..."
	@python3 scripts/sync-version.py --check

version-sync:
	@echo "Synchronizing versions from version.json..."
	@python3 scripts/sync-version.py

version-show:
	@echo "Current version information:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "Master Version (version.json): $$(python3 -c "import json; print(json.load(open('version.json'))['version'])")"
	@echo "Python Package (pyproject.toml): $$(grep -m 1 'version' pyproject.toml | cut -d '"' -f 2)"
	@if [ -f "apps/web/package.json" ]; then \
		echo "Frontend (apps/web/package.json): $$(python3 -c "import json; print(json.load(open('apps/web/package.json'))['version'])")"; \
	fi
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

version-bump-patch:
	@echo "Bumping patch version..."
	@python3 scripts/bump-version.py patch

version-bump-minor:
	@echo "Bumping minor version..."
	@python3 scripts/bump-version.py minor

version-bump-major:
	@echo "Bumping major version..."
	@python3 scripts/bump-version.py major

# Help target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Backend (Python):"
	@echo "  all            : Clean and build the package"
	@echo "  clean          : Remove all build artifacts (backend + frontend)"
	@echo "  clean-frontend : Remove only frontend build artifacts"
	@echo "  build          : Build the package"
	@echo "  install        : Install the package locally in development mode"
	@echo "  run-api        : Start the API server (logs via Python logging to logs/api.log)"
	@echo "  run-celery     : Start Celery worker (logs via Python logging to logs/celery.log)"
	@echo "  run-celery-debug : Start Celery worker with debug logging (logs to logs/celery-debug.log)"
	@echo "  dev-setup      : Install development dependencies"
	@echo "  test           : Run standalone tests (unit + database integration)"
	@echo "  test-unit      : Run unit tests only (fastest)"
	@echo "  test-db        : Run database integration tests only"  
	@echo "  test-server    : Run server-dependent tests (requires API server)"
	@echo "  test-payment   : Run payment system tests (requires API + auth)"
	@echo "  test-all       : Run all tests (standalone + server-dependent)"
	@echo "  coverage       : Run standalone tests with coverage report"
	@echo "  coverage-all   : Run all tests with coverage (requires API server)"
	@echo "  lint           : Run Ruff formatting and linting (logs to logs/lint.log)"
	@echo ""
	@echo "Zsh compatibility aliases:"
	@echo "  make-lint      : Run Ruff formatting and linting (alias for zsh users)"
	@echo "  make-test-unit : Run unit tests (alias for zsh users)"
	@echo ""
	@echo "Version Management:"
	@echo "  version-show   : Display current version from all files"
	@echo "  version-check  : Check version consistency across all files"
	@echo "  version-sync   : Sync all versions from version.json (single source of truth)"
	@echo "  version-bump-patch : Bump patch version (x.y.Z) - for bug fixes"
	@echo "  version-bump-minor : Bump minor version (x.Y.0) - for new features"
	@echo "  version-bump-major : Bump major version (X.0.0) - for breaking changes"
	@echo ""
	@echo "Frontend (Node.js):"
	@echo "  dev-frontend     : Start frontend development server (logs to logs/frontend-dev.log)"
	@echo "  build-frontend   : Build Next.js frontend only (logs to logs/frontend-build.log)"
	@echo "  build-frontend-cf: Build frontend for Cloudflare Workers (logs to logs/frontend-cf-build.log)"
	@echo "  install-frontend : Install frontend dependencies"
	@echo "  deploy-frontend  : Deploy frontend to Cloudflare Workers (shows API URL, auto-builds)"
	@echo "  deploy-frontend-only : Deploy pre-built frontend (requires build-frontend-cf first)"
	@echo "  preview-frontend : Start Cloudflare Workers preview (logs to logs/frontend-preview.log)"
	@echo ""
	@echo "Full-stack:"
	@echo "  dev-all        : Show instructions for full-stack development"
	@echo "  build-all      : Build all services (backend + frontend)"
	@echo "  install-all    : Install all dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  docker           : Build API, CLI, and Worker Docker images"
	@echo "  docker-api       : Build API Docker image"
	@echo "  docker-cli       : Build CLI Docker image"
	@echo "  docker-worker    : Build Worker Docker image (for Render/general use)"
	@echo "  docker-worker-cloudrun : Build Worker Docker image for GCP Cloud Run"
	@echo "  docker-run-cli   : Run the CLI Docker container"
	@echo "  docker-run       : Run the CLI Docker container (backward compatibility)"
	@echo ""
	@echo "Distribution:"
	@echo "  dist           : Create distribution package"
	@echo "  dist-install   : Install from distribution package"
	@echo ""
	@echo "Logging:"
	@echo "  Python services use proper logging framework with dual output:"
	@echo "  - Terminal: Colorized output for development"
	@echo "  - Files: Clean structured logs in logs/ directory with rotation"
	@echo "  - Frontend services still use tee for npm/node tools"
	@echo "  Logs are automatically ignored by git (.gitignore includes logs/)"
	@echo ""
	@echo "  help           : Show this help message"
