# Testing Philosophy & Standards

## Core Philosophy

- Follow TDD methodology strictly (Red → Green → Refactor)
- Use pytest for backend, Jest for frontend
- Mock external services in tests (STT providers, databases)
- **Maintain 85% coverage minimum** for core-logic package
- Write tests that describe behavior, not implementation
- Use meaningful test names that explain the expected behavior

## Test Organization

```
tests/
├── unit/                  # Fast, isolated tests
├── integration/           # Service integration tests  
├── e2e/                   # End-to-end workflow tests
├── fixtures/              # Test data and mocks
└── performance/           # Performance benchmarks
```

## Test Requirements

- **All test files must be comprehensive** and test edge cases
- **Mock external dependencies** (Google STT, AssemblyAI, Redis, PostgreSQL)
- **Use fixtures** for common test data setup
- **Include performance tests** for critical paths
- **Test error conditions** and recovery scenarios

## Running Tests

⚡ **For complete test command reference, see: [Make Test Organization](make-test-organization.md)**

### Backend Tests (Standalone)
```bash
# Run unit + database integration tests (no server required)
make test

# Run only unit tests (fastest)
make test-unit

# Run only database integration tests
make test-db

# Run with coverage
make coverage
```

### Backend Tests (Server-Dependent)
```bash
# Run API/E2E tests (requires API server)
make test-server

# Run payment system tests (requires server + auth)
make test-payment

# Run all tests
make test-all
```

### Legacy pytest Commands
```bash
# Run specific test file
pytest tests/unit/test_transcription.py

# Run with verbose output
pytest -v

# Run only fast tests (exclude long-running)
pytest -m "not slow"
```

### Frontend Tests
```bash
# Run all frontend tests
cd apps/web && npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

## Test Patterns

### Unit Test Example
```python
def test_transcription_service_creates_session():
    """Test that transcription service correctly creates a new session"""
    # Arrange
    mock_repo = Mock()
    service = TranscriptionService(mock_repo)
    
    # Act
    session = service.create_session(user_id="123", language="en")
    
    # Assert
    assert session.user_id == "123"
    assert session.language == "en"
    mock_repo.save.assert_called_once()
```

### Integration Test Example
```python
@pytest.mark.integration
async def test_stt_provider_processes_audio():
    """Test that STT provider correctly processes audio file"""
    # Arrange
    provider = GoogleSTTProvider()
    audio_file = "tests/fixtures/sample.wav"
    
    # Act
    result = await provider.transcribe(audio_file)
    
    # Assert
    assert result.transcript is not None
    assert len(result.segments) > 0
```

### E2E Test Example
```python
@pytest.mark.e2e
async def test_complete_transcription_workflow(client, db_session):
    """Test complete workflow from upload to transcript download"""
    # Create session
    response = await client.post("/sessions", json={"language": "en"})
    session_id = response.json()["id"]
    
    # Upload audio
    files = {"audio": open("tests/fixtures/sample.wav", "rb")}
    response = await client.post(f"/sessions/{session_id}/upload", files=files)
    
    # Start transcription
    response = await client.post(f"/sessions/{session_id}/start-transcription")
    
    # Wait for completion
    await wait_for_status(client, session_id, "completed")
    
    # Download transcript
    response = await client.get(f"/sessions/{session_id}/transcript")
    assert response.status_code == 200
```

## Mocking Guidelines

### External Services
```python
# Mock STT providers
@patch('coaching_assistant.core.services.stt.GoogleSTTProvider')
def test_with_mocked_stt(mock_stt):
    mock_stt.transcribe.return_value = TranscriptionResult(
        transcript="Hello world",
        segments=[...]
    )
    # Test implementation
```

### Database
```python
# Use test database
@pytest.fixture
def test_db():
    """Create test database for integration tests"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
```

### Redis/Celery
```python
# Mock Celery tasks
@patch('coaching_assistant.tasks.transcription.delay')
def test_async_task(mock_task):
    mock_task.return_value = AsyncResult("task-id")
    # Test implementation
```

## Performance Testing

```python
@pytest.mark.performance
def test_transcription_performance(benchmark):
    """Benchmark transcription processing time"""
    service = TranscriptionService()
    
    # Benchmark the function
    result = benchmark(service.process_audio, "sample.wav")
    
    # Assert performance requirements
    assert benchmark.stats['mean'] < 2.0  # Should complete in < 2 seconds
```

## Test Data Management

### Fixtures Directory Structure
```
tests/fixtures/
├── audio/
│   ├── sample_en.wav      # English sample
│   ├── sample_zh.wav      # Chinese sample
│   └── sample_ja.wav      # Japanese sample
├── transcripts/
│   ├── expected_en.json   # Expected English output
│   └── expected_zh.json   # Expected Chinese output
└── mock_responses/
    ├── google_stt.json     # Mock Google STT responses
    └── assemblyai.json     # Mock AssemblyAI responses
```

## Coverage Requirements

- **Core Logic**: 85% minimum
- **API Endpoints**: 80% minimum
- **Utilities**: 70% minimum
- **Integration Points**: 90% minimum

## CI/CD Integration

Tests run automatically on:
- Every pull request
- Pre-commit hooks (fast tests only)
- Main branch commits (full test suite)
- Deployment pipeline (e2e tests)

## Best Practices

1. **Test Independence**: Each test should be able to run in isolation
2. **Clear Assertions**: Make test failures obvious with descriptive messages
3. **Fast Feedback**: Unit tests should complete in < 100ms
4. **Deterministic**: Tests should produce same results every run
5. **Documentation**: Complex tests should include comments explaining the scenario

## Frontend Testing Strategy

### COMPREHENSIVE TESTING APPROACH

**1. Testing Hierarchy (按重要性排序):**
- **Unit Tests**: 獨立組件功能測試 (Jest + React Testing Library)
- **Integration Tests**: 組件間交互測試
- **i18n Tests**: 多語言功能驗證
- **E2E Tests**: 完整用戶流程測試 (Playwright/Cypress)

**2. Test Coverage Requirements:**
- **Core business logic**: 90%+ coverage
- **UI components**: 80%+ coverage  
- **i18n functionality**: 100% key coverage
- **API integration**: Mock all external calls

### TESTING BEST PRACTICES

**Unit Testing (Jest + React Testing Library):**
```typescript
// 1. 組件渲染測試
describe('ComponentName', () => {
  it('should render correctly with required props', () => {
    render(<Component prop="value" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  // 2. 用戶交互測試
  it('should handle user interactions correctly', async () => {
    const mockHandler = jest.fn();
    render(<Component onClick={mockHandler} />);
    
    await userEvent.click(screen.getByRole('button'));
    expect(mockHandler).toHaveBeenCalledTimes(1);
  });

  // 3. 狀態變化測試
  it('should update state when props change', () => {
    const { rerender } = render(<Component status="loading" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    rerender(<Component status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });
});
```

**API Integration Testing:**
```typescript
// Mock API calls properly
jest.mock('@/lib/api', () => ({
  apiClient: {
    getSession: jest.fn(),
    updateSession: jest.fn(),
  }
}));

// Test error handling
it('should handle API errors gracefully', async () => {
  (apiClient.getSession as jest.Mock).mockRejectedValue(
    new Error('Network error')
  );
  
  render(<SessionComponent />);
  
  await waitFor(() => {
    expect(screen.getByText('Error loading session')).toBeInTheDocument();
  });
});
```

**Context and Provider Testing:**
```typescript
// Test wrapper for context providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <I18nProvider initialLanguage="zh">
    <AuthProvider>
      {children}
    </AuthProvider>
  </I18nProvider>
);

// Avoid mock conflicts
beforeEach(() => {
  jest.clearAllMocks();
  jest.resetModules(); // 重要：重置模組狀態
});
```

### TESTING COMMANDS & AUTOMATION

**Development Testing Workflow:**
```bash
# 1. 開發時持續測試
npm run test:watch

# 2. 完整測試套件
npm test

# 3. 測試覆蓋率檢查
npm run test:coverage

# 4. i18n 專項測試
npm test -- --testPathPattern="i18n"

# 5. 特定組件測試
npm test -- ComponentName

# 6. E2E 測試 (如果有設置)
npm run test:e2e
```

**Pre-commit 自動化:**
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: frontend-tests
      name: Run frontend tests
      entry: npm test -- --passWithNoTests --watchAll=false
      language: system
      pass_filenames: false
```

### TESTING DEBUGGING STRATEGIES

**Mock 問題解決:**
```typescript
// 1. 避免重複定義 mock (重要！)
beforeEach(() => {
  jest.resetModules();
  jest.clearAllMocks();
});

// 2. 正確 mock context hooks
jest.mock('@/contexts/auth-context', () => ({
  useAuth: () => ({
    user: { id: 'test', name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
  }),
  AuthProvider: ({ children }: any) => children,
}));

// 3. 處理複雜 mock 場景
const mockApiClient = {
  getSession: jest.fn().mockResolvedValue(mockSession),
  updateSession: jest.fn().mockResolvedValue({}),
};

jest.mock('@/lib/api', () => ({
  apiClient: mockApiClient,
}));
```

**測試數據管理:**
```typescript
// 建立可重用的測試數據
export const mockSessionData = {
  basic: {
    id: 'session-1',
    client_name: 'Test Client',
    session_date: '2024-01-01',
  },
  withTranscript: {
    ...basic,
    transcript: {
      segments: [/* ... */],
      duration_sec: 300,
    },
  },
};

// 使用工廠函數生成測試數據
const createMockSession = (overrides = {}) => ({
  ...mockSessionData.basic,
  ...overrides,
});
```

### CONTINUOUS INTEGRATION

**GitHub Actions 測試配置:**
```yaml
# .github/workflows/test.yml
- name: Run Frontend Tests
  run: |
    cd apps/web
    npm ci
    npm run test:ci
    npm run test:coverage
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./apps/web/coverage/lcov.info
```

### TESTING ANTI-PATTERNS TO AVOID

**❌ 常見錯誤:**
1. **過度依賴 snapshot testing** - 容易變得脆弱
2. **測試實現細節而非行為** - 測試應該關注用戶體驗
3. **Mock 過多內部函數** - 應該測試整體功能
4. **忽略 async/await 錯誤處理** - 必須測試錯誤情況
5. **測試覆蓋率為了數字而非質量** - 重質不重量

**✅ 最佳實踐:**
1. **測試用戶行為和預期結果**
2. **使用有意義的測試描述**
3. **適當隔離測試環境**
4. **測試 happy path 和 error cases**
5. **保持測試簡單且專注**

### I18N TESTING STRATEGY

**Translation Consistency Tests:**
```typescript
// Test all keys have both languages
describe('Translation Consistency', () => {
  it('should have matching keys for Chinese and English', () => {
    const zhKeys = Object.keys(translations.zh);
    const enKeys = Object.keys(translations.en);
    
    zhKeys.forEach(key => {
      expect(enKeys).toContain(key);
      expect(translations.en[key]).toBeDefined();
      expect(translations.en[key]).not.toBe('');
    });
  });
});
```

**Functional i18n Tests:**
```typescript
// Test component renders correctly in both languages
describe('Component i18n', () => {
  it('should render Chinese translations correctly', () => {
    render(
      <I18nProvider initialLanguage="zh">
        <MyComponent />
      </I18nProvider>
    );
    
    expect(screen.getByText('會談概覽')).toBeInTheDocument();
  });
  
  it('should render English translations correctly', () => {
    render(
      <I18nProvider initialLanguage="en">
        <MyComponent />
      </I18nProvider>
    );
    
    expect(screen.getByText('Overview')).toBeInTheDocument();
  });
});
```

**Parameter Interpolation Tests:**
```typescript
it('should handle parameter interpolation correctly', () => {
  const interpolationKeys = [
    'sessions.uploadSuccess', // {count}
    'sessions.conversationSummary', // {duration}, {count}
  ];

  interpolationKeys.forEach(key => {
    const zhValue = translations.zh[key];
    const enValue = translations.en[key];
    
    // Should contain parameter placeholders
    expect(zhValue).toMatch(/\{[^}]+\}/);
    expect(enValue).toMatch(/\{[^}]+\}/);
  });
});
```

### COMPONENT TESTING PATTERNS

**Form Testing:**
```typescript
describe('SessionForm', () => {
  it('should validate required fields', async () => {
    render(<SessionForm onSubmit={jest.fn()} />);
    
    // Submit without filling required fields
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    // Check validation messages
    expect(screen.getByText('Client is required')).toBeInTheDocument();
    expect(screen.getByText('Date is required')).toBeInTheDocument();
  });
  
  it('should submit with valid data', async () => {
    const mockSubmit = jest.fn();
    render(<SessionForm onSubmit={mockSubmit} />);
    
    // Fill form
    await userEvent.type(screen.getByLabelText(/client/i), 'Test Client');
    await userEvent.type(screen.getByLabelText(/date/i), '2024-01-01');
    
    // Submit
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(mockSubmit).toHaveBeenCalledWith({
      client: 'Test Client',
      date: '2024-01-01',
    });
  });
});
```

**Async Component Testing:**
```typescript
describe('SessionDetailPage', () => {
  it('should display loading state initially', () => {
    render(<SessionDetailPage sessionId="123" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
  
  it('should display session data when loaded', async () => {
    const mockSession = { id: '123', client_name: 'Test Client' };
    (apiClient.getSession as jest.Mock).mockResolvedValue(mockSession);
    
    render(<SessionDetailPage sessionId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Client')).toBeInTheDocument();
    });
  });
  
  it('should display error message on failure', async () => {
    (apiClient.getSession as jest.Mock).mockRejectedValue(
      new Error('Session not found')
    );
    
    render(<SessionDetailPage sessionId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading session')).toBeInTheDocument();
    });
  });
});
```

### PERFORMANCE TESTING

**Component Render Performance:**
```typescript
describe('ComponentName Performance', () => {
  it('should render within performance budget', () => {
    const startTime = performance.now();
    
    render(<LargeComponent items={generateMockItems(1000)} />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within 100ms
    expect(renderTime).toBeLessThan(100);
  });
});
```

**Memory Leak Detection:**
```typescript
describe('Memory Management', () => {
  it('should cleanup event listeners on unmount', () => {
    const { unmount } = render(<ComponentWithEventListeners />);
    
    // Track event listeners before unmount
    const initialListeners = window.addEventListener.mock.calls.length;
    
    unmount();
    
    // Verify cleanup
    expect(window.removeEventListener).toHaveBeenCalledTimes(initialListeners);
  });
});
```