# Google OAuth Middleware CSP Fix

**Date**: 2025-10-03
**Issue**: Google OAuth login fails due to Next.js proxy intercepting OAuth redirects
**Status**: ✅ Fixed
**Version**: v2.25.2 (pending)

## Problem Summary

### Symptoms
- Users unable to login with Google OAuth on production (`https://coachly.doxa.com.tw`)
- CSP violations showing Google's auth page served from wrong domain
- Error: `Refused to set the document's base URI to 'https://accounts.google.com/v3/signin/'`
- Console errors about CSP violations and CORS policy blocks

### Root Cause

**TWO ISSUES FOUND**:

#### Issue #1: CSP Middleware Applied to API Routes ✅ FIXED

The Next.js middleware was applying CSP headers to all routes including OAuth endpoints.

**Broken Matcher Pattern** (commit 07686ff):
```typescript
'/((?!_next/static|_next/image|favicon.ico|images/|api/proxy/v1/auth/google/).*)'
```

**Why It Failed**:
- Negative lookahead pattern doesn't properly exclude entire API path tree
- API routes were receiving CSP headers unnecessarily

#### Issue #2: Next.js Rewrites Intercepting OAuth Redirects ⚠️ CRITICAL

**The Real Problem**: Next.js `rewrites()` in `next.config.js` don't follow HTTP 302 redirects - they **proxy the response content**.

When frontend code calls `/api/proxy/v1/auth/google/login`:
1. Next.js rewrites route to backend `https://api.doxa.com.tw/api/v1/auth/google/login`
2. Backend returns HTTP 302 redirect to `https://accounts.google.com/o/oauth2/v2/auth`
3. **Instead of following redirect**, Next.js fetches Google's login page HTML
4. Next.js serves Google's page from your domain (`https://coachly.doxa.com.tw/...`)
5. Google's inline scripts violate your CSP policy
6. **OAuth breaks with CSP violations**

**Evidence**:
```
Refused to set the document's base URI to 'https://accounts.google.com/v3/signin/'
because it violates the following Content Security Policy directive: "base-uri 'self'".

POST https://coachly.doxa.com.tw/v3/signin/_/AccountsSignInUi/cspreport 404 (Not Found)
```

This shows Google's auth page (`/v3/signin/`) being served from your domain!

## Solution

### Fix #1: Middleware Matcher Pattern ✅

**apps/web/middleware.ts** (line 67):
```typescript
// Before (broken):
'/((?!_next/static|_next/image|favicon.ico|images/|api/proxy/v1/auth/google/).*)'

// After (fixed):
'/((?!api)(?!_next/static)(?!_next/image)(?!favicon.ico)(?!images/).*)'
```

**Rationale**:
- Exclude **entire** `/api/*` path tree from CSP middleware
- API routes handle their own security headers
- Simpler pattern, easier to understand and maintain

### Fix #2: Direct Backend URLs for OAuth ⚠️ CRITICAL

**apps/web/app/login/page.tsx** and **apps/web/app/signup/page.tsx**:

```typescript
// Before (broken - uses Next.js proxy):
const handleGoogleLogin = () => {
  const baseUrl = apiClient.getBaseUrl()  // Returns '/api/proxy'
  window.location.href = `${baseUrl}/v1/auth/google/login`
}

// After (fixed - bypasses Next.js proxy):
const handleGoogleLogin = () => {
  // MUST use direct backend URL to allow browser to follow OAuth redirects
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL ||
                     process.env.NEXT_PUBLIC_API_URL ||
                     'https://api.doxa.com.tw'
  window.location.href = `${backendUrl}/api/v1/auth/google/login`
}
```

**Why This Is Critical**:
- OAuth REQUIRES browser navigation redirects (HTTP 302)
- Next.js rewrites intercept these redirects and proxy the content
- For OAuth, frontend MUST connect directly to backend
- Regular API calls can still use Next.js proxy for same-origin benefits

### Verification

After the fix, API routes are properly excluded:

```bash
$ curl -I http://localhost:3000/login
content-security-policy: default-src 'self'; ...
# ✅ CSP applied to login page

$ curl -I http://localhost:3000/api/proxy/v1/auth/google/login
HTTP/1.1 500 Internal Server Error
# ✅ NO CSP headers - middleware bypassed correctly
```

## Deployment Process

### 1. Testing Locally

```bash
cd apps/web

# Start Next.js dev server
npm run dev

# Verify CSP exclusion
curl -I http://localhost:3000/login | grep content-security-policy
# Should show CSP headers

curl -I http://localhost:3000/api/proxy/v1/auth/google/login | grep content-security-policy
# Should NOT show CSP headers

# Test Google OAuth flow manually
open http://localhost:3000/login
# Click "Sign in with Google" and complete auth flow
```

### 2. Building for Production

```bash
cd apps/web

# Clean previous builds
npm run clean

# Build Next.js
npm run build

# Build for Cloudflare Workers
npm run build:cf

# Verify chunks (optional but recommended)
npm run verify:chunks
```

### 3. Deploy to Cloudflare Pages

```bash
# Option A: Manual deployment via Cloudflare dashboard
# 1. Go to Cloudflare Pages dashboard
# 2. Upload .open-next directory

# Option B: Using wrangler CLI
cd apps/web
npx wrangler pages deploy .open-next --project-name=coachly-frontend
```

### 4. Verification in Production

```bash
# Check CSP headers on login page (should have CSP)
curl -I https://coachly.doxa.com.tw/login | grep -i content-security

# Check OAuth endpoint (should NOT have CSP)
curl -I https://coachly.doxa.com.tw/api/proxy/v1/auth/google/login | grep -i content-security

# Test OAuth flow end-to-end
# Visit https://coachly.doxa.com.tw/login
# Click "使用 Google 登入" button
# Complete authentication
# Should redirect back to /dashboard successfully
```

## Technical Details

### OAuth Flow Affected Routes

1. **`/api/proxy/v1/auth/google/login`**
   - Initiates OAuth flow
   - Redirects user to Google's authentication page
   - Must NOT have CSP headers

2. **`/api/proxy/v1/auth/google/callback`**
   - Handles Google's redirect after authentication
   - Exchanges authorization code for access token
   - Creates user session
   - Must NOT have CSP headers

### Why CSP Breaks OAuth

When Next.js middleware applies CSP headers to OAuth endpoints:
- Our CSP policy conflicts with Google's authentication page CSP
- Google's inline scripts and dynamic content fail to execute
- Authentication flow fails silently or with cryptic errors
- User sees blank page or redirect loops

### Previous Attempts

**Commit d08f8d9** (2025-10-03):
- Introduced CSP middleware for security
- Applied to all routes
- Broke Google OAuth

**Commit 07686ff** (2025-10-03):
- Attempted to fix by excluding `api/proxy/v1/auth/google/`
- Used incorrect regex pattern
- OAuth still broken

**Current Fix** (2025-10-03):
- Properly excludes entire `/api/*` tree
- OAuth flow restored
- Maintains CSP protection for frontend pages

## Related Files

- `apps/web/middleware.ts` - Next.js middleware configuration
- `apps/web/app/login/page.tsx` - Login page with Google OAuth button
- `apps/web/lib/api.ts` - API client with OAuth URL construction
- `src/coaching_assistant/api/v1/auth.py` - Backend OAuth endpoints

## Lessons Learned

1. **Next.js rewrites don't follow HTTP redirects**
   - Rewrites proxy response content, not redirect locations
   - OAuth flows MUST use direct backend URLs
   - Only use Next.js proxy for regular API calls

2. **Test OAuth flows thoroughly after infrastructure changes**
   - Verify redirects work in both dev and production
   - Check browser console for CSP violations
   - Test end-to-end authentication flow

3. **Understand middleware matcher patterns**
   - Negative lookaheads can be tricky
   - Simple exclusions are better than complex patterns
   - Document the intent clearly in comments

4. **OAuth is special**
   - Requires browser navigation (not fetch/AJAX)
   - Can't be proxied through Next.js rewrites
   - Must handle CORS properly for cross-origin redirects

5. **CSP debugging tips**
   - Browser console shows which policy is violated
   - Check `base-uri` violations - indicate wrong origin
   - 404s on `/cspreport` endpoints = CSP from wrong domain

## References

- [Next.js Middleware Documentation](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [Content Security Policy (CSP) Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
