# Authentication Testing Guide for Clean Architecture Migration

**Created**: 2025-09-21
**Purpose**: Document proper authentication testing procedures for Clean Architecture API endpoints
**Context**: WP6-Cleanup-3 Phase 2 verification

## Overview

This guide explains how to properly test API endpoints with authentication tokens instead of relying on 401 responses. This ensures we're testing real functionality rather than just security barriers.

## Quick Start

### 1. Generate Test Authentication Tokens

Use the provided token generation script:

```bash
# Generate JWT tokens for all user types
python /tmp/create_test_auth_token.py

# This creates tokens for:
# - FREE user
# - STUDENT user
# - PRO user
# - ENTERPRISE user
```

### 2. Run Comprehensive API Tests

```bash
# Run the full test suite with authentication
python /tmp/test_api_with_auth.py

# This tests:
# - Basic server connectivity
# - Plan management endpoints (Clean Architecture)
# - Usage tracking endpoints
# - Authentication enforcement
```

### 3. Manual Testing with curl

```bash
# Export tokens for manual testing
export STUDENT_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
export PRO_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# Test authenticated endpoints
curl -H "Authorization: Bearer $STUDENT_TOKEN" http://localhost:8000/api/v1/plans/current
curl -H "Authorization: Bearer $PRO_TOKEN" http://localhost:8000/api/v1/usage/current
```

## Authentication Token Structure

Our JWT tokens include the following payload:

```json
{
  "sub": "user-id-123",           // Subject (user ID)
  "email": "user@example.com",    // User email
  "plan": "STUDENT",              // User plan type
  "type": "access",               // Token type
  "iat": 1758427828,              // Issued at (timestamp)
  "exp": 1758514228               // Expires (24 hours later)
}
```

## Test User Types

| Plan Type | User ID | Email | Purpose |
|-----------|---------|-------|---------|
| FREE | free-user-456 | free@example.com | Test basic limits |
| STUDENT | student-user-789 | student@example.com | Test student features |
| PRO | pro-user-101 | pro@example.com | Test advanced features |
| ENTERPRISE | enterprise-user-202 | enterprise@example.com | Test unlimited features |

## Critical Endpoints to Test

### 1. Plan Management (Clean Architecture)
- `GET /api/v1/plans/current` - Get current user plan
- `GET /api/v1/plans/compare` - Compare available plans
- `POST /api/v1/plan-limits/validate` - Validate user actions

### 2. Usage Tracking (Clean Architecture)
- `GET /api/v1/usage/current` - Get current usage statistics
- `POST /api/v1/usage/increment` - Track usage increment

### 3. Session Management
- `GET /api/v1/sessions` - List user sessions
- `POST /api/v1/sessions` - Create new session

## Expected Response Examples

### Successful Plan Request (STUDENT user)
```json
{
  "currentPlan": {
    "id": "STUDENT",
    "display_name": "學習方案",
    "limits": {
      "maxSessions": "unlimited",
      "maxTotalMinutes": 300,
      "maxFileSizeMb": 100
    }
  },
  "usageStatus": {
    "plan": "student",
    "current_usage": {
      "session_count": 5,
      "total_minutes": 120
    }
  }
}
```

### Authentication Failure (no token)
```json
{
  "detail": "Not authenticated"
}
```
**Status**: 401 Unauthorized

## Testing Best Practices

### ✅ DO: Test with Real Authentication
```bash
# GOOD: Test with valid JWT token
curl -H "Authorization: Bearer $VALID_TOKEN" /api/v1/plans/current

# Verify you get actual plan data, not just 401
```

### ❌ DON'T: Claim Success Based on 401 Responses
```bash
# BAD: Don't claim endpoints work based on this
curl /api/v1/plans/current
# Response: 401 Unauthorized

# This only proves authentication is working, not the endpoint logic
```

### ✅ DO: Test Multiple User Types
```bash
# Test different plan types to verify Clean Architecture logic
curl -H "Authorization: Bearer $FREE_TOKEN" /api/v1/plans/current
curl -H "Authorization: Bearer $PRO_TOKEN" /api/v1/plans/current
curl -H "Authorization: Bearer $ENTERPRISE_TOKEN" /api/v1/plans/current
```

### ✅ DO: Verify Response Content
```bash
# Check that responses contain expected data structure
curl -H "Authorization: Bearer $STUDENT_TOKEN" /api/v1/plans/current | jq '.currentPlan.display_name'
# Should return: "學習方案"
```

## Troubleshooting

### Issue: 401 Unauthorized with Valid Token

**Causes**:
1. Token expired (24-hour lifespan)
2. Wrong SECRET_KEY in environment
3. User doesn't exist in database

**Solutions**:
```bash
# Regenerate fresh tokens
python /tmp/create_test_auth_token.py

# Check token payload
python -c "import jwt; print(jwt.decode('$TOKEN', verify=False))"

# Verify SECRET_KEY matches server
echo $SECRET_KEY
```

### Issue: 404 Not Found

**Causes**:
1. Endpoint path incorrect
2. API server not running
3. Routes not registered

**Solutions**:
```bash
# Check server is running
curl http://localhost:8000/

# Verify endpoint exists
curl http://localhost:8000/docs  # OpenAPI documentation

# Check server logs for route registration
```

### Issue: 500 Internal Server Error

**Causes**:
1. Database connection issues
2. Missing user records
3. Clean Architecture migration bugs

**Solutions**:
```bash
# Check server logs
tail -f logs/api.log

# Verify database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Run with debug logging
LOGGING_LEVEL=DEBUG python apps/api-server/main.py
```

## Test Results Documentation

### Successful Test Run
```
🎉 ALL AUTHENTICATION TESTS PASSED!
✅ Clean Architecture endpoints working correctly with JWT authentication
✅ Proper authentication enforcement confirmed

📈 SUMMARY: 5 passed, 0 failed
```

### Failed Test Example
```
⚠️  SOME TESTS FAILED
❌ FAIL GET /api/v1/plans/current
   Token: student
   Status: 401 (expected: 200)

📈 SUMMARY: 2 passed, 3 failed
```

## Integration with CI/CD

### Pre-deployment Testing
```bash
# Add to deployment pipeline
make dev-setup
make run-api &
sleep 5
python /tmp/test_api_with_auth.py
if [ $? -eq 0 ]; then
  echo "✅ Authentication tests passed - safe to deploy"
else
  echo "❌ Authentication tests failed - blocking deployment"
  exit 1
fi
```

### Automated Testing
```bash
# Add to GitHub Actions or CI system
- name: Test API Authentication
  run: |
    python /tmp/test_api_with_auth.py
    if [ ! -f /tmp/api_auth_test_results.json ]; then
      echo "Test results not generated"
      exit 1
    fi
```

## Files Created

- `/tmp/create_test_auth_token.py` - JWT token generation utility
- `/tmp/test_api_with_auth.py` - Comprehensive authentication test suite
- `/tmp/api_auth_test_results.json` - Detailed test results (auto-generated)

## Security Notes

### Test Tokens
- Generated tokens use development SECRET_KEY
- Tokens expire after 24 hours
- Test user IDs are clearly marked as test accounts
- Do not use in production

### Production Testing
- Use separate test environment
- Generate tokens with production SECRET_KEY
- Use dedicated test user accounts
- Rotate test tokens regularly

## Conclusion

This authentication testing approach ensures that:

1. **Real Functionality Testing**: We test actual business logic, not just security barriers
2. **Clean Architecture Verification**: Domain models and use cases work correctly
3. **Multiple User Types**: Different plan types are properly handled
4. **Proper Documentation**: Clear evidence of working authentication

By following this guide, we can confidently verify that Clean Architecture migrations maintain both security and functionality.