# API Testing & Verification Standards

## 🚫 CRITICAL RULE: Never Claim API Fixes Without Real Verification

### 🔥 MANDATORY AUTHENTICATION TESTING (User Requirement)
- **NEVER ACCEPTABLE**: Claiming API fixes based only on 401 authentication responses
- **ALWAYS REQUIRED**: Use real JWT tokens with proper authentication for ALL testing
- **User Quote**: "任何 API 測試，回覆 Now we're getting 401 (authentication required) 都是不能接受的，要測試就必須取得 token 測試!!!"

**FORBIDDEN Claims:**
- ❌ "The API now returns 401 instead of 500, so the fix works"
- ❌ "Both endpoints correctly respond with authentication required"
- ❌ "The enum bug is fixed" (based only on status code changes)
- ❌ "Now we're getting 401 (authentication required)" (without real token testing)

**REQUIRED Verification for API Fix Claims:**

#### 1. **Authenticate with Real Tokens** (MANDATORY)
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

#### 2. **Verify Real Data Responses**
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

#### 3. **Test Multiple User Types**
- Test with users having different plans (FREE, STUDENT, PRO)
- Verify each plan type returns correct data
- Document which users were tested and their plan types

#### 4. **Evidence-Based Claims Only**
```markdown
✅ ACCEPTABLE: "Tested with user howie.yu@gmail.com (STUDENT plan) - API returns complete plan data with display_name '學習方案'"

❌ UNACCEPTABLE: "Both endpoints now correctly return 401 instead of 500 errors"
```

#### 5. **Use Test Automation When Possible**
```python
# Create temporary auth tokens in test scripts
# Verify complete request/response cycles
# Test actual business logic, not just HTTP status
```

### Testing Token Management

**For API Testing:**
- Create temporary test tokens with limited scope
- Use test user accounts with known plan types
- Document which authentication method was used
- Clean up test tokens after verification

**Authentication Testing Levels:**
1. **Unauthenticated**: Should return 401
2. **Authenticated but wrong plan**: Should return appropriate data/limits
3. **Authenticated with test plan**: Should return real plan configuration data

### Mandatory Documentation for API Claims

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

## Key API Endpoints

```
Authentication:
POST /auth/google - Google SSO authentication

Sessions:
POST /sessions - Create transcription session
GET /sessions - List user sessions
GET /sessions/{id} - Get session details
POST /sessions/{id}/upload-url - Get signed upload URL
POST /sessions/{id}/start-transcription - Start processing
GET /sessions/{id}/transcript - Download transcript
PATCH /sessions/{id}/speaker-roles - Update speaker assignments

LeMUR Optimization:
POST /lemur-speaker-identification - Optimize speaker identification
POST /lemur-punctuation-optimization - Optimize punctuation
POST /session/{session_id}/lemur-speaker-identification - Database-based speaker optimization
POST /session/{session_id}/lemur-punctuation-optimization - Database-based punctuation optimization

Coaching Management:
GET /api/v1/clients - List clients
POST /api/v1/clients - Create client
GET /api/v1/coaching-sessions - List coaching sessions
POST /api/v1/coaching-sessions - Create session
```

## Plan Limitations & Features

The platform enforces different limits based on user subscription plans:

### File Size Limits
- **FREE Plan**: 60MB per file
- **PRO Plan**: 200MB per file
- **ENTERPRISE Plan**: 500MB per file

### Session & Transcription Limits
- **Database-driven**: All plan limits are stored in PostgreSQL and dynamically loaded
- **API Integration**: `/api/v1/plans/current` endpoint provides real-time limit information
- **Frontend Validation**: File upload component shows dynamic size limits based on user's plan
- **Backend Enforcement**: Plan validation occurs before processing to prevent overuse

### Dynamic Limit Display
The frontend automatically adapts to show the correct limits:
- AudioUploader component displays plan-specific file size limits
- Error messages include current plan context
- Billing pages show accurate feature comparisons per plan