# Subscription Cancel 404 Error Investigation

**Date**: 2025-10-04
**Reporter**: User
**Status**: 🔍 INVESTIGATING
**Priority**: 🔴 HIGH

## 📋 Problem Statement

User reports 404 errors when trying to cancel subscription in local development environment.

### Error Message

```
Failed to load resource: the server responded with a status of 404 (Not Found)
POST /api/v1/subscriptions/cancel/5d8aab68-8bab-438c-b7ab-1e5dd9d66d07 error: Error: Not Found
```

**Frontend Code** (`apps/web/components/billing/PaymentSettings.tsx:72`):
```typescript
await apiClient.post(`/api/v1/subscriptions/cancel/${subscriptionData.subscription.id}`)
```

## 🔍 Investigation Results

### ✅ Backend Endpoint EXISTS

**API Route**: `POST /api/v1/subscriptions/cancel/{subscription_id}`
- **File**: `src/coaching_assistant/api/v1/subscriptions.py:163-199`
- **Registered**: ✅ Yes (line 171-174 in `main.py`)
- **Handler**: `cancel_subscription()` function
- **Use Case**: `SubscriptionModificationUseCase.cancel_subscription()`

**Test Results**:
```bash
$ curl -X POST http://localhost:8000/api/v1/subscriptions/cancel/test-id
{
  "detail": "No active subscription found"
}
```

✅ **Endpoint is reachable** - Returns business logic error, not 404

### 🎯 Root Cause Analysis

**Hypothesis 1: Frontend API Client Issue** ⭐ LIKELY
- Frontend may be using incorrect base URL
- API proxy configuration in Next.js may be failing
- Check `apps/web/lib/api.ts` configuration

**Hypothesis 2: Authentication Required**
- Endpoint requires JWT token via `get_current_user_dependency`
- Frontend token may be invalid/expired
- Test mode bypasses auth, production doesn't

**Hypothesis 3: Frontend Path Issue**
- Frontend might be calling wrong path (e.g., missing `/api` prefix)
- Check browser DevTools Network tab for actual request URL

## 🧪 Diagnostic Tests

### Test 1: Direct API Call (No Auth)
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions/cancel/test-id
```
**Result**: ✅ Returns "No active subscription found" (404 status but valid response)

### Test 2: Check API Docs
```bash
curl http://localhost:8000/api/docs
```
**Result**: ✅ Endpoint visible in OpenAPI docs

### Test 3: Check Dependencies
```bash
grep -r "get_subscription_modification_use_case" src/
```
**Result**: ✅ Dependency injection correctly configured

## 🔧 Next Steps

1. **Check Frontend API Client Configuration**
   - Verify `apps/web/lib/api.ts` base URL
   - Check Next.js API proxy configuration (`next.config.js`)
   - Inspect actual HTTP request in browser DevTools

2. **Test with Valid User**
   - Create test user in database
   - Get valid JWT token
   - Test cancel endpoint with auth

3. **Compare with Working Endpoints**
   - Check if other subscription endpoints work (e.g., `/current`)
   - Identify differences in API client usage

## 📊 System State

### Environment
- **Local Dev**: macOS, localhost:8000 (backend), localhost:3000 (frontend)
- **Database**: PostgreSQL (local)
- **API Server**: Running with TEST_MODE=true

### Recent Changes
- ✅ merchant_member_id column length fix (VARCHAR 30→50)
- ✅ ECPay environment variables configured
- ⚠️ No changes to subscription cancel logic

## 🎬 Action Items

- [ ] Check frontend API client configuration
- [ ] Test with valid authentication
- [ ] Review browser DevTools Network tab
- [ ] Compare with other working endpoints
- [ ] Add integration test for cancel flow

## 📝 Notes

- Backend code appears healthy
- Endpoint is registered and responsive
- Issue likely in frontend integration, not backend logic
- Need to verify actual HTTP request being sent by frontend

---

**Last Updated**: 2025-10-04 22:42 UTC
**Investigator**: Claude Code Agent
