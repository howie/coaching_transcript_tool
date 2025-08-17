# US001: Real-time Notification Foundation

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P0 (Critical)
- **Story Points**: 8
- **Sprint**: Foundation Sprint 1
- **Feature Flag**: `enable_notifications` 
- **Dependencies**: Database migration system, User authentication
- **Assignee**: Backend Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to receive real-time notifications about my transcription status  
**So that** I know immediately when my audio processing is complete and can take action

### Business Value
- **User Impact**: Eliminate waiting and page refreshing for transcription status
- **Support Impact**: Reduce "where is my transcription?" tickets by 40%
- **Engagement**: Keep users active on platform instead of switching away
- **Revenue**: Faster feedback loop increases user satisfaction and retention

## ✅ Acceptance Criteria

### AC1: Notification Database Model
**Given** the system needs to store notifications  
**When** a notification is created  
**Then** it must be persisted with all required fields and proper indexing

**Technical Requirements:**
- User ID (foreign key to user table)
- Title (max 255 characters)
- Message (max 1000 characters)
- Type (success, error, info, warning)
- Status (unread, read, archived)
- Metadata (JSON for additional context)
- Created timestamp
- Read timestamp (nullable)
- Related session ID (nullable)

### AC2: Event Publishing on Transcription Complete
**Given** a transcription task completes successfully  
**When** the task finishes processing  
**Then** a success notification must be created and stored

**Given** a transcription task fails  
**When** the task encounters an error  
**Then** an error notification must be created with failure details

### AC3: Notification API Endpoints
**Given** an authenticated user requests their notifications  
**When** they call the notifications API  
**Then** they receive only their own notifications with proper pagination

**API Endpoints Required:**
- `GET /api/notifications` - List notifications (paginated)
- `GET /api/notifications/unread-count` - Get unread count
- `PATCH /api/notifications/{id}/read` - Mark single notification as read
- `PATCH /api/notifications/read-all` - Mark all notifications as read
- `DELETE /api/notifications/{id}` - Delete single notification

### AC4: Authentication & Authorization
**Given** an unauthenticated user tries to access notifications  
**When** they make a request to any notification endpoint  
**Then** they receive a 401 Unauthorized response

**Given** an authenticated user requests notifications  
**When** they make a valid request  
**Then** they only see their own notifications, never other users'

### AC5: Performance Requirements
**Given** the system has 1000+ concurrent users  
**When** notifications are created and queried  
**Then** response times must be <50ms for queries, <100ms for creation

## 🧪 TDD Test Implementation

### MANDATORY: Follow Red-Green-Refactor Cycle
All code for this story MUST be written using strict TDD methodology:

1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass  
3. **REFACTOR**: Improve structure while tests pass
4. **COMMIT**: Separate structural from behavioral changes

### Backend Unit Tests (Required: 8 tests)

#### Test Sequence (MUST FOLLOW THIS ORDER)
```python
# Test 1: Basic Model Creation (Write First)
def test_should_create_notification_model_with_required_fields():
    """RED: Will fail - model doesn't exist yet"""
    notification = Notification(
        user_id=uuid4(),
        title="Test Notification",
        message="Test message",
        type=NotificationType.INFO,
        status=NotificationStatus.UNREAD
    )
    assert notification.id is not None
    assert notification.created_at is not None
    assert notification.user_id is not None

# Test 2: Data Validation (Write Second, after Test 1 passes)
def test_should_validate_notification_title_max_length():
    """RED: Will fail - validation not implemented"""
    with pytest.raises(ValidationError):
        Notification(
            user_id=uuid4(),
            title="x" * 256,  # Exceeds 255 char limit
            message="Test",
            type=NotificationType.INFO
        )

# Test 3: Database Persistence (Write Third)  
def test_should_store_notification_in_database(db_session):
    """RED: Will fail - database table doesn't exist"""
    notification = Notification(
        user_id=uuid4(),
        title="Test",
        message="Test message", 
        type=NotificationType.INFO
    )
    db_session.add(notification)
    db_session.commit()
    
    saved = db_session.query(Notification).filter_by(id=notification.id).first()
    assert saved is not None
    assert saved.title == "Test"

# Test 4: Event Publishing (Write Fourth)
def test_should_publish_event_on_transcription_complete(mock_event_publisher):
    """RED: Will fail - event publishing not implemented"""
    session_id = uuid4()
    result = publish_transcription_complete_event(session_id, "success")
    
    mock_event_publisher.publish.assert_called_once()
    call_args = mock_event_publisher.publish.call_args[0]
    assert call_args[0] == "transcription.completed"
    assert call_args[1]["session_id"] == str(session_id)

# Test 5: Error Handling (Write Fifth)
def test_should_handle_notification_creation_failure(db_session, monkeypatch):
    """RED: Will fail - error handling not implemented"""
    def mock_db_error(*args, **kwargs):
        raise IntegrityError("Database error", None, None)
    
    monkeypatch.setattr(db_session, "add", mock_db_error)
    
    with pytest.raises(NotificationCreationError):
        create_notification(
            user_id=uuid4(),
            title="Test",
            message="Test",
            type=NotificationType.INFO
        )

# Test 6: User Filtering (Write Sixth)
def test_should_filter_notifications_by_user_id(db_session):
    """RED: Will fail - filtering logic not implemented"""
    user1 = uuid4()
    user2 = uuid4()
    
    # Create notifications for different users
    create_notification(user1, "Title 1", "Message 1", NotificationType.INFO)
    create_notification(user2, "Title 2", "Message 2", NotificationType.INFO) 
    create_notification(user1, "Title 3", "Message 3", NotificationType.ERROR)
    
    user1_notifications = get_user_notifications(user1)
    assert len(user1_notifications) == 2
    assert all(n.user_id == user1 for n in user1_notifications)

# Test 7: Indexing Performance (Write Seventh)
def test_should_query_notifications_efficiently(db_session):
    """RED: Will fail - indexes not created"""
    user_id = uuid4()
    
    # Create many notifications to test index performance
    for i in range(1000):
        create_notification(user_id, f"Title {i}", f"Message {i}", NotificationType.INFO)
    
    # Query should use index on user_id and be fast
    start_time = time.time()
    notifications = get_user_notifications(user_id, limit=10)
    query_time = time.time() - start_time
    
    assert len(notifications) == 10
    assert query_time < 0.05  # Less than 50ms

# Test 8: Duplicate Prevention (Write Eighth) 
def test_should_prevent_duplicate_notifications(db_session):
    """RED: Will fail - duplicate prevention not implemented"""
    session_id = uuid4()
    user_id = uuid4()
    
    # Try to create same notification twice
    create_transcription_notification(user_id, session_id, "completed")
    
    # Second call should not create duplicate
    result = create_transcription_notification(user_id, session_id, "completed")
    
    notifications = get_user_notifications(user_id)
    assert len(notifications) == 1  # Only one notification created
    assert result.is_duplicate == True
```

### API Integration Tests (Required: 4 tests)

```python
# API Test 1: Authentication (Write First)
def test_get_notifications_should_return_401_when_unauthenticated():
    """RED: Will fail - endpoint doesn't exist yet"""
    response = client.get("/api/notifications")
    assert response.status_code == 401
    assert "detail" in response.json()

# API Test 2: Basic Functionality (Write Second)
def test_get_notifications_should_return_empty_list_for_new_user(authenticated_client):
    """RED: Will fail - endpoint returns empty"""
    response = authenticated_client.get("/api/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["notifications"] == []
    assert data["total"] == 0

# API Test 3: Data Isolation (Write Third)
def test_get_notifications_should_filter_by_user_id(authenticated_client, other_user_client):
    """RED: Will fail - filtering not implemented"""
    # Create notifications for both users
    create_test_notification(authenticated_client.user_id)
    create_test_notification(other_user_client.user_id)
    
    # Each user should only see their own
    response = authenticated_client.get("/api/notifications")
    notifications = response.json()["notifications"]
    
    assert len(notifications) == 1
    assert notifications[0]["user_id"] == str(authenticated_client.user_id)

# API Test 4: Pagination (Write Fourth)  
def test_get_notifications_should_paginate_results(authenticated_client):
    """RED: Will fail - pagination not implemented"""
    # Create 25 notifications
    for i in range(25):
        create_test_notification(authenticated_client.user_id, title=f"Title {i}")
    
    # Test first page
    response = authenticated_client.get("/api/notifications?page=1&limit=10")
    data = response.json()
    
    assert len(data["notifications"]) == 10
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["pages"] == 3
```

## 🛠️ Technical Implementation

### Database Schema
```sql
-- Migration: Add notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type notification_type NOT NULL,
    status notification_status DEFAULT 'unread',
    metadata JSONB DEFAULT '{}',
    related_session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_notifications_session_id ON notifications(related_session_id);

-- Enums
CREATE TYPE notification_type AS ENUM ('success', 'error', 'info', 'warning');
CREATE TYPE notification_status AS ENUM ('unread', 'read', 'archived');
```

### API Endpoint Specifications

#### GET /api/notifications
```yaml
summary: List user notifications
parameters:
  - name: page
    type: integer
    default: 1
  - name: limit  
    type: integer
    default: 20
    maximum: 100
  - name: status
    type: string
    enum: [unread, read, all]
    default: all
  - name: type
    type: string
    enum: [success, error, info, warning]
responses:
  200:
    schema:
      type: object
      properties:
        notifications:
          type: array
          items:
            $ref: "#/components/schemas/Notification"
        total: 
          type: integer
        page:
          type: integer
        pages:
          type: integer
  401:
    description: Unauthorized
```

#### GET /api/notifications/unread-count
```yaml
summary: Get unread notification count
responses:
  200:
    schema:
      type: object
      properties:
        unread_count:
          type: integer
        last_notification_at:
          type: string
          format: date-time
```

### Event Publishing Integration
```python
# Integration with existing transcription tasks
def _publish_transcription_event(session_id: UUID, status: str, error_msg: str = None):
    """Publish notification event when transcription completes"""
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found for notification")
            return
            
        if status == "completed":
            create_notification(
                user_id=session.user_id,
                title="Transcription Complete",
                message=f"Your transcription '{session.title}' is ready to view",
                type=NotificationType.SUCCESS,
                related_session_id=session_id,
                metadata={
                    "duration_seconds": session.duration_seconds,
                    "segments_count": session.segments_count,
                    "action_url": f"/dashboard/sessions/{session_id}"
                }
            )
        elif status == "failed":
            create_notification(
                user_id=session.user_id, 
                title="Transcription Failed",
                message=f"Transcription for '{session.title}' encountered an error",
                type=NotificationType.ERROR,
                related_session_id=session_id,
                metadata={
                    "error_message": error_msg,
                    "action_url": f"/dashboard/sessions/{session_id}",
                    "retry_available": True
                }
            )
    except Exception as e:
        logger.error(f"Failed to create notification for session {session_id}: {e}")
        # Don't re-raise - notification failure shouldn't break transcription
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Unit tests written first (TDD)**: 8/8 tests implemented using Red-Green-Refactor
- [ ] **API tests written**: 4/4 integration tests passing
- [ ] **Test coverage >80%**: Backend code coverage measured and meets threshold
- [ ] **All tests passing**: No failing tests in CI/CD pipeline
- [ ] **Performance tests**: Database queries <50ms, API endpoints <100ms

### Code Quality Requirements  
- [ ] **TDD cycle followed**: Every line of production code preceded by failing test
- [ ] **Tidy First approach**: Structural changes separated from behavioral changes
- [ ] **Code review completed**: At least one team member approval
- [ ] **No linter warnings**: ESLint, Black, mypy all passing
- [ ] **Type annotations**: All Python functions properly typed

### Documentation Requirements
- [ ] **API documentation updated**: OpenAPI spec includes all new endpoints  
- [ ] **Database migration**: Alembic migration created and tested
- [ ] **Monitoring setup**: Logging and metrics for notification creation/delivery
- [ ] **Error handling documented**: All exception paths covered

### Security Requirements
- [ ] **Authentication enforced**: All endpoints require valid JWT token
- [ ] **Authorization implemented**: Users can only access their own notifications
- [ ] **Input validation**: SQL injection and XSS prevention implemented
- [ ] **Rate limiting**: Prevent notification spam and DoS attacks

### Performance Requirements
- [ ] **Database indexes**: Proper indexing on user_id, created_at, status
- [ ] **Query optimization**: N+1 queries avoided, eager loading used appropriately
- [ ] **Memory usage**: No memory leaks in long-running processes
- [ ] **Load testing**: System handles 100+ concurrent notification creations

## 🚀 Implementation Notes

### Migration Strategy
1. **Create database migration** with proper indexes
2. **Deploy schema changes** first (backward compatible)
3. **Deploy application code** with feature flag disabled
4. **Test in staging** with feature flag enabled  
5. **Gradual rollout** in production (10% → 50% → 100%)

### Monitoring & Observability
```python
# Metrics to track
notification_creation_total = Counter('notifications_created_total', ['type', 'status'])
notification_delivery_duration = Histogram('notification_delivery_seconds')
notification_errors_total = Counter('notification_errors_total', ['error_type'])

# Logging
logger.info("Notification created", extra={
    "user_id": str(user_id),
    "notification_id": str(notification.id), 
    "type": notification.type,
    "session_id": str(session_id) if session_id else None
})
```

### Error Handling Strategy
- **Graceful degradation**: Notification failures don't break main workflows
- **Retry mechanism**: Failed notifications retry with exponential backoff
- **Dead letter queue**: Persistently failing notifications logged for investigation
- **Circuit breaker**: Prevent cascade failures if notification service overloaded

### Security Considerations
- **SQL injection prevention**: Use parameterized queries only
- **XSS prevention**: Sanitize notification content before display
- **Rate limiting**: 100 notifications per user per hour maximum
- **Audit logging**: Track all notification access for security monitoring

---

**🔄 Next Story**: [US002: Notification Bell UI Component](US002-notification-bell-ui-component.md)  
**📋 Back to**: [Feature Overview](README.md)