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

# For more verbose logging
celery -A coaching_assistant.core.celery_app worker \
  --loglevel=debug \
  --concurrency=1 \
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

For development, use these Celery settings:

```bash
# Low concurrency for debugging
celery worker --concurrency=1 --loglevel=debug

# Higher concurrency for testing
celery worker --concurrency=4 --loglevel=info

# Enable task events for monitoring
celery worker --loglevel=info -E
```

## Production Considerations

In production:
- Use Redis Cluster or managed Redis service
- Run multiple Celery workers across different machines
- Use proper process managers (systemd, supervisor)
- Enable task result persistence
- Set up monitoring with Flower or Celery monitoring tools

---

For more details, see:
- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Google STT API Documentation](https://cloud.google.com/speech-to-text/docs)


###

🔧 Makefile 新增功能

  新增 Celery 指令:
  - make run-celery - 啟動 Celery worker (一般模式)
  - make run-celery-debug - 啟動 Celery worker (除錯模式)

  新增 Docker 建置指令:
  - make docker-worker - 建置一般用途 Worker Docker image
  - make docker-worker-cloudrun - 建置 GCP Cloud Run 專用 Worker image

  📦 生產環境部署策略

  Render.com

  方法 1: 分離服務 (推薦)
  - API Service: Web Service
  - Worker Service: Background Worker
  - 使用 apps/worker/Dockerfile

  方法 2: 合併服務
  - 單一服務同時執行 API + Worker
  - 適合小規模應用

  GCP Cloud Run

  需要 HTTP 端點用於健康檢查
  - 使用 apps/worker/Dockerfile.cloudrun
  - 包含 health_server.py 提供健康檢查端點
  - 支援 Cloud Run 的要求

  🏗️ 建議架構

  生產環境推薦分離部署:
  Web Service (API) ←→ Managed Redis ←→ Worker Service (Celery)

  優點:
  - 獨立擴展
  - 故障隔離
  - 資源最佳化
  - 部署靈活性

  快速啟動:
  # 開發環境
  make run-celery        # 啟動 Celery worker
  make run-api          # 啟動 API server

  # Docker 建置
  make docker-worker    # Render.com 用
  make docker-worker-cloudrun  # GCP Cloud Run 用

  所有部署細節和配置範例都已記錄在 docs/deployment/production-celery-deployment.md 中！