FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY apps/api-server/requirements.txt /app/requirements.txt
COPY packages/core-logic /app/packages/core-logic

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e packages/core-logic

# Copy source code
COPY packages/core-logic/src /app/packages/core-logic/src

# Set Python path
ENV PYTHONPATH=/app/packages/core-logic/src:$PYTHONPATH

# Health check for Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A coaching_assistant.core.celery_app inspect ping

# Start Celery worker
CMD ["celery", "-A", "coaching_assistant.core.celery_app", "worker", "--loglevel=info", "--concurrency=4"]