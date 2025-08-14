# US003: SSE Real-time Updates

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P1 (High)
- **Story Points**: 8
- **Sprint**: Real-time Sprint 2
- **Feature Flag**: `enable_sse_notifications`
- **Dependencies**: US001 (Backend Foundation), US002 (Frontend Bell)
- **Assignee**: Full-stack Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to receive notifications instantly when events occur  
**So that** I don't have to wait or refresh the page to see updates

### Business Value
- **Real-time Experience**: Instant feedback creates professional, modern feel
- **User Engagement**: Users stay active instead of leaving while waiting
- **Reduced Support**: Eliminates "why didn't I get notified?" support tickets
- **Competitive Advantage**: Real-time features differentiate from competitors

## ✅ Acceptance Criteria

### AC1: Server-Sent Events (SSE) Endpoint
**Given** I am an authenticated user  
**When** I connect to the SSE notification endpoint  
**Then** I receive a persistent connection that streams notifications in real-time

**Technical Requirements:**
- Endpoint: `GET /api/notifications/stream`
- Uses `text/event-stream` content type
- Requires valid JWT token for authentication
- Supports concurrent connections (1000+ users)
- Automatically sends heartbeat every 30 seconds

### AC2: Real-time Notification Delivery
**Given** a new notification is created for my user account  
**When** the notification is saved to the database  
**Then** I receive the notification via SSE within 1 second

**Event Format:**
```
event: notification
data: {"id": "123", "type": "success", "title": "Transcription Complete", "message": "Your audio is ready", "created_at": "2025-01-01T10:00:00Z"}

event: heartbeat
data: {"timestamp": "2025-01-01T10:00:30Z", "connections": 1}
```

### AC3: Connection Management
**Given** my SSE connection is lost (network issue, server restart)  
**When** the connection drops  
**Then** the frontend automatically attempts to reconnect with exponential backoff

**Connection Requirements:**
- Auto-reconnect on disconnect
- Exponential backoff: 1s, 2s, 4s, 8s, max 30s
- Stop reconnection attempts after 10 failures
- Resume normal polling as fallback when SSE fails

### AC4: Frontend SSE Integration
**Given** I have the dashboard open  
**When** I receive an SSE notification  
**Then** the notification bell badge updates instantly without page refresh

**Integration Requirements:**
- EventSource API used for SSE connection
- Notifications added to existing notification state
- Bell badge count updates immediately
- Toast notification shows for important events
- Works alongside existing polling mechanism

### AC5: Performance & Scalability
**Given** the system has 1000+ concurrent SSE connections  
**When** notifications are broadcast  
**Then** all users receive notifications within 2 seconds with <10MB memory per connection

**Performance Targets:**
- Connection establishment: <500ms
- Notification delivery: <1s from creation to receipt
- Memory per connection: <10MB
- CPU overhead: <1% per 100 connections

## 🧪 TDD Test Implementation

### MANDATORY: Follow Red-Green-Refactor Cycle
All code must be written test-first using strict TDD methodology.

### Backend SSE Tests (Required: 6 tests)

#### Test Sequence (MUST FOLLOW THIS ORDER)

```python
# Test 1: SSE Endpoint Creation (Write First)
def test_sse_endpoint_should_establish_connection():
    """RED: SSE endpoint doesn't exist yet"""
    response = client.get(
        "/api/notifications/stream",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["connection"] == "keep-alive"

# Test 2: Authentication Required (Write Second)
def test_sse_endpoint_should_require_authentication():
    """RED: Authentication not implemented"""
    response = client.get("/api/notifications/stream")
    assert response.status_code == 401
    
    # Invalid token
    response = client.get(
        "/api/notifications/stream",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

# Test 3: Heartbeat Mechanism (Write Third)
@pytest.mark.asyncio
async def test_sse_should_send_heartbeat_every_30_seconds():
    """RED: Heartbeat not implemented"""
    async with AsyncClient(app=app) as client:
        async with client.stream(
            "GET",
            "/api/notifications/stream", 
            headers={"Authorization": f"Bearer {valid_token}"}
        ) as response:
            
            events = []
            async for line in response.aiter_lines():
                if line.startswith("event: heartbeat"):
                    events.append(line)
                    if len(events) >= 2:
                        break
            
            # Should receive at least 2 heartbeats in 65 seconds
            assert len(events) >= 2

# Test 4: Notification Broadcasting (Write Fourth)  
@pytest.mark.asyncio
async def test_sse_should_broadcast_new_notifications():
    """RED: Notification broadcasting not implemented"""
    user_id = uuid4()
    
    # Start SSE connection
    async with AsyncClient(app=app) as client:
        async with client.stream(
            "GET",
            "/api/notifications/stream",
            headers={"Authorization": f"Bearer {create_token(user_id)}"}
        ) as response:
            
            # Create notification in another task
            notification = await create_notification(
                user_id=user_id,
                title="Test Notification",
                message="Test message", 
                type=NotificationType.INFO
            )
            
            # Should receive notification via SSE
            received_event = None
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])  # Remove "data:" prefix
                    if data.get("id") == str(notification.id):
                        received_event = data
                        break
            
            assert received_event is not None
            assert received_event["title"] == "Test Notification"
            assert received_event["type"] == "info"

# Test 5: User Isolation (Write Fifth)
@pytest.mark.asyncio 
async def test_sse_should_only_send_user_specific_notifications():
    """RED: User filtering not implemented"""
    user1_id = uuid4()
    user2_id = uuid4()
    
    # User1 connects to SSE
    async with AsyncClient(app=app) as client:
        async with client.stream(
            "GET",
            "/api/notifications/stream",
            headers={"Authorization": f"Bearer {create_token(user1_id)}"}
        ) as response:
            
            # Create notifications for both users
            await create_notification(user1_id, "User1 Notification", "Message", NotificationType.INFO)
            await create_notification(user2_id, "User2 Notification", "Message", NotificationType.INFO)
            
            # User1 should only receive their notification
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data:") and "Notification" in line:
                    data = json.loads(line[5:])
                    events.append(data["title"])
                    if len(events) >= 1:
                        break
            
            assert len(events) == 1
            assert events[0] == "User1 Notification"

# Test 6: Connection Cleanup (Write Sixth)
@pytest.mark.asyncio
async def test_sse_should_handle_client_disconnect():
    """RED: Connection cleanup not implemented"""
    user_id = uuid4()
    
    # Track connection count
    initial_connections = get_active_connection_count()
    
    # Create and immediately close connection
    async with AsyncClient(app=app) as client:
        async with client.stream(
            "GET", 
            "/api/notifications/stream",
            headers={"Authorization": f"Bearer {create_token(user_id)}"}
        ) as response:
            # Connection established
            active_connections = get_active_connection_count()
            assert active_connections == initial_connections + 1
    
    # Connection should be cleaned up
    await asyncio.sleep(0.1)  # Allow cleanup
    final_connections = get_active_connection_count()
    assert final_connections == initial_connections
```

### Frontend SSE Tests (Required: 5 tests)

```typescript
// Test 1: SSE Connection Establishment (Write First)
describe('SSE Notification Integration', () => {
  beforeEach(() => {
    // Mock EventSource
    global.EventSource = jest.fn().mockImplementation((url) => ({
      url,
      readyState: EventSource.CONNECTING,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      close: jest.fn(),
      onerror: null,
      onmessage: null,
      onopen: null
    }));
  });

  it('should establish SSE connection with proper headers', () => {
    // RED: SSE connection logic doesn't exist
    const { result } = renderHook(() => useNotificationSSE());
    
    expect(EventSource).toHaveBeenCalledWith(
      '/api/notifications/stream',
      {
        headers: {
          'Authorization': `Bearer ${mockToken}`
        }
      }
    );
  });

  // Test 2: Message Handling (Write Second)
  it('should handle incoming notification messages', () => {
    // RED: Message handling not implemented
    const mockOnNotification = jest.fn();
    const mockEventSource = new EventSource('/test');
    
    const { result } = renderHook(() => 
      useNotificationSSE({ onNotification: mockOnNotification })
    );
    
    // Simulate incoming notification
    const notificationEvent = new MessageEvent('notification', {
      data: JSON.stringify({
        id: '123',
        title: 'Test Notification',
        type: 'success'
      })
    });
    
    mockEventSource.dispatchEvent(notificationEvent);
    
    expect(mockOnNotification).toHaveBeenCalledWith({
      id: '123',
      title: 'Test Notification', 
      type: 'success'
    });
  });

  // Test 3: Reconnection Logic (Write Third)
  it('should reconnect with exponential backoff on disconnect', async () => {
    // RED: Reconnection logic not implemented
    jest.useFakeTimers();
    const mockEventSource = new EventSource('/test');
    
    const { result } = renderHook(() => useNotificationSSE());
    
    // Simulate connection error
    const errorEvent = new Event('error');
    mockEventSource.dispatchEvent(errorEvent);
    
    // Should attempt reconnect after 1 second
    jest.advanceTimersByTime(1000);
    expect(EventSource).toHaveBeenCalledTimes(2);
    
    // Simulate another error - should wait 2 seconds
    const newMockEventSource = (EventSource as jest.Mock).mock.results[1].value;
    newMockEventSource.dispatchEvent(errorEvent);
    
    jest.advanceTimersByTime(2000);
    expect(EventSource).toHaveBeenCalledTimes(3);
    
    jest.useRealTimers();
  });

  // Test 4: State Integration (Write Fourth)
  it('should update notification state when SSE message received', () => {
    // RED: State integration not implemented
    const { result } = renderHook(() => useNotificationContext());
    
    act(() => {
      // Simulate SSE notification received
      result.current.handleSSENotification({
        id: '123',
        title: 'New Notification',
        status: 'unread',
        type: 'success'
      });
    });
    
    expect(result.current.notifications).toContainEqual(
      expect.objectContaining({
        id: '123',
        title: 'New Notification'
      })
    );
    expect(result.current.unreadCount).toBe(1);
  });

  // Test 5: Cleanup on Unmount (Write Fifth)
  it('should close SSE connection on component unmount', () => {
    // RED: Cleanup not implemented
    const mockEventSource = {
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };
    (EventSource as jest.Mock).mockReturnValue(mockEventSource);
    
    const { unmount } = renderHook(() => useNotificationSSE());
    
    unmount();
    
    expect(mockEventSource.close).toHaveBeenCalled();
  });
});
```

## 🛠️ Technical Implementation

### Backend SSE Implementation

```python
# api/notifications.py - SSE endpoint
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import AsyncGenerator

router = APIRouter()

# Connection manager to track active SSE connections
class SSEConnectionManager:
    def __init__(self):
        self.connections: Dict[str, List[asyncio.Queue]] = {}
    
    async def connect(self, user_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(queue)
        return queue
    
    async def disconnect(self, user_id: str, queue: asyncio.Queue):
        if user_id in self.connections:
            self.connections[user_id].remove(queue)
            if not self.connections[user_id]:
                del self.connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, event: dict):
        if user_id in self.connections:
            for queue in self.connections[user_id][:]:  # Copy to avoid modification during iteration
                try:
                    await queue.put(event)
                except Exception:
                    # Connection likely closed, remove it
                    self.connections[user_id].remove(queue)

sse_manager = SSEConnectionManager()

@router.get("/notifications/stream")
async def notification_stream(
    request: Request,
    current_user: User = Depends(get_current_user_dependency)
) -> StreamingResponse:
    """Server-Sent Events endpoint for real-time notifications"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await sse_manager.connect(str(current_user.id))
        
        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'user_id': str(current_user.id), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Heartbeat task
            heartbeat_task = asyncio.create_task(send_heartbeat(queue))
            
            while True:
                try:
                    # Wait for events with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    if event['type'] == 'heartbeat':
                        yield f"event: heartbeat\ndata: {json.dumps(event)}\n\n"
                    else:
                        yield f"event: notification\ndata: {json.dumps(event)}\n\n"
                        
                except asyncio.TimeoutError:
                    # Send heartbeat if no events in 30 seconds
                    await queue.put({
                        'type': 'heartbeat', 
                        'timestamp': datetime.utcnow().isoformat(),
                        'connections': len(sse_manager.connections.get(str(current_user.id), []))
                    })
                    
        except asyncio.CancelledError:
            pass
        finally:
            heartbeat_task.cancel()
            await sse_manager.disconnect(str(current_user.id), queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

async def send_heartbeat(queue: asyncio.Queue):
    """Send heartbeat every 30 seconds to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)
            await queue.put({
                'type': 'heartbeat',
                'timestamp': datetime.utcnow().isoformat()
            })
    except asyncio.CancelledError:
        pass

# Notification creation hook
async def publish_notification_event(notification: Notification):
    """Publish notification via SSE when created"""
    event_data = {
        'id': str(notification.id),
        'title': notification.title,
        'message': notification.message,
        'type': notification.type.value,
        'status': notification.status.value,
        'metadata': notification.metadata,
        'created_at': notification.created_at.isoformat(),
        'related_session_id': str(notification.related_session_id) if notification.related_session_id else None
    }
    
    await sse_manager.broadcast_to_user(str(notification.user_id), event_data)
```

### Frontend SSE Integration

```typescript
// hooks/useNotificationSSE.ts
import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useNotificationContext } from '@/contexts/notification-context';

interface SSEHookOptions {
  enabled?: boolean;
  maxReconnectAttempts?: number;
  onError?: (error: Event) => void;
}

export const useNotificationSSE = (options: SSEHookOptions = {}) => {
  const { token } = useAuth();
  const { addNotification, updateUnreadCount } = useNotificationContext();
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  
  const {
    enabled = true,
    maxReconnectAttempts = 10,
    onError
  } = options;

  const connect = useCallback(() => {
    if (!token || !enabled || eventSourceRef.current?.readyState === EventSource.OPEN) {
      return;
    }

    try {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create new EventSource with auth headers
      const eventSource = new EventSource('/api/notifications/stream', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connection established');
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts
      };

      eventSource.addEventListener('notification', (event) => {
        try {
          const notification = JSON.parse(event.data);
          addNotification(notification);
          
          // Show toast for important notifications
          if (notification.type === 'success' || notification.type === 'error') {
            toast(notification.title, { 
              type: notification.type,
              description: notification.message
            });
          }
        } catch (error) {
          console.error('Error parsing SSE notification:', error);
        }
      });

      eventSource.addEventListener('heartbeat', (event) => {
        console.debug('SSE heartbeat received:', event.data);
      });

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        onError?.(error);
        
        if (eventSource.readyState === EventSource.CLOSED) {
          attemptReconnect();
        }
      };

    } catch (error) {
      console.error('Failed to create SSE connection:', error);
      attemptReconnect();
    }
  }, [token, enabled, addNotification, onError]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.error('Max SSE reconnection attempts reached');
      return;
    }

    reconnectAttemptsRef.current += 1;
    const delay = Math.min(Math.pow(2, reconnectAttemptsRef.current - 1) * 1000, 30000);
    
    console.log(`Attempting SSE reconnect ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${delay}ms`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Connect on mount and token change
  useEffect(() => {
    if (enabled && token) {
      connect();
    }
    
    return disconnect;
  }, [connect, disconnect, enabled, token]);

  // Cleanup on unmount
  useEffect(() => {
    return disconnect;
  }, [disconnect]);

  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
    reconnectAttempts: reconnectAttemptsRef.current,
    connect,
    disconnect
  };
};
```

### Enhanced Notification Context

```typescript
// contexts/notification-context.tsx - Enhanced with SSE
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // SSE integration
  const { isConnected } = useNotificationSSE({
    enabled: true,
    onError: (error) => {
      console.error('SSE connection error, falling back to polling');
      // Fallback to more frequent polling when SSE fails
      startPolling(10000); // 10 seconds instead of 30
    }
  });
  
  const addNotification = useCallback((notification: Notification) => {
    setNotifications(prev => [notification, ...prev.slice(0, 19)]); // Keep only 20 most recent
    if (notification.status === 'unread') {
      setUnreadCount(prev => prev + 1);
    }
  }, []);
  
  const handleSSENotification = useCallback((notification: Notification) => {
    addNotification(notification);
    
    // Update badge count immediately
    if (notification.status === 'unread') {
      setUnreadCount(prev => prev + 1);
    }
  }, [addNotification]);
  
  // Fallback polling (less frequent when SSE is working)
  useEffect(() => {
    const pollInterval = isConnected ? 60000 : 30000; // 1 min vs 30 sec
    
    const interval = setInterval(async () => {
      try {
        const { unread_count } = await apiClient.getUnreadCount();
        setUnreadCount(unread_count);
      } catch (error) {
        console.error('Failed to poll unread count:', error);
      }
    }, pollInterval);
    
    return () => clearInterval(interval);
  }, [isConnected]);
  
  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      addNotification: handleSSENotification,
      // ... other methods
    }}>
      {children}
    </NotificationContext.Provider>
  );
};
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Backend SSE tests**: 6/6 tests using TDD methodology
- [ ] **Frontend SSE tests**: 5/5 tests covering connection management
- [ ] **Integration tests**: End-to-end SSE flow tested
- [ ] **Load tests**: 1000+ concurrent connections tested
- [ ] **Reconnection tests**: Network failure scenarios covered

### Code Quality Requirements
- [ ] **TDD followed**: All SSE code written test-first
- [ ] **Error handling**: Comprehensive error recovery implemented
- [ ] **Memory management**: No connection leaks verified
- [ ] **Code review**: Backend and frontend changes reviewed
- [ ] **Performance monitoring**: SSE metrics and logging added

### Performance Requirements
- [ ] **Connection speed**: <500ms to establish SSE connection
- [ ] **Delivery time**: <1s from notification creation to frontend receipt
- [ ] **Memory usage**: <10MB per connection measured
- [ ] **Reconnection**: Exponential backoff working properly
- [ ] **Scalability**: 1000+ concurrent connections supported

### Security Requirements
- [ ] **Authentication**: JWT token required for SSE connection
- [ ] **Authorization**: Users only receive their own notifications
- [ ] **Rate limiting**: Connection attempts limited to prevent abuse
- [ ] **CORS**: Proper headers for cross-origin requests

### Integration Requirements
- [ ] **Frontend integration**: SSE works with existing notification bell
- [ ] **Fallback mechanism**: Polling continues when SSE fails
- [ ] **State synchronization**: SSE and polling don't conflict
- [ ] **Toast notifications**: Important events show user feedback

## 🚀 Implementation Notes

### SSE vs WebSocket Decision
- **SSE chosen** for simplicity and server-to-client only communication
- **HTTP/2 multiplexing** allows many SSE connections efficiently
- **Automatic reconnection** built into EventSource API
- **Simpler deployment** - no WebSocket proxy configuration needed

### Browser Compatibility
- **EventSource support**: All modern browsers (IE11+ via polyfill)
- **Mobile support**: Works on iOS Safari and Android Chrome
- **Polyfill available**: For older browser support if needed

### Error Handling Strategy
- **Connection failures**: Exponential backoff with max attempts
- **Authentication errors**: Redirect to login page
- **Server overload**: Circuit breaker pattern to prevent cascade failures
- **Graceful degradation**: Fall back to polling when SSE unavailable

### Monitoring & Observability
```python
# Metrics to track
sse_connections_total = Gauge('sse_connections_total', 'Active SSE connections')
sse_messages_sent_total = Counter('sse_messages_sent_total', ['event_type'])
sse_connection_duration = Histogram('sse_connection_duration_seconds')
sse_reconnection_attempts = Counter('sse_reconnection_attempts_total', ['reason'])
```

---

**🔄 Next Story**: [US004: Notification Persistence & History](US004-notification-persistence-history.md)  
**⬅️ Previous Story**: [US002: Notification Bell UI Component](US002-notification-bell-ui-component.md)  
**📋 Back to**: [Feature Overview](README.md)