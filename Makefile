.PHONY: clean clean-frontend build install docker docker-run test lint dev-frontend build-frontend install-frontend deploy-frontend preview-frontend dev-all build-all install-all

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
	rm -rf .next/
	rm -rf out/
	rm -rf apps/web/tsconfig.tsbuildinfo

# Build the package
build: clean
	$(PYTHON) -m pip install -r apps/api-server/requirements.txt --break-system-packages

# Install the package locally
install: build
	$(PIP) install -r apps/api-server/requirements.txt --break-system-packages
	$(PIP) install -e packages/core-logic --break-system-packages

# Start API server
run-api: install
	cd apps/api-server && $(PYTHON) main.py

# Frontend Development
dev-frontend:
	@echo "Starting frontend development server..."
	cd apps/web && npm run dev

build-frontend:
	@echo "Building frontend for production..."
	cd apps/web && npm run build

install-frontend:
	@echo "Installing frontend dependencies..."
	cd apps/web && npm install

# Cloudflare Workers Deployment
deploy-frontend:
	@echo "Deploying frontend to Cloudflare Workers..."
	cd apps/web && npm run deploy

preview-frontend:
	@echo "Starting Cloudflare Workers preview..."
	cd apps/web && npm run preview

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
	@echo "  dev-frontend   : Start frontend development server"
	@echo "  build-frontend : Build frontend for production"
	@echo "  install-frontend : Install frontend dependencies"
	@echo "  deploy-frontend : Deploy frontend to Cloudflare Workers"
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
