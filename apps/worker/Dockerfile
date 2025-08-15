FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY apps/api-server/requirements.txt /app/requirements.txt
COPY src/ /app/src/
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

# Copy alembic configuration
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Health check for Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A coaching_assistant.core.celery_app inspect ping

# Start Celery worker
CMD ["celery", "-A", "coaching_assistant.core.celery_app", "worker", "--loglevel=info", "--concurrency=4"]