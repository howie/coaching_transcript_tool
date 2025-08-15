# Engineering Standards

## Development Methodology: Test-Driven Development (TDD)

### Core Principles
- Always follow the TDD cycle: **Red → Green → Refactor**
- Write the simplest failing test first
- Implement the minimum code needed to make tests pass
- Refactor only after tests are passing
- Follow Beck's "Tidy First" approach by separating structural changes from behavioral changes
- Maintain high code quality throughout development

### TDD Methodology
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

### Tidy First Approach
Separate all changes into two distinct types:

**STRUCTURAL CHANGES**: Rearranging code without changing behavior (renaming, extracting methods, moving code)
**BEHAVIORAL CHANGES**: Adding or modifying actual functionality

- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

### Commit Discipline
Only commit when:
- ALL tests are passing
- ALL compiler/linter warnings have been resolved
- The change represents a single logical unit of work
- Commit messages clearly state whether the commit contains structural or behavioral changes
- Use small, frequent commits rather than large, infrequent ones

### Code Quality Standards
- Eliminate duplication ruthlessly
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects
- Use the simplest solution that could possibly work

### Refactoring Guidelines
- Refactor only when tests are passing (in the "Green" phase)
- Use established refactoring patterns with their proper names
- Make one refactoring change at a time
- Run tests after each refactoring step
- Prioritize refactorings that remove duplication or improve clarity

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

def setup_logging(debug_mode=False):
    log_level = logging.DEBUG if debug_mode else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)  # Note: File logging removed for container compatibility
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

### Example Workflow
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