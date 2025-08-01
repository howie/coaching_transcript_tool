# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy shared core logic package
COPY packages/core-logic/ ./packages/core-logic/

# Copy CLI application files
COPY apps/cli/requirements.txt ./apps/cli/
COPY apps/cli/main.py ./apps/cli/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./apps/cli/requirements.txt

# Create a volume mount point for data
VOLUME ["/data"]

# Set the entrypoint to our CLI main.py
ENTRYPOINT ["python", "./apps/cli/main.py"]

# Default command to show help
CMD ["--help"]
