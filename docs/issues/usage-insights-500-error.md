# Usage Insights API 500 Internal Server Error

## Issue Summary
The usage insights API endpoint is returning a 500 Internal Server Error, preventing users from viewing their usage statistics and insights.

**Error**: `GET http://localhost:3000/api/proxy/v1/usage/insights 500 (Internal Server Error)`

## Environment
- **Page**: Dashboard (likely usage/analytics page)
- **Component**: `UsageHistory.tsx`
- **Authentication**: Token present ✅
- **Error Location**: `UsageHistory.tsx:189` calling `ApiClient.getUsageInsights`

## Error Stack Trace
```
GET /v1/usage/insights error: Error: Failed to generate usage insights
    at ApiClient.get (api.ts:298:15)
    at async ApiClient.getUsageInsights (api.ts:1869:14)
    at async eval (UsageHistory.tsx:189:24)
```

## Root Cause Analysis

### Request Flow
1. **Frontend**: `UsageHistory.tsx:189` → `ApiClient.getUsageInsights()`
2. **API Client**: `api.ts:1869` → `ApiClient.get()`
3. **Fetch Wrapper**: `api.ts:298` → Throws error
4. **Backend**: `/api/v1/usage/insights` → 500 Internal Server Error

### Problem
The backend endpoint `/api/v1/usage/insights` is failing with an internal server error, indicating:
- Database query issue
- Data processing/aggregation failure
- Missing error handling in the endpoint
- Authentication/authorization problem (less likely since token is present)

## Impact
- **Severity**: High
- **User Impact**: Cannot view usage statistics and insights
- **Functionality**: Complete failure of usage insights feature
- **Business Impact**: Users cannot track their API usage, transcription credits, etc.

## Related Files
- `/apps/web/app/dashboard/usage/UsageHistory.tsx:189` - Frontend component
- `/apps/web/lib/api.ts:1869` - API client method
- `/apps/web/lib/api.ts:298` - Fetch wrapper error handling
- Backend API route for `/api/v1/usage/insights` - Server-side error

## Investigation Needed

### 1. Backend Logs
```bash
# Check backend logs for detailed error
grep -r "usage/insights" logs/
# Or run API server with debug logging
TEST_MODE=true uv run python apps/api-server/main.py
```

### 2. Database Query
- Check if usage insights query is failing
- Verify database schema for usage tracking tables
- Test query independently

### 3. API Endpoint Code
- Review `/api/v1/usage/insights` implementation
- Check for missing try/catch blocks
- Verify data aggregation logic

### 4. Test with Auth Token
```bash
# Get actual auth token and test endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/usage/insights
```

## Error Handling Issues

### Current Implementation (api.ts:298)
```typescript
// api.ts:298 - Throws generic error
throw new Error('Failed to generate usage insights')
```

### Problems
1. Generic error message loses backend error details
2. No retry logic for transient failures
3. No fallback UI for users

## Possible Solutions

### Short-term (Error Handling)
1. Improve error handling in `api.ts:298` to preserve backend error details
2. Add user-friendly error message in `UsageHistory.tsx`
3. Implement loading states and error boundaries

### Long-term (Root Cause)
1. Fix the backend `/api/v1/usage/insights` endpoint
2. Add comprehensive error logging
3. Implement retry logic with exponential backoff
4. Add endpoint monitoring/alerting

## Next Steps
1. ✅ Document the issue
2. ⬜ Run API server and reproduce error with debug logging
3. ⬜ Check backend implementation of `/api/v1/usage/insights`
4. ⬜ Identify root cause (DB query, data processing, etc.)
5. ⬜ Fix backend endpoint
6. ⬜ Improve frontend error handling
7. ⬜ Add integration tests
8. ⬜ Verify fix on billing/usage pages

## Testing Checklist
- [ ] Backend logs show detailed error cause
- [ ] Endpoint returns 200 with valid data
- [ ] Frontend displays usage insights correctly
- [ ] Error states show user-friendly messages
- [ ] Integration tests cover success and failure cases

## Status
🔴 **ACTIVE** - Requires immediate attention (500 error)

---
*Created: 2025-10-03*
*Priority: HIGH*
*Branch: hotfix/production-plan-fail*
