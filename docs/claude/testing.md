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

### Backend Tests
```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html

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