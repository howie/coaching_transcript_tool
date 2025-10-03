# Usage Insights API - Schema Migration Required

## Feature Status
🚧 **In Development** - This feature is currently under development and hidden from production users.

**Frontend Visibility**: Usage history tab only visible in `NODE_ENV=development` with "DEV" label.

## Issue Summary
The usage insights API endpoint is returning a 500 Internal Server Error, preventing the feature from working properly.

**Error**: `GET http://localhost:3000/api/proxy/v1/usage/insights 500 (Internal Server Error)`

## Environment
- **Page**: Dashboard billing page → Usage History tab (dev only)
- **Component**: `UsageHistory.tsx`
- **Authentication**: Token present ✅
- **Error Locations**:
  - `UsageHistory.tsx:189` calling `ApiClient.getUsageInsights`
  - `UsageHistory.tsx:219` calling `ApiClient.getUsagePredictions`

## Error Stack Traces

### 1. Usage Insights Error
```
GET /v1/usage/insights error: Error: Failed to generate usage insights
    at ApiClient.get (api.ts:298:15)
    at async ApiClient.getUsageInsights (api.ts:1869:14)
    at async eval (UsageHistory.tsx:189:24)
```

### 2. Usage Predictions Error
```
GET /v1/usage/predictions error: Error: Failed to generate usage predictions
    at ApiClient.get (api.ts:298:15)
    at async ApiClient.getUsagePredictions (api.ts:1878:14)
    at async eval (UsageHistory.tsx:219:27)
```

Both endpoints fail with same root cause: **Database schema mismatch**

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

## Root Cause Identified

### Issue #1: Missing Repository Method
- Use case calls `get_by_user_and_date_range()`
- Repository only implements `get_by_user_id()`
- **Fix**: Added method alias in `usage_log_repository.py:120`

### Issue #2: Database Schema Mismatch (BLOCKING)
```
ERROR: column usage_logs.billable does not exist
ERROR: column usage_logs.cost_cents does not exist
```

**Database has**: `cost_usd`, `processing_duration_seconds`, `session_duration_seconds`
**Model expects**: `cost_cents`, `billable`, `processing_time_seconds`

This is a **critical schema migration issue** - the database schema is out of sync with ORM models.

## Temporary Workarounds Applied

### 1. Added Missing Repository Method
```python
# usage_log_repository.py:120
def get_by_user_and_date_range(self, user_id, start_date, end_date):
    return self.get_by_user_id(user_id, start_date, end_date)
```

### 2. Made ORM Model Tolerant (Temporary)
```python
# usage_log_model.py:55 - Commented out missing column
# billable = Column(Boolean, default=True, nullable=False)

# usage_log_model.py:97 - Use getattr with default
billable=getattr(self, 'billable', True)
```

## Permanent Solution Required

### Database Migration Needed
Create Alembic migration to:
1. Add `billable` column (Boolean, default True)
2. Rename `cost_usd` → `cost_cents` (or update models to match DB)
3. Rename `processing_duration_seconds` → `processing_time_seconds`
4. Handle data conversion (USD to cents if renaming)

### Migration Script Location
```
migrations/versions/XXXX_add_billable_and_fix_cost_columns.py
```

## Status
🟡 **PARTIALLY RESOLVED** - Workarounds in place, requires database migration

---
*Created: 2025-10-03*
*Investigated: 2025-10-03*
*Priority: HIGH - Schema mismatch blocks production usage insights*
*Branch: hotfix/production-plan-fail*

## Files Modified (Temporary Workarounds)
1. `src/coaching_assistant/infrastructure/db/repositories/usage_log_repository.py` - Added method, commented billable filter
2. `src/coaching_assistant/infrastructure/db/models/usage_log_model.py` - Made billable column optional with getattr defaults
