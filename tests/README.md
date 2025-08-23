# Testing Structure

This directory contains all reusable test scripts and suites for the Coaching Assistant Platform.

## Directory Structure

```
tests/
├── README.md              # This file - testing overview
├── unit/                  # Unit tests (fast, isolated)
├── integration/           # Service integration tests  
├── api/                   # API endpoint tests
└── e2e/                   # End-to-end workflow tests
    ├── requirements.txt   # Python dependencies for E2E tests
    ├── test_lemur_*.py   # LeMUR optimization testing scripts
    └── lemur_examples/    # Example scripts and usage patterns
```

## Testing Categories

### Unit Tests (`unit/`)
- Fast, isolated tests
- Mock external dependencies
- Test individual functions/methods
- Run with: `pytest tests/unit/`

### Integration Tests (`integration/`)
- Test service interactions
- Database connections
- External API integrations
- Run with: `pytest tests/integration/`

### API Tests (`api/`)
- HTTP endpoint testing
- Request/response validation
- Authentication testing
- Run with: `pytest tests/api/`

### End-to-End Tests (`e2e/`)
- Complete workflow validation
- Real system interactions
- User journey testing
- LeMUR optimization validation

## LeMUR Testing

The E2E directory contains comprehensive LeMUR (Large Language Model) testing tools:

### Scripts
- `test_lemur_full_pipeline.py` - Complete audio upload → transcription → LeMUR optimization
- `test_lemur_database_processing.py` - Test LeMUR on existing transcript data

### Examples
- `lemur_examples/run_*.sh` - Shell script wrappers for easy execution
- `lemur_examples/sample_custom_prompts.py` - Prompt engineering examples

### Usage
```bash
cd tests/e2e
pip install -r requirements.txt

# Test existing database sessions
python test_lemur_database_processing.py --list-sessions --auth-token $TOKEN

# Test complete pipeline with audio file
python test_lemur_full_pipeline.py --audio-file /path/to/audio.mp3 --auth-token $TOKEN
```

## Running Tests

### Prerequisites
```bash
# Install Python dependencies
cd tests/e2e && pip install -r requirements.txt

# Set environment variables
export AUTH_TOKEN="your_auth_token"
export API_URL="http://localhost:8000"
```

### Quick Commands
```bash
# Run all unit tests
make test

# Run integration tests
pytest tests/integration/

# Run API tests
pytest tests/api/

# Run E2E LeMUR tests
cd tests/e2e && python test_lemur_database_processing.py --list-sessions --auth-token $AUTH_TOKEN
```

## Test Data Management

- **Temporary files**: Use `tmp/` directory (gets cleaned up)
- **Test fixtures**: Store in respective `tests/*/fixtures/` directories
- **Generated results**: Output to `tmp/` by default, use `--output` flag for permanent storage

## Best Practices

1. **Keep tests isolated**: Each test should be independent
2. **Use meaningful names**: Test names should describe the expected behavior
3. **Mock external services**: Don't rely on external systems in unit tests
4. **Clean up resources**: Ensure tests clean up after themselves
5. **Document test purposes**: Include clear docstrings explaining what each test validates

## Adding New Tests

1. Choose the appropriate category (unit/integration/api/e2e)
2. Follow existing naming conventions
3. Include proper documentation
4. Add to CI/CD pipeline if applicable
5. Update this README if adding new test types