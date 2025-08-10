# Production Celery Deployment Guide

This document explains how to deploy Celery workers in production environments, specifically for Render.com and GCP Cloud Run.

## Overview

In production, Celery workers should run as separate services from your web API to ensure:
- **Scalability**: Independent scaling of web and worker processes
- **Reliability**: Worker failures don't affect web service
- **Resource Management**: Different CPU/memory requirements
- **Deployment Flexibility**: Deploy workers and web services independently

## Architecture Options

### Option 1: Separate Service (Recommended)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Service   │    │  Redis (Managed) │    │ Worker Service  │
│   (Port: 8000)  │◄──►│  (Cloud Redis)   │◄──►│  (Background)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Option 2: Combined Service (Development/Small Scale)
```
┌─────────────────────────────────┐    ┌──────────────────┐
│        Single Service           │    │  Redis (Managed) │
│  ┌─────────────┐ ┌─────────────┐│◄──►│  (Cloud Redis)   │
│  │ Web Process │ │Worker Process││    └──────────────────┘
│  │ (Port: 8000)│ │(Background) ││
│  └─────────────┘ └─────────────┘│
└─────────────────────────────────┘
```

## Render.com Deployment

### Method 1: Separate Worker Service (Recommended)

#### 1. Create Celery Worker Dockerfile

Create `apps/worker/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY apps/api-server/requirements.txt /app/requirements.txt
COPY packages/core-logic /app/packages/core-logic

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e packages/core-logic

# Copy source code
COPY packages/core-logic/src /app/packages/core-logic/src

# Set Python path
ENV PYTHONPATH=/app/packages/core-logic/src:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A coaching_assistant.core.celery_app inspect ping

# Start Celery worker
CMD ["celery", "-A", "coaching_assistant.core.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
```

#### 2. Create Worker Service on Render

1. **Create New Service**:
   - Service Type: `Background Worker`
   - Repository: Your GitHub repo
   - Branch: `main`

2. **Configure Build Settings**:
   ```
   Build Command: docker build -f apps/worker/Dockerfile -t worker .
   Start Command: celery -A coaching_assistant.core.celery_app worker --loglevel=info --concurrency=4
   ```

3. **Environment Variables**:
   ```
   DATABASE_URL=<your_postgres_url>
   REDIS_URL=<your_redis_url>
   GOOGLE_APPLICATION_CREDENTIALS_JSON=<base64_service_account>
   GOOGLE_PROJECT_ID=<your_project_id>
   ENVIRONMENT=production
   ```

4. **Resource Configuration**:
   - Instance Type: `Standard` (1 CPU, 2GB RAM)
   - Auto-scaling: Enable with 1-3 instances

#### 3. Update API Service

Update your existing API service to remove worker processes:

```python
# apps/api-server/main.py - Remove any Celery worker startup code
# Keep only FastAPI application
```

### Method 2: Combined Service (Simpler Setup)

#### 1. Create Startup Script

Create `apps/api-server/start_production.sh`:

```bash
#!/bin/bash
set -e

echo "Starting production services..."

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A coaching_assistant.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --detach \
    --pidfile=/tmp/celery_worker.pid \
    --logfile=/tmp/celery_worker.log

# Start FastAPI application
echo "Starting FastAPI application..."
exec python main.py
```

#### 2. Update Dockerfile

```dockerfile
# Add to your existing API Dockerfile
COPY apps/api-server/start_production.sh /app/start_production.sh
RUN chmod +x /app/start_production.sh

CMD ["/app/start_production.sh"]
```

#### 3. Configure Render Service

```
Start Command: /app/start_production.sh
```

## GCP Cloud Run Deployment

### Method 1: Separate Services

#### 1. Create Worker Container

```dockerfile
# apps/worker/Dockerfile.cloudrun
FROM python:3.11-slim

WORKDIR /app

# Install dependencies (same as Render)
COPY apps/api-server/requirements.txt .
COPY packages/core-logic packages/core-logic
RUN pip install -r requirements.txt
RUN pip install -e packages/core-logic

# Copy source
COPY packages/core-logic/src packages/core-logic/src

ENV PYTHONPATH=/app/packages/core-logic/src:$PYTHONPATH
ENV PORT=8080

# Cloud Run requires HTTP endpoint for health checks
COPY apps/worker/health_server.py /app/health_server.py

# Start both health server and Celery worker
CMD python health_server.py & celery -A coaching_assistant.core.celery_app worker --loglevel=info --concurrency=4
```

#### 2. Create Health Check Server

Create `apps/worker/health_server.py`:

```python
"""
Simple HTTP server for Cloud Run health checks
"""
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), HealthHandler)
    server.serve_forever()

if __name__ == '__main__':
    start_health_server()
```

#### 3. Deploy with gcloud

```bash
# Build and deploy worker service
gcloud run deploy coaching-worker \
    --source=apps/worker \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="DATABASE_URL=${DATABASE_URL},REDIS_URL=${REDIS_URL}"

# Deploy API service (existing)
gcloud run deploy coaching-api \
    --source=apps/api-server \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated
```

### Method 2: Using Cloud Tasks (Alternative)

For Cloud Run, consider using Google Cloud Tasks instead of Celery:

```python
from google.cloud import tasks_v2

# Replace Celery tasks with Cloud Tasks
def queue_transcription_task(session_id: str, gcs_path: str):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project_id, location, queue_name)
    
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': 'https://your-worker-service/transcribe',
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'session_id': session_id,
                'gcs_path': gcs_path
            }).encode()
        }
    }
    
    return client.create_task(parent=parent, task=task)
```

## Managed Redis Services

### Render Redis

```bash
# Create Redis addon in Render dashboard
# Connection URL format:
REDIS_URL=rediss://:password@hostname:port
```

### Google Cloud Memorystore

```bash
# Create Redis instance
gcloud redis instances create coaching-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x

# Get connection info
gcloud redis instances describe coaching-redis --region=us-central1
```

### Redis Cloud (Recommended for Multi-Cloud)

```bash
# Use Redis Cloud for both Render and GCP
# Provides consistent Redis URL across platforms
REDIS_URL=redis://default:password@host:port
```

## Production Configuration

### Environment Variables

```bash
# Required for all platforms
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port/db
GOOGLE_APPLICATION_CREDENTIALS_JSON=<base64_credentials>
GOOGLE_PROJECT_ID=your-project-id
ENVIRONMENT=production

# Celery-specific
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
WORKER_CONCURRENCY=4
TASK_TIME_LIMIT=7200

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=<your_sentry_dsn>  # Optional monitoring
```

### Resource Recommendations

#### Render.com
- **API Service**: Standard (1 CPU, 2GB RAM)
- **Worker Service**: Standard+ (2 CPU, 4GB RAM)
- **Redis**: 1GB plan

#### GCP Cloud Run
- **API Service**: 1 CPU, 2GB RAM, 0-100 instances
- **Worker Service**: 2 CPU, 4GB RAM, 1-10 instances
- **Redis**: 1GB Standard tier

## Monitoring & Logging

### Celery Monitoring

Add monitoring to your worker:

```python
# packages/core-logic/src/coaching_assistant/core/celery_config.py
from celery.signals import worker_ready, task_prerun, task_postrun

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    logger.info(f"Celery worker {sender.hostname} is ready")

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    logger.info(f"Task {task.name}[{task_id}] started")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, state=None, **kwargs):
    logger.info(f"Task {task.name}[{task_id}] finished with state {state}")
```

### Health Checks

```python
# Add to worker service
@celery_app.task
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Check worker health
def check_worker_health():
    result = health_check.delay()
    return result.get(timeout=10)
```

## Scaling Considerations

### Horizontal Scaling
- Scale workers based on queue length
- Use Redis monitoring for queue metrics
- Set up auto-scaling based on CPU/memory usage

### Vertical Scaling
- Monitor task execution time
- Adjust worker concurrency based on I/O vs CPU workload
- Audio transcription is I/O bound, so higher concurrency works well

### Cost Optimization
- Use spot instances for workers when available
- Scale down workers during low-usage periods
- Consider serverless options for intermittent workloads

---

## Troubleshooting

### Common Issues

1. **Workers not connecting to Redis**
   - Check Redis URL format
   - Verify network connectivity
   - Test Redis auth credentials

2. **Tasks stuck in pending state**
   - Check worker logs
   - Verify worker registration
   - Monitor Redis memory usage

3. **Memory issues with large audio files**
   - Increase worker memory limits
   - Process audio in chunks
   - Use streaming for large files

4. **High latency**
   - Use dedicated Redis instance
   - Optimize task serialization
   - Consider task routing strategies

For platform-specific issues:
- **Render.com**: Check service logs in dashboard
- **GCP Cloud Run**: Use Cloud Logging and Monitoring
- **Redis**: Monitor connection pools and memory usage