# Dashboard OAuth Authentication Fix Guide

**Date**: 2025-09-27
**Issue**: Frontend-Backend API Endpoint Path Mismatch
**Status**: 🔧 Fix Ready for Implementation

## 🚨 Problem Summary

The dashboard OAuth authentication is failing due to incorrect API endpoint paths between the frontend and backend. The frontend is calling authentication endpoints without the proper `/api/v1` prefix.

### Console Errors Observed
```bash
❌ POST http://localhost:8000/auth/refresh 404 (Not Found)
❌ GET http://localhost:8000/api/v1/user/profile net::ERR_FAILED 500 (Internal Server Error)
❌ Access to fetch blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

## 🔍 Root Cause Analysis

### Backend Configuration (✅ Verified Working)
- **Auth Router Mount Point**: `/api/v1/auth` (main.py:90)
- **CORS Configuration**: Properly configured with `http://localhost:3000` allowed
- **Available Endpoints**: All authentication routes functional

### Frontend Configuration (❌ Needs Fix)
- **Current Calls**: `/auth/refresh` (missing `/api/v1` prefix)
- **Expected Calls**: `/api/v1/auth/refresh`
- **Impact**: 404 errors causing authentication failures

## 🛠️ Fix Implementation Plan

### Option 1: Frontend API Client Update (Recommended)

#### Files to Modify
Look for these common frontend API client files:
- `apps/web/src/lib/api.ts`
- `apps/web/src/utils/api-client.ts`
- `apps/web/src/services/auth.ts`
- Any file containing API endpoint definitions

#### Required Changes

**1. Authentication Endpoint Updates**
```typescript
// ❌ BEFORE (Incorrect paths)
const authEndpoints = {
  refresh: '/auth/refresh',
  login: '/auth/login',
  me: '/auth/me',
  googleLogin: '/auth/google/login',
  googleCallback: '/auth/google/callback'
};

// ✅ AFTER (Correct paths)
const authEndpoints = {
  refresh: '/api/v1/auth/refresh',
  login: '/api/v1/auth/login',
  me: '/api/v1/auth/me',
  googleLogin: '/api/v1/auth/google/login',
  googleCallback: '/api/v1/auth/google/callback'
};
```

**2. API Base URL Configuration**
```typescript
// Ensure your API client is configured with the correct base URL
const API_BASE_URL = 'http://localhost:8000';

// Or use environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**3. Fetch Calls Update**
```typescript
// ❌ BEFORE
async function refreshToken(refreshToken: string) {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    // ... rest of config
  });
}

// ✅ AFTER
async function refreshToken(refreshToken: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    // ... rest of config
  });
}
```

### Option 2: Server Process Cleanup

```bash
# Kill all conflicting API server processes
pkill -f "uv run python apps/api-server/main.py"

# Wait a moment for processes to terminate
sleep 2

# Start single clean API server
uv run python apps/api-server/main.py
```

## ✅ Verified Working Backend Endpoints

All these endpoints are confirmed available and functional:

| Method | Endpoint | Purpose | File Reference |
|--------|----------|---------|----------------|
| `POST` | `/api/v1/auth/refresh` | Token refresh | auth.py:377 |
| `POST` | `/api/v1/auth/login` | User login | auth.py:185 |
| `GET` | `/api/v1/auth/me` | Get current user | auth.py:494 |
| `GET` | `/api/v1/auth/google/login` | Google OAuth start | auth.py:203 |
| `GET` | `/api/v1/auth/google/callback` | Google OAuth callback | auth.py:241 |
| `POST` | `/api/v1/auth/signup` | User registration | auth.py:140 |

## 🧪 Testing the Fix

### 1. Before Implementing
```bash
# Should return 404
curl -X POST http://localhost:8000/auth/refresh

# Should return 200 or proper auth response
curl -X POST http://localhost:8000/api/v1/auth/refresh
```

### 2. After Frontend Update
1. Start the API server: `uv run python apps/api-server/main.py`
2. Start the frontend: `cd apps/web && npm run dev`
3. Open browser console and check for:
   - ✅ No 404 errors on authentication endpoints
   - ✅ Successful token refresh calls
   - ✅ Proper user profile loading

### 3. Verification Checklist
- [ ] Dashboard loads without authentication errors
- [ ] OAuth login flow completes successfully
- [ ] Token refresh works automatically
- [ ] User profile data loads correctly
- [ ] No CORS errors in console

## 📋 Common Frontend Files to Check

Based on typical Next.js project structure, check these files:

```bash
# Search for auth endpoint references
grep -r "/auth/" apps/web/src/
grep -r "auth/refresh" apps/web/src/
grep -r "auth/login" apps/web/src/

# Look for API client configurations
find apps/web/src -name "*api*" -type f
find apps/web/src -name "*auth*" -type f
```

## 🚀 Expected Results After Fix

- **✅ Authentication Flow**: Complete OAuth login without errors
- **✅ Token Management**: Automatic token refresh working
- **✅ User Session**: Persistent login state
- **✅ API Calls**: All protected endpoints accessible
- **✅ Console Clean**: No 404 or CORS errors

## 📞 Support

If the fix doesn't resolve the issue, check:

1. **Network Tab**: Verify the actual URLs being called
2. **API Server Logs**: Check for any backend errors
3. **Environment Variables**: Ensure API_URL is correctly set
4. **Port Conflicts**: Make sure only one API server is running

---

**Note**: This fix addresses frontend-backend integration and does not affect the Clean Architecture migration, which remains 100% complete.