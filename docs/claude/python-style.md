# Python Code Style & Standards

## Core Requirements
- **Python Compatibility**: Python 3.11+ (primary), test on 3.12 when possible
- **Framework**: FastAPI for backend APIs (established choice)
- **HTTP Libraries**: Use `httpx` for async operations, `requests` for simple sync calls
- **CLI Arguments**: Use `argparse` or `click` with standard format (`--option value` or `--option=value`)

## Naming Conventions
- **Use highly semantic and descriptive names** for classes, functions, and parameters
- Prefer longer, clear names over abbreviated ones
- Examples: `TranscriptionProcessingService` vs `TPS`, `analyze_speaker_segments()` vs `analyze()`

## Configuration Management
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

## Method Chaining Pattern
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

## Logging Standards
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

## Documentation Requirements
- **Every module must include usage examples** in docstrings or README
- **All public functions require docstrings** with examples
- **Create README.md files** for major components explaining "how to use"
- **Include type hints** for all function parameters and return values

## Code Quality Tools
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