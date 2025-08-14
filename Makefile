.PHONY: clean clean-frontend build install docker docker-run test lint dev-frontend build-frontend build-frontend-cf install-frontend deploy-frontend preview-frontend dev-all build-all install-all

# Variables
PACKAGE_NAME = coaching_transcript_tool
VERSION = $(shell grep -m 1 'version' packages/core-logic/pyproject.toml | cut -d '"' -f 2)
DOCKER_API_IMAGE = $(PACKAGE_NAME)-api:$(VERSION)
DOCKER_CLI_IMAGE = $(PACKAGE_NAME)-cli:$(VERSION)
DOCKER_API_LATEST = $(PACKAGE_NAME)-api:latest
DOCKER_CLI_LATEST = $(PACKAGE_NAME)-cli:latest
PYTHON = python3
PIP = pip

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
	@echo "Installing core logic package..."
	$(PYTHON) -m pip install -e packages/core-logic --break-system-packages
	@echo "Installing api-server dependencies..."
	$(PYTHON) -m pip install -r apps/api-server/requirements.txt --break-system-packages

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
	@echo "Building Next.js frontend..."
	@echo "Build logs will be saved to logs/frontend-build.log (with colors preserved)"
	cd apps/web && FORCE_COLOR=1 npm run build 2>&1 | tee ../../logs/frontend-build.log

apps/web/.open-next/worker.js: apps/web/.next/BUILD_ID
	@mkdir -p logs
	@echo "Building frontend for Cloudflare Workers..."
	@echo "Cloudflare Workers build logs will be saved to logs/frontend-cf-build.log"
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
	@echo "Deploying frontend to Cloudflare Workers..."
	@echo "Preparing production environment..."
	@if [ -f apps/web/.env.local ]; then \
		echo "  → Backing up .env.local to .env.local.bak"; \
		mv apps/web/.env.local apps/web/.env.local.bak; \
	fi
	cd apps/web && npm run deploy
	@if [ -f apps/web/.env.local.bak ]; then \
		echo "  → Restoring .env.local from backup"; \
		mv apps/web/.env.local.bak apps/web/.env.local; \
	fi
	@echo "✅ Deployment complete!"

deploy-frontend-only: build-frontend-cf
	@echo "Deploying frontend to Cloudflare Workers (without rebuild)..."
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

# Run tests
test: dev-setup
	@mkdir -p logs
	@echo "Running tests..."
	@echo "Test logs will be saved to logs/test.log (with colors preserved)"
	pytest packages/core-logic/tests/ -v --color=yes 2>&1 | tee logs/test.log

# Install development dependencies
dev-setup:
	$(PIP) install -r apps/api-server/requirements.txt --break-system-packages
	$(PIP) install -r apps/cli/requirements.txt --break-system-packages
	$(PIP) install setuptools wheel build flake8 pytest --break-system-packages
	$(PIP) install -e packages/core-logic --break-system-packages

# Run linting
lint: dev-setup
	@mkdir -p logs
	@echo "Running linting..."
	@echo "Lint logs will be saved to logs/lint.log"
	$(PYTHON) -m flake8 packages/core-logic/src/ packages/core-logic/tests/ 2>&1 | tee logs/lint.log

# Create a distribution package
dist: clean
	$(PYTHON) -m pip install setuptools wheel build --break-system-packages
	$(PYTHON) -m build

# Install the package from the distribution
dist-install: dist
	$(PIP) install dist/*.whl --break-system-packages

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
	@echo "  test           : Run tests (logs to logs/test.log)"
	@echo "  lint           : Run linting (logs to logs/lint.log)"
	@echo ""
	@echo "Frontend (Node.js):"
	@echo "  dev-frontend     : Start frontend development server (logs to logs/frontend-dev.log)"
	@echo "  build-frontend   : Build Next.js frontend only (logs to logs/frontend-build.log)"
	@echo "  build-frontend-cf: Build frontend for Cloudflare Workers (logs to logs/frontend-cf-build.log)"
	@echo "  install-frontend : Install frontend dependencies"
	@echo "  deploy-frontend  : Deploy frontend to Cloudflare Workers"
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
