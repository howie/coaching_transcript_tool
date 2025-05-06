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

# Install development dependencies
dev-setup:
	$(PIP) install -r requirements.txt
	$(PIP) install --upgrade pip setuptools wheel build
	$(PIP) install -e .

# Build Docker image
docker:
	docker build -t $(DOCKER_IMAGE) -t $(DOCKER_LATEST) .

# Run the Docker container
docker-run:
	@echo "Running Docker container..."
	@echo "Usage: docker run -v /path/to/data:/data $(DOCKER_IMAGE) -m src.vtt /data/input.vtt /data/output.xlsx -Coach 'Coach Name' -Client 'Client Name'"
	docker run -it --rm $(DOCKER_IMAGE) -m src.vtt --help

# Run tests
test:
	pytest tests/

# Run linting
lint:
	flake8 src/ tests/

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
