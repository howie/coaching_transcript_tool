# ECPay Webhook Health Check 404 Error

## Issue Summary
The ECPay status component on the billing page is trying to access a webhook health endpoint that doesn't exist, resulting in a 404 error.

**Error**: `GET http://localhost:3000/api/proxy/webhooks/health 404 (Not Found)`

## Environment
- **Page**: `/dashboard/billing`
- **Component**: `ECPayStatus.tsx`
- **Authentication**: Token present ✅
- **Error Location**: `ECPayStatus.tsx:33` in `checkECPayStatus` function

## Root Cause Analysis

### Current Implementation
```typescript
// ECPayStatus.tsx:33
const healthResponse = await fetch('/api/proxy/webhooks/health', {
  method: 'GET',
  cache: 'no-store',
})
```

### Problem
The endpoint `/api/proxy/webhooks/health` does not exist in the backend API routes.

### Expected Behavior
Either:
1. The endpoint should exist and return ECPay webhook service health status, OR
2. The component should use a different endpoint that actually exists

## Impact
- **Severity**: Medium
- **User Impact**: ECPay status check fails silently on billing page
- **Functionality**: Prevents users from seeing ECPay service health status
- **Performance**: Unnecessary 404 errors in console (non-breaking)

## Related Files
- `/apps/web/components/billing/ECPayStatus.tsx:33` - Health check call
- `/apps/web/next.config.js` - Proxy configuration
- Backend API routes - Missing webhook health endpoint

## Investigation Needed
1. Check if `/api/webhooks/health` endpoint exists in backend
2. Verify correct proxy path in `next.config.js`
3. Determine if webhook health check is still needed for ECPay status

## Possible Solutions

### Option 1: Add Missing Endpoint
Create `/api/webhooks/health` endpoint in backend that returns:
```json
{
  "status": "healthy",
  "service": "ecpay-webhooks",
  "timestamp": "2025-10-03T..."
}
```

### Option 2: Use Existing Endpoint
Replace with an existing health check endpoint (e.g., `/api/health`)

### Option 3: Remove Health Check
If ECPay status doesn't require webhook health check, remove this call

## Next Steps
1. ✅ Document the issue
2. ⬜ Verify backend API routes
3. ⬜ Determine correct endpoint or implement missing one
4. ⬜ Update ECPayStatus component
5. ⬜ Test on billing page
6. ⬜ Add integration test for endpoint

## Status
🔴 **ACTIVE** - Awaiting investigation

---
*Created: 2025-10-03*
*Branch: hotfix/production-plan-fail*
