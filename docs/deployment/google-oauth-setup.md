# Google OAuth Setup Guide

**Date**: 2025-10-03
**Purpose**: Configure Google SSO (Single Sign-On) for production deployment
**Status**: ✅ Fixed and Documented

---

## 🔍 Issue Summary

### **Problem Identified**
Production Google SSO login was failing with CSP (Content Security Policy) violations and CORS errors:

```
Refused to set the document's base URI to 'https://accounts.google.com/v3/signin/'
because it violates the following Content Security Policy directive: "base-uri 'self'"

Access to script at 'https://www.gstatic.com/_/mss/boq-identity/...' blocked by CORS policy
```

### **Root Causes**
1. **Missing CSP Headers** - No middleware to allow Google OAuth domains
2. **Domain Mismatch** - Testing URL vs Production URL configuration
3. **Hardcoded Frontend URL** - Backend not using environment configuration

---

## ✅ Fixes Implemented

### 1. **Next.js Middleware with OAuth-Compatible CSP**

**File Created**: `apps/web/middleware.ts`

**Features**:
- ✅ Allows Google authentication domains
- ✅ Permits Google Analytics and Tag Manager
- ✅ Supports Font Awesome CDN
- ✅ Maintains security with restrictive defaults

**CSP Directives**:
```typescript
script-src: Self, Google Auth, Analytics, GTM
style-src: Self, Google, Fonts, CDN
connect-src: Self, Google APIs, Backend
frame-src: Google Auth pages
base-uri: 'self' (secure)
form-action: Self, Google Auth
```

### 2. **Backend OAuth Configuration**

**File Modified**: `src/coaching_assistant/api/v1/auth.py`

**Changes**:
- ✅ Uses `settings.FRONTEND_URL` instead of hardcoded URLs
- ✅ Supports multi-domain deployment
- ✅ Proper redirect handling

**Before**:
```python
frontend_url = (
    "https://coachly.doxa.com.tw"
    if settings.ENVIRONMENT == "production"
    else "http://localhost:3000"
)
```

**After**:
```python
# Use configured FRONTEND_URL for better multi-domain support
frontend_url = settings.FRONTEND_URL.rstrip('/')
```

### 3. **Environment Configuration**

**File**: `src/coaching_assistant/core/config.py`

**Existing Config** (already present):
```python
FRONTEND_URL: str = "http://localhost:3000"  # ✅ Already exists
GOOGLE_CLIENT_ID: str = ""
GOOGLE_CLIENT_SECRET: str = ""
```

---

## 🚀 Setup Instructions

### **Step 1: Google Cloud Console Configuration**

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/

2. **Create/Select Project**:
   - Project Name: "Coaching Transcript Tool" (or your project name)
   - Project ID: Note this for later

3. **Enable APIs**:
   ```
   APIs & Services → Library → Enable:
   - Google+ API
   - Google Identity
   ```

4. **Create OAuth 2.0 Credentials**:
   ```
   APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID

   Application type: Web application
   Name: Coaching Tool - Production

   Authorized JavaScript origins:
   - https://coachly.doxa.com.tw
   - http://localhost:3000 (for development)

   Authorized redirect URIs:
   - https://api.doxa.com.tw/api/v1/auth/google/callback
   - http://localhost:8000/api/v1/auth/google/callback (for development)
   ```

5. **Copy Credentials**:
   - Client ID: `xxxxx.apps.googleusercontent.com`
   - Client Secret: `GOCSPX-xxxxx`

### **Step 2: Backend Environment Variables**

**Production (.env or environment variables)**:
```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Frontend URL (CRITICAL for OAuth redirects)
FRONTEND_URL=https://coachly.doxa.com.tw

# Environment
ENVIRONMENT=production
```

**Development (.env.local)**:
```bash
# Google OAuth Configuration (same as production)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Environment
ENVIRONMENT=development
```

### **Step 3: Frontend Configuration**

**File**: `apps/web/.env.production`

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://api.doxa.com.tw

# Optional: Google Analytics
NEXT_PUBLIC_GA_ID=G-859X61KC45
```

### **Step 4: Deploy Changes**

```bash
# 1. Lint and format
uv run ruff format .
uv run ruff check . --fix

# 2. Test locally
make run-api          # Start backend
make dev-frontend     # Start frontend
# Test Google login at http://localhost:3000/login

# 3. Deploy to production
make deploy-frontend  # Deploy frontend to Cloudflare
# Deploy backend via your CI/CD or Terraform
```

---

## 🔒 Security Considerations

### **OAuth Token Transmission** ⚠️

**Current Method** (URL Parameters):
```
/dashboard?access_token=xxx&refresh_token=yyy
```

**Issues**:
- ❌ Tokens visible in browser history
- ❌ Tokens visible in server logs
- ❌ Potential MITM attacks

**Recommended Improvements** (Future):
1. **HttpOnly Cookies**:
   ```python
   response.set_cookie(
       key="access_token",
       value=access_token,
       httponly=True,
       secure=True,
       samesite="lax"
   )
   ```

2. **Authorization Code Flow with PKCE**:
   - Use state parameter for CSRF protection
   - Implement PKCE (Proof Key for Code Exchange)
   - Store tokens server-side

### **CSP Headers Best Practices**

✅ **Current Implementation**:
- Restrictive default-src
- Specific allowlist for Google services
- `base-uri 'self'` prevents injection attacks
- `object-src 'none'` blocks plugins

⚠️ **Known Trade-offs**:
- `'unsafe-inline'` in script-src for GTM/GA
- `'unsafe-eval'` for some third-party scripts

📝 **Future Improvements**:
- Use nonces for inline scripts
- Migrate to CSP Level 3
- Implement strict-dynamic

---

## 🧪 Testing Checklist

### **Local Development**

- [ ] Google OAuth button visible on `/login`
- [ ] Click redirects to `accounts.google.com`
- [ ] Google login page loads without CSP errors
- [ ] After authentication, redirects to `/dashboard`
- [ ] Access token present in URL parameters
- [ ] User logged in successfully
- [ ] Dashboard loads user data

### **Production**

- [ ] Access https://coachly.doxa.com.tw/login
- [ ] Click "Sign in with Google"
- [ ] No CSP violations in browser console
- [ ] No CORS errors
- [ ] Google authentication completes
- [ ] Redirect to dashboard succeeds
- [ ] User session persists across page refresh

### **Browser Console Checks**

**No errors should appear**:
```bash
# ✅ Should NOT see:
"Refused to set the document's base URI"
"Access to script... blocked by CORS policy"
"ChunkLoadError"

# ✅ Should see:
"Using Git SHA as Build ID"
"Using Next.js proxy for same-origin API requests"
```

---

## 🐛 Troubleshooting

### **Issue: "redirect_uri_mismatch" Error**

**Symptom**:
```
Error 400: redirect_uri_mismatch
The redirect URI in the request does not match the authorized redirect URIs
```

**Solution**:
1. Check Google Cloud Console → Credentials
2. Verify exact match (including trailing slash):
   ```
   Configured: https://api.doxa.com.tw/api/v1/auth/google/callback
   Actual:     https://api.doxa.com.tw/api/v1/auth/google/callback
   ```
3. Update redirect URI if needed
4. Wait 5 minutes for Google to propagate changes

### **Issue: CSP Violations Still Appearing**

**Symptom**:
```
Refused to load... because it violates the following CSP directive
```

**Solution**:
1. Check middleware is deployed:
   ```bash
   ls -la apps/web/middleware.ts
   ```

2. Verify CSP headers in browser:
   ```bash
   # Open DevTools → Network → Select any request → Headers
   # Look for: Content-Security-Policy
   ```

3. Rebuild and redeploy:
   ```bash
   make clean-frontend && make deploy-frontend
   ```

### **Issue: "origin" Error from Google**

**Symptom**:
```
That's an error.
Error: origin_mismatch
```

**Solution**:
1. Verify "Authorized JavaScript origins" in Google Console
2. Must match EXACTLY (no trailing slash):
   ```
   ✅ https://coachly.doxa.com.tw
   ❌ https://coachly.doxa.com.tw/
   ```

### **Issue: Wrong Frontend URL After Login**

**Symptom**: Redirects to wrong domain after authentication

**Solution**:
1. Check backend environment variable:
   ```bash
   echo $FRONTEND_URL
   # Should output: https://coachly.doxa.com.tw
   ```

2. Update `.env` or environment:
   ```bash
   FRONTEND_URL=https://coachly.doxa.com.tw
   ```

3. Restart backend:
   ```bash
   make run-api
   ```

---

## 📊 Monitoring & Alerts

### **Key Metrics to Track**

1. **OAuth Success Rate**:
   - Track `/api/v1/auth/google/callback` success vs errors
   - Alert if success rate drops below 95%

2. **CSP Violations**:
   - Monitor browser console errors
   - Set up CSP reporting endpoint

3. **User Login Flow**:
   - Track Google login button clicks
   - Monitor redirect completion
   - Measure authentication latency

### **Logging Recommendations**

**Backend** (`auth.py`):
```python
# Add structured logging
logger.info("Google OAuth initiated", extra={
    "redirect_uri": redirect_uri,
    "environment": settings.ENVIRONMENT
})

logger.info("Google OAuth callback received", extra={
    "user_email": email,
    "is_new_user": existing_user is None
})
```

**Frontend** (Analytics):
```javascript
// Track OAuth events
gtag('event', 'google_login_initiated')
gtag('event', 'google_login_success', { user_id: userId })
gtag('event', 'google_login_failed', { error: errorMessage })
```

---

## 📝 Related Files

### **Modified Files**
- ✅ `apps/web/middleware.ts` - Created CSP headers
- ✅ `src/coaching_assistant/api/v1/auth.py` - Updated OAuth redirect logic

### **Configuration Files**
- `src/coaching_assistant/core/config.py` - Environment variables
- `apps/web/next.config.js` - Next.js configuration
- `apps/web/wrangler.toml` - Cloudflare Workers config

### **Documentation**
- `docs/deployment/google-oauth-setup.md` - This guide
- `docs/deployment/production-fix-guide.md` - Chunk loading fix

---

## 🎯 Future Enhancements

1. **Security Improvements**:
   - [ ] Implement HttpOnly cookies for tokens
   - [ ] Add PKCE to OAuth flow
   - [ ] Use CSP nonces instead of unsafe-inline
   - [ ] Add state parameter for CSRF protection

2. **User Experience**:
   - [ ] Add loading spinner during OAuth redirect
   - [ ] Handle OAuth errors gracefully
   - [ ] Remember user's intended destination
   - [ ] Add "Continue with Google" branding

3. **Multi-Provider Support**:
   - [ ] Add Microsoft/Azure AD
   - [ ] Add Apple Sign-In
   - [ ] Add GitHub OAuth

4. **Monitoring**:
   - [ ] Set up CSP violation reporting
   - [ ] Add OAuth flow analytics
   - [ ] Create authentication dashboard

---

## 📚 References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Content Security Policy Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Next.js Middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [Cloudflare Workers Security](https://developers.cloudflare.com/workers/runtime-apis/web-standards/)

---

**Last Updated**: 2025-10-03
**Maintainer**: DevOps Team
**Emergency Contact**: Check team escalation guide
