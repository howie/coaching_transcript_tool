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

## Scaling Strategies & Best Practices

### 🎯 Concurrency Configuration Guidelines

#### **Task Characteristics Analysis**
Audio transcription tasks are:
- **Duration**: 3-5 minutes processing time per task
- **Nature**: I/O intensive (STT API calls) + moderate CPU usage
- **Memory**: ~200-500MB per concurrent task

#### **Scaling Strategy Decision Matrix**

| Deployment Scale | Strategy | Worker Instances | Concurrency per Instance | Total Throughput |
|------------------|----------|------------------|--------------------------|------------------|
| **Small** (< 50 users) | Vertical Scaling | 1 instance | `--concurrency=4` | 4 concurrent tasks |
| **Medium** (50-200 users) | Mixed Scaling | 2-3 instances | `--concurrency=3` | 6-9 concurrent tasks |
| **Large** (200+ users) | Horizontal Scaling | 4+ instances | `--concurrency=2-3` | 8-12+ concurrent tasks |
| **Enterprise** (1000+ users) | Multi-Region Horizontal | 10+ instances | `--concurrency=2-3` | 20-30+ concurrent tasks |

### 🚀 Production Configuration Examples

#### **AWS ECS/Fargate Configuration**
```yaml
# Small Scale Deployment
service_small:
  cpu: 1024  # 1 vCPU
  memory: 2048  # 2 GB
  desired_count: 1
  environment:
    - CELERY_CONCURRENCY=4
  
# Medium Scale Deployment  
service_medium:
  cpu: 1024  # 1 vCPU
  memory: 2048  # 2 GB
  desired_count: 3
  environment:
    - CELERY_CONCURRENCY=3
  autoscaling:
    min_capacity: 2
    max_capacity: 5
    target_cpu: 70

# Large Scale Deployment
service_large:
  cpu: 2048  # 2 vCPU
  memory: 4096  # 4 GB
  desired_count: 4
  environment:
    - CELERY_CONCURRENCY=2
  autoscaling:
    min_capacity: 4
    max_capacity: 12
    target_cpu: 60
```

#### **Google Cloud Run Configuration**
```yaml
# Medium Scale
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: celery-worker
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "2"
        autoscaling.knative.dev/maxScale: "8"
        autoscaling.knative.dev/target: "3"  # concurrent requests per instance
    spec:
      containers:
      - image: gcr.io/project/celery-worker
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
        env:
        - name: CELERY_CONCURRENCY
          value: "3"
        - name: WORKER_MAX_TASKS_PER_CHILD
          value: "20"
```

#### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 3  # Horizontal scaling
  template:
    spec:
      containers:
      - name: celery-worker
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        args: 
        - "celery"
        - "-A"
        - "coaching_assistant.core.celery_app"
        - "worker"
        - "--concurrency=3"
        - "--max-tasks-per-child=15"
        - "--pool=threads"
```

### 📊 Auto-Scaling Configuration

#### **Queue-Based Auto-Scaling (Recommended)**
```python
# Monitor Redis queue length for scaling decisions
def get_queue_metrics():
    """Get queue length for auto-scaling decisions"""
    from redis import Redis
    import os
    
    redis_client = Redis.from_url(os.getenv('REDIS_URL'))
    
    return {
        'queue_length': redis_client.llen('celery'),
        'active_tasks': len(redis_client.smembers('celery_active_tasks')),
        'failed_tasks': redis_client.llen('celery_failed')
    }

# Auto-scaling thresholds
SCALING_THRESHOLDS = {
    'scale_up_queue_length': 10,    # Scale up if > 10 tasks waiting
    'scale_down_queue_length': 2,   # Scale down if < 2 tasks waiting
    'max_wait_time_minutes': 5,     # Scale up if tasks wait > 5 minutes
}
```

#### **AWS CloudWatch Auto-Scaling**
```yaml
# Custom metric for queue length
MetricFilter:
  Type: AWS::Logs::MetricFilter
  Properties:
    LogGroupName: /ecs/celery-worker
    FilterPattern: '[timestamp, level="INFO", message="Queue length:", queue_length]'
    MetricTransformations:
      - MetricNamespace: CeleryQueue
        MetricName: QueueLength
        MetricValue: $queue_length

# Auto-scaling policy
ScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyType: TargetTrackingScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 5.0  # Target queue length
      CustomMetricSpecification:
        MetricName: QueueLength
        Namespace: CeleryQueue
        Statistic: Average
```

#### **Google Cloud Monitoring Auto-Scaling**
```yaml
# HPA based on custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
      target:
        type: AverageValue
        averageValue: "5"  # Scale when queue length > 5
```

### 💰 Cost Optimization Strategies

#### **Spot Instance Configuration**
```bash
# AWS ECS with Spot instances
aws ecs create-service \
    --service-name celery-worker-spot \
    --capacity-provider-strategy \
        capacityProvider=FARGATE_SPOT,weight=70 \
        capacityProvider=FARGATE,weight=30
```

#### **Scheduled Scaling**
```yaml
# Scale up during business hours
BusinessHoursScale:
  Type: AWS::ApplicationAutoScaling::ScheduledAction
  Properties:
    Schedule: cron(0 8 ? * MON-FRI *)  # 8 AM weekdays
    ScalableDimension: ecs:service:DesiredCount
    MinCapacity: 4
    MaxCapacity: 12

# Scale down during off-hours  
OffHoursScale:
  Type: AWS::ApplicationAutoScaling::ScheduledAction
  Properties:
    Schedule: cron(0 18 ? * MON-FRI *)  # 6 PM weekdays
    ScalableDimension: ecs:service:DesiredCount
    MinCapacity: 1
    MaxCapacity: 3
```

### 📈 Monitoring & Alerting

#### **Key Metrics to Monitor**

```python
# Essential Celery metrics
CRITICAL_METRICS = {
    # Queue health
    'redis_queue_length': {'threshold': 20, 'alert': 'high_queue'},
    'task_wait_time_avg': {'threshold': 300, 'alert': 'slow_processing'},  # 5 minutes
    
    # Worker health  
    'worker_cpu_usage': {'threshold': 80, 'alert': 'high_cpu'},
    'worker_memory_usage': {'threshold': 85, 'alert': 'high_memory'},
    'active_worker_count': {'min': 1, 'alert': 'no_workers'},
    
    # Task outcomes
    'task_failure_rate': {'threshold': 0.05, 'alert': 'high_failures'},  # 5%
    'task_processing_time_p95': {'threshold': 600, 'alert': 'slow_tasks'},  # 10 minutes
    
    # Business metrics
    'concurrent_users': {'threshold': 100, 'alert': 'traffic_spike'},
    'transcriptions_per_hour': {'min': 10, 'alert': 'low_throughput'},
}
```

#### **Alerting Rules**
```yaml
# Prometheus/AlertManager rules
groups:
- name: celery_alerts
  rules:
  - alert: HighQueueLength
    expr: redis_queue_length > 20
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Celery queue length is high"
      description: "Queue has {{ $value }} tasks waiting"

  - alert: NoActiveWorkers
    expr: celery_active_workers == 0
    for: 30s
    labels:
      severity: critical
    annotations:
      summary: "No active Celery workers"
      
  - alert: HighTaskFailureRate
    expr: rate(celery_task_failures[5m]) / rate(celery_task_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
```

### 🎯 Performance Tuning Guidelines

#### **Concurrency vs Performance Trade-offs**

| Concurrency Level | Pros | Cons | Best For |
|-------------------|------|------|----------|
| **Low (1-2)** | Stable memory usage, easier debugging | Lower throughput | Development, debugging |
| **Medium (3-4)** | Balanced performance/stability | Moderate resource usage | Most production workloads |
| **High (5-8)** | Maximum throughput | Higher memory usage, potential I/O contention | High-load scenarios |
| **Very High (8+)** | Extreme throughput | Memory issues, diminishing returns | Specialized high-throughput needs |

#### **Worker Configuration Best Practices**

```python
# Production celery_app.py configuration
celery_app.conf.update(
    # Prevent memory leaks
    worker_max_tasks_per_child=50,
    
    # Pool configuration for I/O intensive tasks
    worker_pool='threads',  # Better for I/O bound tasks
    worker_pool_restarts=True,
    
    # Prefetch optimization
    worker_prefetch_multiplier=1,  # Important for long-running tasks
    
    # Task routing for different priorities
    task_routes={
        'transcribe_audio': {'queue': 'high_priority'},
        'batch_operations': {'queue': 'low_priority'},
    },
    
    # Results optimization
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'celery',
        'visibility_timeout': 43200,  # 12 hours
    },
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
)
```

### 🏗️ Multi-Region Deployment

For global scale applications:

```yaml
# Multi-region architecture
regions:
  us-east-1:
    workers: 3
    concurrency: 3
    redis_cluster: primary
    
  eu-west-1: 
    workers: 2
    concurrency: 3
    redis_cluster: replica
    
  asia-southeast-1:
    workers: 2
    concurrency: 3
    redis_cluster: replica

# Global load balancing
task_routing:
  - route: audio_transcription
    regions: [us-east-1, eu-west-1, asia-southeast-1]
    strategy: lowest_latency
```

### 🎯 Quick Reference

#### **Scaling Decision Flowchart**
```
Queue Length > 10 → Scale Up Workers
Queue Length < 2 → Scale Down Workers
Task Wait Time > 5min → Increase Concurrency
CPU Usage > 80% → Scale Horizontally
Memory Usage > 85% → Reduce Concurrency or Scale Horizontally
Failure Rate > 5% → Reduce Concurrency & Investigate
```

#### **Recommended Starting Points**
- **Development**: 1 worker, concurrency=2
- **Staging**: 1 worker, concurrency=4  
- **Production (Small)**: 1 worker, concurrency=4
- **Production (Medium)**: 3 workers, concurrency=3
- **Production (Large)**: 5+ workers, concurrency=2-3

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