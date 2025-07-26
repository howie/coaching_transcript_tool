.PHONY: clean build install docker docker-run test lint

# Variables
PACKAGE_NAME = coaching_transcript_tool
VERSION = $(shell grep -m 1 'version' pyproject.toml | cut -d '"' -f 2)
DOCKER_IMAGE = $(PACKAGE_NAME):$(VERSION)
DOCKER_LATEST = $(PACKAGE_NAME):latest
PYTHON = python3
PIP = pip

# Default target
all: clean build

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

# Build the package
build: clean
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install --upgrade setuptools wheel build
	$(PYTHON) -m build

# Install the package locally
install: build
	$(PIP) install -e .



# Build Docker image
docker:
	docker build -t $(DOCKER_IMAGE) -t $(DOCKER_LATEST) .

# Run the Docker container with volume mapping
docker-run:
	@echo "Running Docker container..."
	@echo "Example usage:"
	@echo "  make docker-run INPUT=./input.vtt OUTPUT=./output.md"
	@echo "  make docker-run INPUT=./input.vtt OUTPUT=./output.xlsx FORMAT=excel"
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Error: INPUT and OUTPUT parameters are required"; \
		echo "Example: make docker-run INPUT=./input.vtt OUTPUT=./output.md"; \
		exit 1; \
	fi
	docker run -it --rm \
		-v $(shell pwd)/$(INPUT):/input.vtt:ro \
		-v $(shell pwd)/$(dir $(OUTPUT)):/output \
		$(DOCKER_IMAGE) format-command /input.vtt /output/$(notdir $(OUTPUT)) $(if $(FORMAT),--format $(FORMAT))

# Run tests
test:
	pytest tests/

# Install development dependencies
dev-setup:
	$(PIP) install -r requirements.txt
	$(PIP) install --upgrade pip setuptools wheel build flake8 pytest
	$(PIP) install -e .

# Run linting
lint: dev-setup
	$(PYTHON) -m flake8 src/ tests/

# Create a distribution package
dist: clean
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install --upgrade setuptools wheel build
	$(PYTHON) -m build

# Install the package from the distribution
dist-install: dist
	$(PIP) install dist/*.whl

# Help target
help:
	@echo "Available targets:"
	@echo "  all          : Clean and build the package"
	@echo "  clean        : Remove build artifacts"
	@echo "  build        : Build the package"
	@echo "  install      : Install the package locally in development mode"
	@echo "  dev-setup    : Install development dependencies"
	@echo "  docker       : Build Docker image"
	@echo "  docker-run   : Run the Docker container"
	@echo "  test         : Run tests"
	@echo "  lint         : Run linting"
	@echo "  dist         : Create distribution package"
	@echo "  dist-install : Install from distribution package"
	@echo "  help         : Show this help message"
