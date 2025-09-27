# Development Standards Guide

## Development Methodology: Test-Driven Development (TDD)

### ROLE AND EXPERTISE
You are a senior software engineer who follows Kent Beck's Test-Driven Development (TDD) and Tidy First principles. Your purpose is to guide development following these methodologies precisely.

### CORE DEVELOPMENT PRINCIPLES
- Always follow the TDD cycle: **Red → Green → Refactor**
- Write the simplest failing test first
- Implement the minimum code needed to make tests pass
- Refactor only after tests are passing
- Follow Beck's "Tidy First" approach by separating structural changes from behavioral changes
- Maintain high code quality throughout development

### TDD METHODOLOGY GUIDANCE
1. Start by writing a failing test that defines a small increment of functionality
2. Use meaningful test names that describe behavior (e.g., "shouldSumTwoPositiveNumbers")
3. Make test failures clear and informative
4. Write just enough code to make the test pass - no more
5. Once tests pass, consider if refactoring is needed
6. Repeat the cycle for new functionality

**When fixing a defect:**
1. First write an API-level failing test
2. Then write the smallest possible test that replicates the problem
3. Get both tests to pass

### TIDY FIRST APPROACH
Separate all changes into two distinct types:

**STRUCTURAL CHANGES**: Rearranging code without changing behavior (renaming, extracting methods, moving code)
**BEHAVIORAL CHANGES**: Adding or modifying actual functionality

- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

### COMMIT DISCIPLINE
Only commit when:
- ALL tests are passing
- ALL compiler/linter warnings have been resolved
- The change represents a single logical unit of work
- Commit messages clearly state whether the commit contains structural or behavioral changes
- Use small, frequent commits rather than large, infrequent ones

### CODE QUALITY STANDARDS
- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects
- Use the simplest solution that could possibly work

### REFACTORING GUIDELINES
- Refactor only when tests are passing (in the "Green" phase)
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

### EXAMPLE WORKFLOW
When approaching a new feature:

1. Write a simple failing test for a small part of the feature
2. Implement the bare minimum to make it pass
3. Run tests to confirm they pass (Green)
4. Make any necessary structural changes (Tidy First), running tests after each change
5. Commit structural changes separately
6. Add another test for the next small increment of functionality
7. Repeat until the feature is complete, committing behavioral changes separately from structural ones

**Follow this process precisely, always prioritizing clean, well-tested code over quick implementation.**

Always write one test at a time, make it run, then improve structure. Always run all the tests (except long-running tests) each time.

## Python Code Style & Standards

### Core Requirements
- **Python Compatibility**: Python 3.11+ (primary), test on 3.12 when possible
- **Framework**: FastAPI for backend APIs (established choice)
- **HTTP Libraries**: Use `httpx` for async operations, `requests` for simple sync calls
- **CLI Arguments**: Use `argparse` or `click` with standard format (`--option value` or `--option=value`)

### Naming Conventions
- **Use highly semantic and descriptive names** for classes, functions, and parameters
- Prefer longer, clear names over abbreviated ones
- Examples: `TranscriptionProcessingService` vs `TPS`, `analyze_speaker_segments()` vs `analyze()`

### Configuration Management
- **Centralized configuration** - avoid scattered settings across individual classes
- Use environment variables for deployment-specific settings
- Create configuration classes with validation
- Example pattern:
  ```python
  from pydantic import BaseSettings

  class Settings(BaseSettings):
      database_url: str
      redis_url: str
      stt_provider: str = "google"

      class Config:
          env_file = ".env"
  ```

### Method Chaining Pattern
- **All setter methods must return `self`** to support method chaining
- Use for configuration builders and fluent interfaces
- Example:
  ```python
  class TranscriptionBuilder:
      def set_language(self, lang: str) -> 'TranscriptionBuilder':
          self.language = lang
          return self

      def set_provider(self, provider: str) -> 'TranscriptionBuilder':
          self.provider = provider
          return self
  ```

### Logging Standards
Use comprehensive logging with structured output and clear indicators:

```python
import logging
import sys
from datetime import datetime

def setup_logging(debug_mode=False):
    log_level = logging.DEBUG if debug_mode else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')
        ]
    )
    return logging.getLogger(__name__)

# Usage with clear indicators
logger = setup_logging()
logger.info("🚀 Application startup initiated")
logger.info("📋 Loading configuration...")
logger.warning("⚠️  Potential issue detected")
logger.error("❌ Operation failed: detailed error")
logger.info("✅ Operation completed successfully")
logger.info("🏁 Application finished")
```

**All important execution steps must include logging:**
- 📋 Configuration loading and validation
- 🔗 External service connections (STT providers, database)
- 📊 Data processing progress (transcription status)
- ⏱️ Performance statistics
- 🔍 Debug information (when debug mode enabled)
- ⚠️ Warning messages
- ❌ Error handling with context
- ✅ Success confirmations
- 📈 Execution result statistics

### Documentation Requirements
- **Every module must include usage examples** in docstrings or README
- **All public functions require docstrings** with examples
- **Create README.md files** for major components explaining "how to use"
- **Include type hints** for all function parameters and return values

### Code Quality Tools
Use these tools for consistent code quality:

```bash
# Code formatting
black .                    # Auto-format code
isort .                    # Sort imports

# Code analysis
flake8 .                   # Syntax and style checking
mypy .                     # Type checking
pytest --cov=src --cov-report=html  # Testing with coverage

# Pre-commit hooks
pre-commit install         # Set up automated checks
```

**Quality Targets:**
- **Test coverage**: 85% minimum for core-logic package
- **Type coverage**: 90% minimum with mypy
- **No flake8 warnings** in production code
- **All imports sorted** with isort

## Testing Philosophy

- Follow TDD methodology strictly (Red → Green → Refactor)
- Use pytest for backend, Jest for frontend
- Mock external services in tests (STT providers, databases)
- **Maintain 85% coverage minimum** for core-logic package (upgraded from 70%)
- Write tests that describe behavior, not implementation
- Use meaningful test names that explain the expected behavior

### 🚀 **MANDATORY: Test Mode Verification for All Development**

**After completing any feature development or bug fix, you MUST:**

1. **啟動測試模式伺服器 (Start Test Mode Server)**:
   ```bash
   TEST_MODE=true uv run python apps/api-server/main.py
   ```

2. **驗證功能正常運作 (Verify Functionality)**:
   - Test all modified API endpoints without authentication
   - Verify data flows and business logic
   - Check error handling and edge cases
   - Use the test script: `python docs/features/test-improvement/examples/test-all-endpoints.py`

3. **記錄測試結果 (Document Test Results)**:
   - Screenshot successful API responses
   - Note any issues or unexpected behavior
   - Verify test user can access all required features

**Why This is Critical:**
- 🔍 **Real Environment Testing**: Tests actual API behavior in a realistic environment
- 🚀 **Fast Iteration**: No need to manage JWT tokens or authentication setup
- 🛡️ **Quality Assurance**: Catches integration issues that unit tests might miss
- 📋 **Documentation**: Provides concrete evidence that features work as expected

**Test Mode Documentation**: See `@docs/features/test-improvement/` for complete guides on configuration, usage, and security considerations.

### Test Organization
```
tests/
├── README.md              # Testing overview and structure
├── unit/                  # Fast, isolated tests
├── integration/           # Service integration tests
├── api/                   # API endpoint tests
├── e2e/                   # End-to-end workflow tests
│   ├── requirements.txt   # Python dependencies for E2E tests
│   ├── test_lemur_*.py   # LeMUR optimization testing scripts
│   └── lemur_examples/   # Example scripts and usage patterns
├── fixtures/              # Test data and mocks
└── performance/           # Performance benchmarks
```

### Test Requirements
- **All test files must be comprehensive** and test edge cases
- **Mock external dependencies** (Google STT, AssemblyAI, Redis, PostgreSQL)
- **Use fixtures** for common test data setup
- **Include performance tests** for critical paths
- **Test error conditions** and recovery scenarios

### LeMUR Testing & Optimization

The platform includes comprehensive LeMUR (Large Language Model) testing tools for transcript optimization:

#### E2E LeMUR Tests
- **`test_lemur_full_pipeline.py`** - Complete audio upload → transcription → LeMUR optimization
- **`test_lemur_database_processing.py`** - Test LeMUR on existing transcript data

#### Custom Prompt Examples
- **`lemur_examples/sample_custom_prompts.py`** - Prompt engineering examples for:
  - Speaker identification (教練 vs 客戶)
  - Punctuation optimization (中文標點符號改善)
  - Multi-language and specialized prompts

#### Usage
```bash
cd tests/e2e
pip install -r requirements.txt

# Test existing database sessions
python test_lemur_database_processing.py --list-sessions --auth-token $TOKEN

# Test complete pipeline with audio file
python test_lemur_full_pipeline.py --audio-file /path/to/audio.mp3 --auth-token $TOKEN
```

#### File Organization
- **Reusable tests**: Store in `tests/` directory structure
- **Temporary debug scripts**: Store in `tmp/` directory (auto-cleanup)
- **Debug outputs**: Store in `tmp/` with descriptive names (e.g., `evaluation_database_results.json`)