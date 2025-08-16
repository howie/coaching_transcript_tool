# Test Directory Structure

This directory contains the complete test suite for the Coaching Assistant Platform, organized by test type for optimal maintainability and performance.

## 📁 Directory Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── services/           # Service layer tests
│   ├── models/             # Database model tests
│   ├── providers/          # STT provider tests
│   └── utils/              # Utility function tests
├── integration/             # Integration tests (service combinations)
│   ├── api/                # API endpoint integration tests
│   └── database/           # Database integration tests
├── e2e/                     # End-to-end tests (complete workflows)
├── performance/             # Performance and load tests
├── data/                    # Test data files
├── conftest.py             # Pytest configuration and fixtures
└── run_tests.py            # Test runner script
```

## 🧪 Test Categories

### **Unit Tests** (`tests/unit/`)
Fast, isolated tests that test individual components in isolation.

**Characteristics:**
- Run in < 1 second each
- No external dependencies (database, APIs, files)
- Use mocks for dependencies
- Test single functions or classes

**Examples:**
- `unit/services/test_usage_tracking.py` - Usage tracking service logic
- `unit/models/test_user.py` - User model validation
- `unit/providers/test_assemblyai_provider.py` - AssemblyAI provider logic

### **Integration Tests** (`tests/integration/`)
Tests that verify how multiple components work together.

**Characteristics:**
- May use test database
- Test component interactions
- Verify API contracts
- Run in < 5 seconds each

**Examples:**
- `integration/api/test_plan_limits.py` - Plan limit API endpoints
- `integration/database/test_database_models.py` - Database model relationships

### **End-to-End Tests** (`tests/e2e/`)
Complete user journey tests that verify entire workflows.

**Characteristics:**
- Test complete user scenarios
- May take several seconds
- Use real or near-real environments
- Verify business logic end-to-end

**Examples:**
- `e2e/test_beta_limits.py` - Complete plan limit enforcement testing
- `e2e/test_plan_upgrade_e2e.py` - Plan upgrade user journey

### **Performance Tests** (`tests/performance/`)
Tests that verify system performance under load.

**Examples:**
- `performance/test_billing_performance.py` - Billing system performance

## 🚀 Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run by Category
```bash
# Unit tests only (fastest)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (slowest)
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v
```

### Run Specific Test Files
```bash
# Single test file
pytest tests/unit/services/test_usage_tracking.py -v

# With coverage
pytest tests/unit/ --cov=src/coaching_assistant --cov-report=html
```

### Run Tests for Specific Features
```bash
# Plan limitation tests
pytest tests/ -k "plan" -v

# Usage tracking tests
pytest tests/ -k "usage" -v

# API tests
pytest tests/integration/api/ -v
```

## 🛠️ Test Configuration

### Fixtures (`conftest.py`)
Common test fixtures are defined in `conftest.py`:
- Database setup/teardown
- User fixtures
- Session fixtures
- Authentication helpers

### Environment Variables
Tests use these environment variables:
```bash
# Test database
DATABASE_URL=postgresql://test:test@localhost/coaching_test

# Test mode
TESTING=true

# Debug mode for verbose output
TEST_DEBUG=true
```

## 📊 Test Quality Standards

### Coverage Requirements
- **Unit tests**: 95% line coverage minimum
- **Integration tests**: 85% feature coverage minimum
- **E2E tests**: 100% critical path coverage

### Performance Requirements
- **Unit tests**: < 1 second per test
- **Integration tests**: < 5 seconds per test
- **E2E tests**: < 30 seconds per test
- **Full test suite**: < 5 minutes total

### Quality Criteria
- All tests must be deterministic (no flaky tests)
- Tests must clean up after themselves
- Use descriptive test names that explain behavior
- Include both happy path and error case testing

## 🔍 Test Data

### Test Data Files (`tests/data/`)
- `sample_1.vtt` - Sample VTT transcript file
- `sample_2.vtt` - Another sample VTT file

### Test Fixtures
- Use `tests/conftest.py` for shared fixtures
- Create specific fixtures in test files when needed
- Always clean up test data after tests complete

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest tests/ -v -s
```

### Debug Single Test
```bash
pytest tests/unit/services/test_usage_tracking.py::TestUsageTracking::test_increment_usage -v -s
```

### Profile Test Performance
```bash
pytest tests/ --durations=10
```

## 📝 Writing New Tests

### Test Naming Convention
- File names: `test_<component_name>.py`
- Class names: `Test<ComponentName>`
- Method names: `test_<behavior_description>`

### Example Unit Test
```python
"""Unit tests for usage tracking service."""

import pytest
from unittest.mock import Mock, patch
from coaching_assistant.services.usage_tracking import UsageTrackingService

class TestUsageTracking:
    """Test usage tracking service."""
    
    def test_increment_session_count_success(self):
        """Should increment user session count correctly."""
        # Arrange
        mock_db = Mock()
        service = UsageTrackingService(mock_db)
        user = Mock(session_count=5)
        
        # Act
        service.increment_session_count(user)
        
        # Assert
        assert user.session_count == 6
        mock_db.commit.assert_called_once()
```

### Example Integration Test
```python
"""Integration tests for plan limits API."""

def test_create_session_with_limits(client, test_user, db_session):
    """Should block session creation when limit exceeded."""
    # Set user to have max sessions
    test_user.session_count = 3  # FREE plan limit
    db_session.commit()
    
    # Try to create session
    response = client.post("/api/sessions", json={"title": "Test"})
    
    # Should be blocked
    assert response.status_code == 403
    assert "session_limit_exceeded" in response.json()["detail"]
```

## 🔄 Continuous Integration

The test suite runs automatically on:
- Pull request creation
- Push to main branch
- Nightly schedule for full suite

### CI Pipeline
1. **Fast feedback**: Unit tests run first
2. **Integration validation**: Integration tests run second
3. **End-to-end verification**: E2E tests run last
4. **Performance check**: Performance tests run nightly

---

**Keep tests fast, reliable, and maintainable!** 🧪✨