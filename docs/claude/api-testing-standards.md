# API Testing & Verification Standards

## 🚫 CRITICAL RULE: Never Claim API Fixes Without Real Verification

**🔥 MANDATORY AUTHENTICATION TESTING (User Requirement)**
- **NEVER ACCEPTABLE**: Claiming API fixes based only on 401 authentication responses
- **ALWAYS REQUIRED**: Use real JWT tokens with proper authentication for ALL testing
- **User Quote**: "任何 API 測試，回覆 Now we're getting 401 (authentication required) 都是不能接受的，要測試就必須取得 token 測試!!!"

**FORBIDDEN Claims:**
- ❌ "The API now returns 401 instead of 500, so the fix works"
- ❌ "Both endpoints correctly respond with authentication required"
- ❌ "The enum bug is fixed" (based only on status code changes)
- ❌ "Now we're getting 401 (authentication required)" (without real token testing)

## REQUIRED Verification for API Fix Claims

### 1. **Authenticate with Real Tokens** (MANDATORY)
```bash
# MUST create and use real JWT tokens for testing
# NEVER test without proper authentication
# Example with real token:
curl -H "Authorization: Bearer <actual_jwt_token>" http://localhost:8000/api/v1/sessions/{session_id}

# Required token format:
{
  "sub": "user_id",
  "exp": timestamp,
  "type": "access",
  "email": "user@example.com"
}
```

### 2. **Verify Real Data Responses**
```bash
# Must show actual JSON response data, not just status codes
# Example acceptable evidence:
{
  "currentPlan": {
    "display_name": "學習方案",
    "id": "STUDENT"
  },
  "usageStatus": {
    "plan": "student",
    "planLimits": {...}
  }
}
```

### 3. **Test Multiple User Types**
- Test with users having different plans (FREE, STUDENT, PRO)
- Verify each plan type returns correct data
- Document which users were tested and their plan types

### 4. **Evidence-Based Claims Only**
```markdown
✅ ACCEPTABLE: "Tested with user howie.yu@gmail.com (STUDENT plan) - API returns complete plan data with display_name '學習方案'"

❌ UNACCEPTABLE: "Both endpoints now correctly return 401 instead of 500 errors"
```

### 5. **Use Test Automation When Possible**
```python
# Create temporary auth tokens in test scripts
# Verify complete request/response cycles
# Test actual business logic, not just HTTP status
```

## Testing Token Management

**For API Testing:**
- Create temporary test tokens with limited scope
- Use test user accounts with known plan types
- Document which authentication method was used
- Clean up test tokens after verification

**Authentication Testing Levels:**
1. **Unauthenticated**: Should return 401
2. **Authenticated but wrong plan**: Should return appropriate data/limits
3. **Authenticated with test plan**: Should return real plan configuration data

## Mandatory Documentation for API Claims

When claiming an API fix works, provide:
```markdown
## API Fix Verification

**Endpoint Tested**: `/api/v1/plans/current`
**User Tested**: test.user@example.com (STUDENT plan)
**Authentication**: JWT token (expires: 2025-01-17T10:00:00Z)
**Response Status**: 200 OK
**Response Data**:
{
  "currentPlan": {...actual data...},
  "usageStatus": {...actual limits...}
}

**Before Fix**: 500 Internal Server Error "UserPlan.STUDENT not in enum"
**After Fix**: 200 OK with complete plan data
```

This ensures all API fix claims are backed by real evidence, not assumptions.

## 🚀 **MANDATORY: Test Mode Verification for All Development**

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