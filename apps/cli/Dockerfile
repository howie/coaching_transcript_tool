# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src:/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code and configuration
COPY src/ ./src/
COPY pyproject.toml requirements.txt ./

# Copy CLI application files
COPY apps/cli/requirements.txt ./apps/cli/
COPY apps/cli/main.py ./apps/cli/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./apps/cli/requirements.txt
RUN pip install -e .

# Create a volume mount point for data
VOLUME ["/data"]

# Set the entrypoint to our CLI main.py
ENTRYPOINT ["python", "./apps/cli/main.py"]

# Default command to show help
CMD ["--help"]
