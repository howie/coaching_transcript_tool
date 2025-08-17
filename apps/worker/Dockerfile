FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code and configuration
COPY src/ ./src/
COPY pyproject.toml requirements.txt ./

# Copy requirements and install dependencies
COPY apps/api-server/requirements.txt ./apps/api-server/

# Install Python dependencies
RUN pip install --no-cache-dir -r ./apps/api-server/requirements.txt
RUN pip install -e .

# Copy alembic configuration
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set Python path
ENV PYTHONPATH=/app/src:/app \
    IS_CONTAINER=true

# Health check for Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A coaching_assistant.core.celery_app inspect ping

# Start Celery worker
CMD ["celery", "-A", "coaching_assistant.core.celery_app", "worker", "--loglevel=info", "--concurrency=4"]