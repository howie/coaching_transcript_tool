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
	cd apps/api-server && $(PYTHON) main.py

# Frontend Development
dev-frontend:
	@echo "Starting frontend development server..."
	cd apps/web && npm run dev

# File-based targets for efficient building
apps/web/.next/BUILD_ID: apps/web/app/* apps/web/components/* apps/web/lib/* apps/web/next.config.js apps/web/package.json
	@echo "Building Next.js frontend..."
	cd apps/web && npm run build

apps/web/.open-next/worker.js: apps/web/.next/BUILD_ID
	@echo "Building frontend for Cloudflare Workers..."
	@if [ -f apps/web/.env.local ]; then \
		echo "  → Temporarily moving .env.local for production build"; \
		mv apps/web/.env.local apps/web/.env.local.tmp; \
	fi
	cd apps/web && NODE_ENV=production npm run build:cf
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
	@echo "Starting Cloudflare Workers preview..."
	cd apps/web && npx wrangler dev

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

docker: docker-api docker-cli

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
	pytest packages/core-logic/tests/

# Install development dependencies
dev-setup:
	$(PIP) install -r apps/api-server/requirements.txt --break-system-packages
	$(PIP) install -r apps/cli/requirements.txt --break-system-packages
	$(PIP) install setuptools wheel build flake8 pytest --break-system-packages
	$(PIP) install -e packages/core-logic --break-system-packages

# Run linting
lint: dev-setup
	$(PYTHON) -m flake8 packages/core-logic/src/ packages/core-logic/tests/

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
	@echo "  run-api        : Start the API server"
	@echo "  dev-setup      : Install development dependencies"
	@echo "  test           : Run tests"
	@echo "  lint           : Run linting"
	@echo ""
	@echo "Frontend (Node.js):"
	@echo "  dev-frontend     : Start frontend development server"
	@echo "  build-frontend   : Build Next.js frontend only"
	@echo "  build-frontend-cf: Build frontend for Cloudflare Workers (includes Next.js build)"
	@echo "  install-frontend : Install frontend dependencies"
	@echo "  deploy-frontend  : Deploy frontend to Cloudflare Workers"
	@echo "  preview-frontend : Start Cloudflare Workers preview"
	@echo ""
	@echo "Full-stack:"
	@echo "  dev-all        : Show instructions for full-stack development"
	@echo "  build-all      : Build all services (backend + frontend)"
	@echo "  install-all    : Install all dependencies"
	@echo ""
	@echo "Docker:"
	@echo "  docker         : Build both API and CLI Docker images"
	@echo "  docker-api     : Build API Docker image"
	@echo "  docker-cli     : Build CLI Docker image"
	@echo "  docker-run-cli : Run the CLI Docker container"
	@echo "  docker-run     : Run the CLI Docker container (backward compatibility)"
	@echo ""
	@echo "Distribution:"
	@echo "  dist           : Create distribution package"
	@echo "  dist-install   : Install from distribution package"
	@echo ""
	@echo "  help           : Show this help message"
