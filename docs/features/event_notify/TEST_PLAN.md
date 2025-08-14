# Test Plan - Event Notification System

## 📋 Overview
This test plan enforces strict **Test-Driven Development (TDD)** methodology for the Event Notification System. Every line of production code must be preceded by a failing test that defines the expected behavior.

## 🎯 TDD Core Principles

### Red-Green-Refactor Cycle
```
🔴 RED    → Write the simplest failing test
🟢 GREEN  → Write minimal code to pass the test  
🔵 REFACTOR → Improve structure while keeping tests green
```

### Critical Rules
1. **NEVER** write production code without a failing test first
2. **ALWAYS** write the simplest test that could possibly fail
3. **ONLY** write enough production code to make the failing test pass
4. **SEPARATE** structural changes (refactoring) from behavioral changes
5. **COMMIT** frequently with clear structural/behavioral labels

### Tidy First Approach
```
✅ GOOD: Two separate commits
  - "refactor: extract notification service interface" 
  - "feat: add notification creation endpoint"

❌ BAD: Mixed commit
  - "feat: add notification with refactored service"
```

## 🧪 Test Categories & Requirements

### 1. Unit Tests (Required for DoD)
**Coverage Target**: >80% line coverage  
**Speed Target**: <1 second total execution time  
**Scope**: Individual functions and methods in isolation

#### Backend Unit Tests
```python
# Example naming convention
def test_should_create_notification_when_valid_data_provided():
    """Test names must describe behavior, not implementation"""
    
def test_should_raise_validation_error_when_title_exceeds_255_chars():
    """Include edge cases and error conditions"""
    
def test_should_return_unread_count_for_authenticated_user():
    """Focus on business logic and user outcomes"""
```

#### Frontend Unit Tests
```typescript
// Example naming convention
describe('NotificationBell', () => {
  it('should render bell icon with no badge when unread count is zero', () => {
    // Test implementation
  });
  
  it('should display unread count badge when notifications exist', () => {
    // Test implementation  
  });
  
  it('should call markAsRead when notification clicked', () => {
    // Test implementation
  });
});
```

### 2. API Tests (Required for DoD)
**Coverage Target**: 100% endpoint coverage  
**Response Time Target**: <200ms per request  
**Scope**: HTTP API behavior and error handling

```python
def test_get_notifications_should_return_401_when_unauthenticated():
    """Test authentication requirements"""
    
def test_get_notifications_should_return_paginated_results():
    """Test successful happy path"""
    
def test_get_notifications_should_filter_by_user_id():
    """Test authorization and data isolation"""
    
def test_post_notification_should_validate_required_fields():
    """Test input validation"""
    
def test_sse_endpoint_should_stream_real_time_notifications():
    """Test real-time functionality"""
```

### 3. Integration Tests
**Coverage Target**: All user workflows covered  
**Execution Time**: <10 seconds per test  
**Scope**: Multiple components working together

### 4. End-to-End Tests
**Coverage Target**: Critical user journeys  
**Browser Support**: Chrome, Firefox, Safari  
**Scope**: Full system behavior from user perspective

### 5. Performance Tests
**Load Target**: 1000 concurrent SSE connections  
**Response Time**: <100ms notification delivery  
**Memory Usage**: <10MB per connection

## 📊 Test Implementation Strategy

### Phase 1: Foundation Tests (US001-US002)

#### US001 Backend Test Sequence
**MUST FOLLOW THIS EXACT ORDER**

```python
# Test 1: Model Creation (Write First)
def test_should_create_notification_model_with_required_fields():
    """RED: This test will fail initially"""
    notification = Notification(
        user_id=uuid4(),
        title="Test",
        message="Test message", 
        type="info"
    )
    assert notification.id is not None
    assert notification.created_at is not None
    assert notification.status == "unread"

# Only after Test 1 passes, write Test 2
def test_should_store_notification_in_database():
    """GREEN: Implement minimal model to pass Test 1"""
    # Implementation after model exists
    
# Continue sequence: 3, 4, 5... one test at a time
```

#### US001 API Test Sequence
```python
# API Test 1: Authentication (Write First)  
def test_get_notifications_should_return_401_without_token():
    """RED: Will fail until auth middleware implemented"""
    response = client.get("/api/notifications")
    assert response.status_code == 401

# API Test 2: Basic Functionality (Write Second)
def test_get_notifications_should_return_empty_list_for_new_user():
    """GREEN: Implement basic endpoint after auth works"""
    response = authenticated_client.get("/api/notifications")
    assert response.status_code == 200
    assert response.json() == {"notifications": [], "total": 0}
```

#### US002 Frontend Test Sequence
```typescript
// Frontend Test 1: Component Rendering (Write First)
test('should render notification bell icon', () => {
  render(<NotificationBell />);
  expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
});

// Frontend Test 2: State Display (Write Second)  
test('should display unread count when notifications exist', () => {
  const mockNotifications = [{ id: '1', status: 'unread' }];
  render(<NotificationBell notifications={mockNotifications} />);
  expect(screen.getByText('1')).toBeInTheDocument();
});
```

### Phase 2: Real-time Tests (US003-US004)

#### SSE Testing Strategy
```python
def test_sse_connection_should_establish_successfully():
    """Test SSE endpoint connectivity"""
    
def test_sse_should_send_heartbeat_every_30_seconds():
    """Test connection keep-alive"""
    
def test_sse_should_broadcast_new_notifications():
    """Test real-time message delivery"""
    
def test_sse_should_handle_client_disconnect_gracefully():
    """Test error handling and cleanup"""
```

#### Frontend SSE Tests
```typescript
test('should connect to SSE endpoint on mount', () => {
  // Mock EventSource
  const mockEventSource = jest.fn();
  global.EventSource = mockEventSource;
  
  render(<NotificationProvider />);
  
  expect(mockEventSource).toHaveBeenCalledWith('/api/notifications/stream');
});

test('should reconnect on connection loss', async () => {
  // Test reconnection logic
});
```

## 🎯 Test Execution Framework

### Backend Testing Stack
```bash
# Test Runner: pytest
pip install pytest pytest-asyncio pytest-cov

# Database Testing: Use test database
TESTING_DATABASE_URL="postgresql://test:test@localhost/test_coaching"

# API Testing: FastAPI TestClient
from fastapi.testclient import TestClient

# Coverage Requirements
pytest --cov=coaching_assistant --cov-report=html --cov-fail-under=80
```

### Frontend Testing Stack
```bash
# Test Runner: Jest + React Testing Library
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# SSE Testing: Mock EventSource
npm install --save-dev jest-environment-jsdom

# Coverage Requirements  
npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'
```

## 📈 Test Metrics & Monitoring

### Coverage Tracking
```yaml
# Backend Coverage Targets
unit_tests:
  minimum: 80%
  target: 90%
  
api_tests:
  endpoints: 100%
  error_paths: 100%

# Frontend Coverage Targets  
component_tests:
  minimum: 80%
  target: 85%
  
integration_tests:
  user_flows: 100%
  error_states: 90%
```

### Performance Benchmarks
```yaml
# Response Time Targets
unit_tests: <1s total
api_tests: <200ms per request
integration_tests: <10s per test
e2e_tests: <30s per test

# Load Testing
concurrent_connections: 1000
notification_delivery: <100ms
memory_per_connection: <10MB
```

### Quality Gates
**ALL tests MUST pass before merge to main branch**

```bash
# Pre-commit Hooks (Required)
pre-commit install

# Test Commands (Must pass)
make test-backend          # Backend unit + API tests
make test-frontend         # Frontend unit tests  
make test-integration      # Integration tests
make test-performance      # Load tests
make lint                  # Code quality checks
```

## 🔧 TDD Workflow Examples

### Example 1: Adding Notification Model (US001)

#### Step 1: RED - Write Failing Test
```python
def test_should_create_notification_with_valid_data():
    # This will fail - model doesn't exist yet
    notification = Notification(
        user_id=uuid4(),
        title="Transcription Complete", 
        message="Your transcription is ready",
        type="success"
    )
    assert notification.id is not None
```

#### Step 2: GREEN - Minimal Implementation
```python
# Create minimal model to pass test
class Notification(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str
    id: UUID = Field(default_factory=uuid4)
```

#### Step 3: REFACTOR - Improve Structure
```python
# Extract enums, add validation (structural change)
class NotificationType(str, Enum):
    SUCCESS = "success"
    ERROR = "error" 
    INFO = "info"

class Notification(BaseModel):
    user_id: UUID
    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)
    type: NotificationType
    id: UUID = Field(default_factory=uuid4)
```

### Example 2: Adding API Endpoint (US001)

#### Step 1: RED - Write Failing API Test
```python
def test_get_notifications_should_return_user_notifications():
    # This will fail - endpoint doesn't exist
    response = authenticated_client.get("/api/notifications")
    assert response.status_code == 200
    assert "notifications" in response.json()
```

#### Step 2: GREEN - Minimal Endpoint
```python
@router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    return {"notifications": []}
```

#### Step 3: REFACTOR - Add Real Implementation
```python
@router.get("/notifications") 
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> NotificationListResponse:
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).all()
    return NotificationListResponse(notifications=notifications)
```

## 🚨 Anti-Patterns to Avoid

### ❌ Don't Write Tests After Code
```python
# WRONG: Implementation first
def create_notification(data):
    return Notification(**data)

def test_create_notification():  # Written after implementation
    result = create_notification({"title": "test"})
    assert result.title == "test"
```

### ❌ Don't Mix Structural and Behavioral Changes
```git
# WRONG: Mixed commit
git commit -m "feat: add notifications and refactor database connection"

# RIGHT: Separate commits  
git commit -m "refactor: extract database connection interface"
git commit -m "feat: add notification creation endpoint"
```

### ❌ Don't Write Complex Tests First
```python
# WRONG: Testing too much at once
def test_complete_notification_workflow():
    # Creates notification, sends SSE, updates UI, marks as read...
    # This is integration test, not unit test

# RIGHT: One behavior at a time
def test_should_create_notification_with_valid_data():
    # Tests only notification creation
```

## 📚 Resources & Tools

### TDD Resources
- [Beck's "Test Driven Development: By Example"](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Tidy First? by Kent Beck](https://www.oreilly.com/library/view/tidy-first/9781098151232/)
- [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com/)

### Testing Tools
```bash
# Backend
pytest          # Test runner
pytest-cov      # Coverage reporting  
pytest-asyncio  # Async test support
factory-boy     # Test data factories
httpx          # Async HTTP client testing

# Frontend  
jest                    # Test runner
@testing-library/react  # React component testing
@testing-library/user-event  # User interaction simulation
msw                    # API mocking
```

### Development Workflow
1. **Write failing test** (RED)
2. **Run test** to confirm it fails  
3. **Write minimal code** to pass (GREEN)
4. **Run all tests** to ensure they pass
5. **Refactor** if needed (BLUE)
6. **Run tests again** after refactoring
7. **Commit** with clear message
8. **Repeat** for next small increment

**Remember**: The goal is not just working code, but **clean, maintainable, well-tested code** that evolves safely over time.