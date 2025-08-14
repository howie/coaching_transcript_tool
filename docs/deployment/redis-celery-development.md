# Redis & Celery Development Environment Setup

This document explains how to set up Redis in Docker and run Celery workers for the Coaching Transcript Tool development environment.

## Overview

In the development environment:
- **Redis** runs in a Docker container as the message broker
- **Celery workers** run on the host machine for easier debugging
- **API server** connects to Redis for task queuing
- **Google STT** processes audio files asynchronously via Celery

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Server    │    │  Redis (Docker)  │    │  Celery Worker  │
│  (Host: 8000)   │◄──►│  (Port: 6379)    │◄──►│  (Host Process) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Task Queue     │    │   Google STT    │
│   (Database)    │    │  (Redis Lists)   │    │   API Service   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

- Docker installed and running
- Python 3.11+ with project dependencies installed
- PostgreSQL database running (local or cloud)
- Google Cloud service account credentials

## Step 1: Start Redis with Docker

### Option A: Using Docker Compose (Recommended)

Update `docker-compose.yml` to include Redis:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass redis_pass_dev
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

Start Redis:
```bash
docker-compose up -d redis
```

### Option B: Using Docker directly

```bash
# Start Redis container
docker run -d \
  --name coaching-redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine \
  redis-server --requirepass redis_pass_dev

# Verify Redis is running
docker logs coaching-redis
```

### Verify Redis Connection

```bash
# Test Redis connection
redis-cli -h localhost -p 6379 -a redis_pass_dev ping
# Should return: PONG

# Or using Docker exec
docker exec coaching-redis redis-cli -a redis_pass_dev ping
```

## Step 2: Configure Environment Variables

Ensure these variables are set in your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://:redis_pass_dev@localhost:6379/0
CELERY_BROKER_URL=redis://:redis_pass_dev@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:redis_pass_dev@localhost:6379/0

# Database
DATABASE_URL=postgresql://coach_user:coach_pass_dev@localhost:5432/coaching_assistant_dev

# Google STT
GOOGLE_APPLICATION_CREDENTIALS_JSON=<base64_encoded_service_account_json>
GOOGLE_PROJECT_ID=your-project-id
```

## Step 3: Start Celery Worker

Open a new terminal and start the Celery worker:

```bash
# Navigate to project root
cd /path/to/coaching_transcript_tool

# Start Celery worker with development settings
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  --pool=threads

# For debugging (single task at a time)
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=debug \
  --concurrency=1 \
  --pool=threads

# For performance testing (multiple concurrent tasks)
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --pool=threads
```

Expected output:
```
 -------------- celery@hostname v5.3.x
---- **** -----
--- * ***  * --
-- * - **** -
- ** ----------
- ** ----------

[config]
.> app:         coaching_assistant.core.celery_app:0x...
.> transport:   redis://:**@localhost:6379/0
.> results:     redis://:**@localhost:6379/0
.> concurrency: 2 (threads)
.> task events: OFF (enable -E to monitor tasks in Flower)
.> queues:      celery (exchange=celery, routing_key=celery)

[tasks]
  . coaching_assistant.tasks.transcription_tasks.transcribe_audio
```

## Step 4: Start API Server

In another terminal, start the API server:

```bash
# Make sure dependencies are installed
make dev-setup

# Start API server
make run-api
```

## Step 5: Test the Setup

### Verify Celery Connection

```bash
# Run the Celery status check script
python3 apps/web/check_celery_status.py
```

Expected output:
```
📋 Registered Celery Tasks:
  - coaching_assistant.tasks.transcription_tasks.transcribe_audio

🔄 Active Tasks:
  Worker: celery@hostname
```

### Test Transcription Flow

```bash
# Run the transcription test script
python3 apps/web/test_transcription_flow.py
```

This script will:
1. Check Celery connection
2. Look for pending transcription sessions
3. Allow you to trigger a test transcription
4. Monitor task progress

## How Celery Interacts with Redis

### Task Queuing Process

1. **API receives audio upload**:
   ```python
   # API creates session and queues transcription task
   task = transcribe_audio.delay(session_id, gcs_path, language)
   session.transcription_job_id = task.id
   ```

2. **Redis stores task data**:
   ```
   # Redis key structure
   celery-task-meta-<task_id>  # Task metadata and results
   celery                      # Default queue name (Redis list)
   ```

3. **Celery worker processes tasks**:
   ```python
   # Worker picks up task from Redis queue
   @celery_app.task
   def transcribe_audio(session_id, gcs_path, language):
       # Process audio with Google STT
       # Update database with progress
       # Return results
   ```

### Redis Data Structure

Redis uses these data structures for Celery:

```bash
# List tasks in queue (Redis list)
redis-cli -a redis_pass_dev LLEN celery

# Check task metadata (Redis hash)
redis-cli -a redis_pass_dev HGETALL celery-task-meta-<task_id>

# Monitor real-time commands
redis-cli -a redis_pass_dev MONITOR
```

### Task States

Celery tasks go through these states:
- `PENDING`: Task waiting in queue
- `STARTED`: Worker picked up task
- `PROGRESS`: Custom state for progress updates
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed with error
- `RETRY`: Task failed but will be retried

## Monitoring & Debugging

### View Celery Logs

```bash
# Celery worker logs show task execution
# Look for these log messages:
# - "Task transcribe_audio[task_id] received"
# - "Starting transcription for session <id>"
# - "Google STT client initialized"
# - "Transcription completed for session <id>"
```

### Monitor Redis Activity

```bash
# Real-time Redis command monitoring
redis-cli -a redis_pass_dev MONITOR

# Check Redis memory usage
redis-cli -a redis_pass_dev INFO memory

# List all keys
redis-cli -a redis_pass_dev KEYS '*'
```

### Database Status Tracking

```sql
-- Check recent sessions and their processing status
SELECT 
    s.id,
    s.status,
    s.transcription_job_id,
    ps.progress,
    ps.message
FROM session s
LEFT JOIN processing_status ps ON s.id = ps.session_id
WHERE s.created_at > NOW() - INTERVAL '1 hour'
ORDER BY s.created_at DESC;
```

## Troubleshooting

### Common Issues

**1. "No Celery workers found"**
```bash
# Check if worker is running
ps aux | grep celery

# Restart worker
celery -A coaching_assistant.core.celery_app worker --loglevel=info
```

**2. "Redis connection refused"**
```bash
# Check if Redis container is running
docker ps | grep redis

# Start Redis container
docker-compose up -d redis
```

**3. "Google STT authentication failed"**
```bash
# Verify credentials are Base64 encoded
echo $GOOGLE_APPLICATION_CREDENTIALS_JSON | base64 -d | jq .

# Test STT service directly
python3 -c "
from coaching_assistant.services.google_stt import GoogleSTTService
stt = GoogleSTTService()
print('STT initialized successfully')
"
```

### Performance Tuning

### 🎯 Development Concurrency Guidelines

Choose concurrency based on your development needs:

#### **Development Scenarios**

| Scenario | Concurrency | Purpose | Command |
|----------|-------------|---------|---------|
| **Debugging** | `--concurrency=1` | Single task debugging, step-through | `make run-celery-debug` |
| **Development** | `--concurrency=2` | Normal development, parallel testing | `make run-celery` |
| **Performance Testing** | `--concurrency=4` | Load testing, production simulation | Custom command |
| **Integration Testing** | `--concurrency=3` | Multi-task integration tests | Custom command |

#### **Recommended Development Commands**

```bash
# 🐛 Debugging mode (sequential processing)
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=debug \
  --concurrency=1 \
  --pool=threads

# 🔧 Development mode (balanced)  
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  --pool=threads

# 🚀 Performance testing mode
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --pool=threads

# 📊 Monitoring enabled
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  -E  # Enable task events for Flower monitoring
```

#### **Makefile Commands Updated**

The project Makefile now supports these configurations:

```bash
# Default development (concurrency=2)
make run-celery

# Debug mode (concurrency=2, verbose logging) 
make run-celery-debug

# Performance testing (custom)
CELERY_CONCURRENCY=4 make run-celery
```

## 🚀 Development to Production Transition

### **Environment Progression**

| Environment | Workers | Concurrency | Total Capacity | Use Case |
|-------------|---------|-------------|----------------|----------|
| **Local Dev** | 1 | 2 | 2 tasks | Feature development |
| **Integration** | 1 | 3 | 3 tasks | Integration testing |
| **Staging** | 1-2 | 4 | 4-8 tasks | Production simulation |
| **Production** | 2+ | 2-4 | 4-12+ tasks | Live workload |

### **Performance Testing in Development**

Before deploying to production, test scalability locally:

```bash
# Step 1: Test single worker performance
celery -A coaching_assistant.core.celery_app worker \
  --concurrency=1 --loglevel=info

# Step 2: Test parallel processing
celery -A coaching_assistant.core.celery_app worker \
  --concurrency=4 --loglevel=info

# Step 3: Test multiple workers (run in separate terminals)
# Terminal 1:
celery -A coaching_assistant.core.celery_app worker \
  --concurrency=2 --loglevel=info --hostname=worker1@%h

# Terminal 2:
celery -A coaching_assistant.core.celery_app worker \
  --concurrency=2 --loglevel=info --hostname=worker2@%h
```

### **Load Testing Framework**

Create a load test script:

```python
# scripts/load_test_celery.py
import time
import concurrent.futures
from coaching_assistant.tasks.transcription_tasks import transcribe_audio

def simulate_concurrent_uploads(num_tasks=10):
    """Simulate multiple concurrent transcription requests"""
    print(f"🚀 Starting load test with {num_tasks} concurrent tasks...")
    
    # Mock session data
    test_sessions = [
        {
            'session_id': f'test-session-{i}',
            'gcs_uri': 'gs://test-bucket/sample-audio.wav',
            'language': 'en-US',
            'original_filename': f'test-{i}.wav'
        }
        for i in range(num_tasks)
    ]
    
    start_time = time.time()
    
    # Submit all tasks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(
                transcribe_audio.delay,
                session['session_id'],
                session['gcs_uri'],
                session['language'],
                original_filename=session['original_filename']
            )
            for session in test_sessions
        ]
        
        # Wait for all tasks to complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                task = future.result()
                results.append(task.get(timeout=300))  # 5 minute timeout
            except Exception as e:
                print(f"❌ Task failed: {e}")
                results.append(None)
    
    end_time = time.time()
    
    # Report results
    successful_tasks = len([r for r in results if r is not None])
    total_time = end_time - start_time
    
    print(f"📊 Load Test Results:")
    print(f"   Total tasks: {num_tasks}")
    print(f"   Successful: {successful_tasks}")
    print(f"   Failed: {num_tasks - successful_tasks}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Average time per task: {total_time/num_tasks:.2f} seconds")
    print(f"   Tasks per minute: {(num_tasks/total_time)*60:.1f}")

if __name__ == "__main__":
    simulate_concurrent_uploads(5)  # Start with 5 concurrent tasks
```

### **Monitoring Setup for Development**

Install and run Flower for task monitoring:

```bash
# Install Flower
pip install flower

# Start Flower monitoring
celery -A coaching_assistant.core.celery_app flower \
  --port=5555 \
  --broker=redis://:redis_pass_dev@localhost:6379/0

# Access web interface at: http://localhost:5555
```

### **Production Scaling Considerations**

When transitioning to production, consider:

#### **Resource Planning**
```python
# Calculate resource requirements
TASK_DURATION_MINUTES = 3.5  # Average transcription time
PEAK_CONCURRENT_USERS = 100
SAFETY_MARGIN = 1.5

required_capacity = (PEAK_CONCURRENT_USERS * SAFETY_MARGIN)
recommended_workers = max(2, required_capacity // 4)  # 4 tasks per worker
recommended_concurrency = min(4, required_capacity // recommended_workers)

print(f"Recommended configuration:")
print(f"  Workers: {recommended_workers}")
print(f"  Concurrency: {recommended_concurrency}")
print(f"  Total capacity: {recommended_workers * recommended_concurrency} tasks")
```

#### **Deployment Migration Path**
1. **Development**: `1 worker × 2 concurrency = 2 capacity`
2. **Staging**: `1 worker × 4 concurrency = 4 capacity`
3. **Production (Phase 1)**: `2 workers × 3 concurrency = 6 capacity`
4. **Production (Scale Up)**: `3 workers × 3 concurrency = 9 capacity`
5. **Enterprise**: `5+ workers × 2-3 concurrency = 10-15+ capacity`

For detailed production deployment strategies, see:
📚 **[Production Celery Deployment Guide](./production-celery-deployment.md)**

---

For more details, see:
- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Google STT API Documentation](https://cloud.google.com/speech-to-text/docs)


## 🔧 Updated Makefile Commands & Production Deployment

### **Makefile Commands**

The project now includes optimized Celery commands:

```bash
# Development Commands
make run-celery         # Start Celery worker (concurrency=2, INFO level)
make run-celery-debug   # Start Celery worker (concurrency=2, DEBUG level)  
make run-api           # Start FastAPI server

# Docker Build Commands  
make docker-worker           # Build general Worker Docker image
make docker-worker-cloudrun  # Build GCP Cloud Run specific Worker image

# Environment-specific overrides
CELERY_CONCURRENCY=4 make run-celery  # Override concurrency
```

### **📦 Production Deployment Strategies**

#### **Render.com Deployment Options**

**Method 1: Separate Services (Recommended)**
- **API Service**: Web Service type
- **Worker Service**: Background Worker type
- **Architecture**: `API ←→ Managed Redis ←→ Worker`
- **Dockerfile**: `apps/worker/Dockerfile`
- **Scaling**: Independent auto-scaling

**Method 2: Combined Service**
- **Single Service**: API + Worker in one container
- **Use Case**: Small to medium scale applications
- **Resource**: Standard+ instance recommended

#### **GCP Cloud Run Deployment**

**Requirements**: HTTP endpoint for health checks
- **Dockerfile**: `apps/worker/Dockerfile.cloudrun`
- **Health Server**: `apps/worker/health_server.py`
- **Auto-scaling**: Built-in based on HTTP requests
- **Concurrency**: Per-instance concurrent request limits

### **🏗️ Recommended Production Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Service   │    │ Managed Redis    │    │ Worker Service  │
│   (Auto-scale   │◄──►│ (HA + Backup)    │◄──►│ (Auto-scale     │
│    1-10 pods)   │    │                  │    │  2-8 workers)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Benefits:**
- 🚀 **Independent Scaling**: Scale API and workers separately
- 🛡️ **Fault Isolation**: Worker failures don't affect API service
- 💰 **Resource Optimization**: Different CPU/memory profiles
- 🔄 **Deployment Flexibility**: Deploy components independently

### **🚀 Quick Start Guide**

```bash
# Local Development Setup
make dev-setup          # Install dependencies
docker-compose up -d redis  # Start Redis

# Terminal 1: Start API
make run-api

# Terminal 2: Start Celery Worker  
make run-celery-debug   # For debugging
# OR
make run-celery         # For development

# Test the setup
python3 apps/web/test_transcription_flow.py
```

### **📈 Scaling Path: Development → Production**

| Stage | Setup | Command | Capacity |
|-------|--------|---------|----------|
| **Local Dev** | Single worker | `make run-celery-debug` | 2 concurrent |
| **Integration** | Load testing | `CELERY_CONCURRENCY=4 make run-celery` | 4 concurrent |
| **Staging** | Production simulation | Deploy 1 worker, concurrency=4 | 4 concurrent |
| **Production** | Multi-worker setup | Deploy 3 workers, concurrency=3 | 9 concurrent |
| **Scale Up** | High availability | Deploy 5+ workers, concurrency=2-3 | 10-15+ concurrent |

---

### **📚 Additional Resources**

For comprehensive production deployment details including:
- Multi-cloud configurations (AWS, GCP, Azure)
- Auto-scaling policies and monitoring
- Cost optimization strategies
- Security best practices

See: **[Production Celery Deployment Guide](./production-celery-deployment.md)**