# Technical Architecture: SSE Status Updates

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js App  │    │  FastAPI Server │    │  Celery Worker  │
│  (Cloudflare)   │    │   (Render.com)  │    │   (Background)  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ EventSource API │◄───┤ SSE Endpoint    │    │ Redis Publisher │
│ Status Display  │    │ Redis Subscriber│◄───┤ Status Updates  │
│ Progress Bar    │    │ Connection Mgmt │    │ Progress Events │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │  Redis Pub/Sub  │
                       │   Channel Bus   │
                       └─────────────────┘
```

## Component Details

### 1. Backend Infrastructure

#### SSE Endpoint Implementation
```python
# File: src/coaching_assistant/api/sessions.py

@router.get("/{session_id}/status/stream")
async def stream_transcription_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
):
    """Stream real-time transcription status updates via SSE."""
    
    # Validate session ownership
    session = get_user_session(session_id, current_user.id)
    
    # Create Redis subscriber
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    channel = f"transcription:status:{session_id}"
    pubsub.subscribe(channel)
    
    async def event_generator():
        try:
            # Send initial status
            current_status = get_current_status(session_id)
            yield f"data: {json.dumps(current_status)}\n\n"
            
            # Listen for updates
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    status_data = json.loads(message['data'])
                    yield f"data: {json.dumps(status_data)}\n\n"
                    
                    # Stop streaming when completed/failed
                    if status_data.get('status') in ['completed', 'failed']:
                        break
                        
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for session {session_id}")
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx buffering disable
        }
    )
```

#### Redis Pub/Sub Utilities
```python
# File: src/coaching_assistant/utils/redis_pubsub.py

class StatusPublisher:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def publish_status_update(self, session_id: str, status_data: dict):
        """Publish status update to Redis channel."""
        channel = f"transcription:status:{session_id}"
        message = json.dumps({
            "session_id": session_id,
            "status": status_data.get("status"),
            "progress": status_data.get("progress"),
            "message": status_data.get("message"),
            "timestamp": datetime.utcnow().isoformat(),
            **status_data
        })
        
        self.redis.publish(channel, message)
        logger.debug(f"Published status update to {channel}: {message}")

class StatusSubscriber:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def subscribe_to_session(self, session_id: str):
        """Subscribe to status updates for a specific session."""
        pubsub = self.redis.pubsub()
        channel = f"transcription:status:{session_id}"
        pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield json.loads(message['data'])
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
```

#### Celery Task Integration
```python
# File: src/coaching_assistant/tasks/transcription_tasks.py

from ..utils.redis_pubsub import StatusPublisher

@celery_app.task(bind=True)
def transcribe_audio(self, session_id: str, gcs_uri: str, language: str, original_filename: str):
    """Transcribe audio with real-time status updates."""
    
    # Initialize status publisher
    redis_client = get_redis_client()
    publisher = StatusPublisher(redis_client)
    
    try:
        # Update progress throughout transcription
        publisher.publish_status_update(session_id, {
            "status": "processing",
            "progress": 10,
            "message": "Starting audio processing..."
        })
        
        # ... transcription logic ...
        
        # Publish progress updates
        for progress in [25, 50, 75, 90]:
            publisher.publish_status_update(session_id, {
                "status": "processing", 
                "progress": progress,
                "message": get_progress_message(progress)
            })
            
        # Final completion
        publisher.publish_status_update(session_id, {
            "status": "completed",
            "progress": 100,
            "message": "Transcription completed successfully!"
        })
        
    except Exception as e:
        publisher.publish_status_update(session_id, {
            "status": "failed",
            "progress": 0,
            "message": f"Transcription failed: {str(e)}"
        })
        raise
```

### 2. Frontend Implementation

#### SSE Hook
```typescript
// File: apps/web/hooks/useTranscriptionStatusSSE.ts

export interface SSETranscriptionStatusOptions {
  enableSSE?: boolean;
  enablePollingFallback?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export const useTranscriptionStatusSSE = (
  sessionId: string | null,
  options: SSETranscriptionStatusOptions = {}
) => {
  const {
    enableSSE = true,
    enablePollingFallback = true,
    reconnectAttempts = 3,
    reconnectDelay = 1000
  } = options;

  const [status, setStatus] = useState<TranscriptionStatus | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const fallbackHook = useTranscriptionStatus(sessionId, { enablePolling: false });

  const connectSSE = useCallback(() => {
    if (!sessionId || !enableSSE) return;

    try {
      setConnectionStatus('connecting');
      
      const url = `${apiClient.baseUrl}/api/v1/sessions/${sessionId}/status/stream`;
      const eventSource = new EventSource(url, {
        withCredentials: true
      });

      eventSource.onopen = () => {
        setConnectionStatus('connected');
        setError(null);
        logger.info(`SSE connected for session ${sessionId}`);
      };

      eventSource.onmessage = (event) => {
        try {
          const statusData = JSON.parse(event.data);
          setStatus(statusData);
          
          // Close connection when transcription completes
          if (statusData.status === 'completed' || statusData.status === 'failed') {
            eventSource.close();
            setConnectionStatus('disconnected');
          }
        } catch (err) {
          logger.error('Error parsing SSE message:', err);
        }
      };

      eventSource.onerror = (error) => {
        logger.error('SSE connection error:', error);
        setConnectionStatus('error');
        setError('Connection lost. Retrying...');
        
        // Auto-reconnect logic
        if (reconnectAttempts > 0) {
          setTimeout(() => {
            connectSSE();
          }, reconnectDelay);
        } else if (enablePollingFallback) {
          // Fall back to polling
          fallbackHook.startPolling();
        }
      };

      eventSourceRef.current = eventSource;

    } catch (err) {
      logger.error('Failed to establish SSE connection:', err);
      setConnectionStatus('error');
      
      if (enablePollingFallback) {
        fallbackHook.startPolling();
      }
    }
  }, [sessionId, enableSSE, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setConnectionStatus('disconnected');
    }
  }, []);

  useEffect(() => {
    connectSSE();
    return disconnect;
  }, [connectSSE, disconnect]);

  return {
    status: status || fallbackHook.status,
    connectionStatus,
    error: error || fallbackHook.error,
    isConnected: connectionStatus === 'connected',
    reconnect: connectSSE,
    disconnect
  };
};
```

#### Component Integration
```typescript
// File: apps/web/app/dashboard/sessions/[id]/page.tsx

const SessionDetailPage = () => {
  const { id } = useParams();
  const sessionId = id as string;

  // Use SSE hook with polling fallback
  const {
    status,
    session,
    connectionStatus,
    isConnected,
    error
  } = useTranscriptionStatusSSE(sessionId, {
    enableSSE: true,
    enablePollingFallback: true,
    reconnectAttempts: 3
  });

  return (
    <div>
      {/* Connection status indicator */}
      <ConnectionStatusIndicator 
        status={connectionStatus}
        isConnected={isConnected}
      />
      
      {/* Real-time progress display */}
      <TranscriptionProgress
        status={status}
        session={session}
        realTime={isConnected}
      />
    </div>
  );
};
```

## Infrastructure Considerations

### Cloudflare Configuration
```javascript
// File: apps/web/cloudflare-worker.js
// Ensure SSE pass-through for /api/v1/sessions/*/status/stream

const handleRequest = async (request) => {
  const url = new URL(request.url);
  
  // Pass SSE requests directly to backend
  if (url.pathname.includes('/status/stream')) {
    return fetch(request, {
      headers: {
        ...request.headers,
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    });
  }
  
  // ... other routing logic
};
```

### Render.com Deployment
```yaml
# File: render.yaml additions
services:
  - type: web
    name: coaching-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.coaching_assistant.main:app --host 0.0.0.0 --port $PORT --workers 1"
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: coaching-redis
      - key: ENABLE_SSE
        value: "true"
      - key: SSE_CONNECTION_TIMEOUT
        value: "300"  # 5 minutes
```

## Performance Optimizations

### Connection Management
- **Connection pooling**: Limit concurrent SSE connections per user
- **Timeout handling**: Close idle connections after 5 minutes
- **Memory cleanup**: Proper subscription cleanup on disconnect

### Redis Optimization
- **Channel naming**: Structured channel names for efficient routing
- **Message expiry**: Set TTL on status messages to prevent memory leaks
- **Connection pooling**: Reuse Redis connections across requests

### Browser Optimization
- **Event batching**: Batch rapid status updates to prevent UI thrashing
- **Memory management**: Clean up event listeners on component unmount
- **Visibility API**: Pause/resume connections based on tab visibility