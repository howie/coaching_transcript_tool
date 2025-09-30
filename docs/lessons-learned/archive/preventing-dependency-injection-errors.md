# Preventing Dependency Injection Errors

This document explains how to prevent the AttributeError that occurred in production with plan limits validation.

## The Problem

On 2025-08-17, production logs showed:
```
'UserResponse' object has no attribute 'session_count'
'UserResponse' object has no attribute 'transcription_count'
```

This occurred because plan limits API endpoints were using the wrong dependency injection function.

## Root Cause

**Incorrect Code:**
```python
from coaching_assistant.api.auth import get_current_user

@router.post("/validate-action")
async def validate_action(
    current_user: User = Depends(get_current_user),  # ❌ WRONG
    db: Session = Depends(get_db)
):
    # This fails because get_current_user returns UserResponse
    session_count = current_user.session_count or 0  # AttributeError!
```

**Correct Code:**
```python
from coaching_assistant.api.auth import get_current_user_dependency

@router.post("/validate-action") 
async def validate_action(
    current_user: User = Depends(get_current_user_dependency),  # ✅ CORRECT
    db: Session = Depends(get_db)
):
    # This works because get_current_user_dependency returns User model
    session_count = current_user.session_count or 0  # Works!
```

## Key Differences

| Function | Returns | Has Usage Attributes | Use Case |
|----------|---------|---------------------|----------|
| `get_current_user` | `UserResponse` | ❌ No | API responses to frontend |
| `get_current_user_dependency` | `User` | ✅ Yes | Internal API logic |

## Prevention Strategy

### 1. Automated Tests

We've added comprehensive tests to catch this error:

```bash
# Run dependency injection tests
pytest tests/unit/api/test_plan_limits_dependency_injection.py

# Run User model contract tests  
pytest tests/unit/models/test_user_plan_limits_contract.py

# Run API integration tests
pytest tests/integration/api/test_plan_limits_integration.py
```

### 2. Pre-commit Hooks

Added a pre-commit hook that automatically checks for wrong dependency usage:

```yaml
- repo: local
  hooks:
    - id: check-dependency-injection
      name: Check API Dependency Injection
      entry: python scripts/check_dependency_injection.py
      language: system
      files: ^src/coaching_assistant/api/.*\.py$
```

### 3. CI/CD Pipeline

GitHub Actions workflow `.github/workflows/test-dependency-injection.yml` runs on every PR:

- Tests dependency injection compatibility
- Verifies User model contract
- Smoke tests API endpoints
- Prevents AttributeError in production

### 4. Static Analysis

The `scripts/check_dependency_injection.py` script:

- Parses AST to find dependency injection patterns
- Flags usage of `get_current_user` in API endpoints
- Ensures correct imports and function signatures

## Rules to Follow

### ✅ DO:
- Use `get_current_user_dependency` for internal API logic
- Import: `from coaching_assistant.api.auth import get_current_user_dependency`
- Type hint: `current_user: User = Depends(get_current_user_dependency)`
- Access usage attributes: `current_user.session_count`, `current_user.transcription_count`

### ❌ DON'T:
- Use `get_current_user` for internal API logic (it returns UserResponse)
- Import: `from coaching_assistant.api.auth import get_current_user` (for internal APIs)
- Try to access usage attributes on UserResponse objects

## Quick Check

Run this to verify your API endpoint uses correct dependencies:

```python
import inspect
from your_api_module import your_endpoint_function
from coaching_assistant.api.auth import get_current_user_dependency

sig = inspect.signature(your_endpoint_function)
current_user_param = sig.parameters['current_user']
assert current_user_param.default.dependency == get_current_user_dependency
```

## When This Error Occurs

**Symptoms:**
- `AttributeError: 'UserResponse' object has no attribute 'session_count'`
- 500 errors in plan validation endpoints
- Missing usage tracking data

**Fix:**
1. Change import from `get_current_user` to `get_current_user_dependency`
2. Update all function signatures in the file
3. Run tests to verify fix
4. Deploy

## Testing Your Changes

Before deploying changes to plan limits or user authentication:

```bash
# Run all dependency injection tests
pytest tests/unit/api/test_plan_limits_dependency_injection.py -v

# Run contract tests
pytest tests/unit/models/test_user_plan_limits_contract.py -v

# Check with static analysis
python scripts/check_dependency_injection.py src/coaching_assistant/api/

# Run pre-commit hooks
pre-commit run --all-files
```

## Files Changed in the Fix

- `src/coaching_assistant/api/plan_limits.py` - Fixed dependency injection
- `tests/unit/api/test_plan_limits_dependency_injection.py` - Added tests
- `tests/integration/api/test_plan_limits_integration.py` - Added integration tests
- `tests/unit/models/test_user_plan_limits_contract.py` - Added contract tests
- `.github/workflows/test-dependency-injection.yml` - Added CI checks
- `scripts/check_dependency_injection.py` - Added static analysis
- `.pre-commit-config.yaml` - Added pre-commit hook

This comprehensive approach ensures this type of error won't reach production again.