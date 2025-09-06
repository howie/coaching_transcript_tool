# Mixed Content Error - Final Resolution ✅

## Problem Summary
Production site (https://coachly.doxa.com.tw) was experiencing Mixed Content errors where HTTPS pages were making HTTP requests to api.doxa.com.tw, causing browser security blocks.

## Root Cause Analysis
1. **Backend Redirect Loop**: Render backend was redirecting HTTPS → HTTP with trailing slashes
2. **Client-Side Enforcement Insufficient**: Trying to fix at fetch wrapper level was too late
3. **Cross-Origin Issues**: Direct API calls from browser created CORS and protocol mismatch

## Solution Implemented (2025-09-06)

### Phase 1: Next.js Rewrites (根本解決方案) ✅
```javascript
// next.config.js
async rewrites() {
  return [
    {
      source: '/api/proxy/:path*',
      destination: 'https://api.doxa.com.tw/api/:path*',
    },
  ]
}
```

### Phase 2: Update Components to Use Proxy ✅
```typescript
// ECPayStatus.tsx - Use relative paths through proxy
const healthResponse = await fetch('/api/proxy/health', {
  method: 'GET',
  cache: 'no-store', // Real-time health check
})
```

### Phase 3: Enhanced Fetch Wrapper ✅
- Supports Request/URL/string input types
- Preserves method, headers, body for Request objects
- Fail-fast in production for insecure URLs
- SSR/Node environment support

### Phase 4: Prevention Mechanisms ✅
- ESLint rule to block `http://api.doxa.com.tw`
- E2E tests to verify no HTTP requests
- Removed problematic trailing slash normalization

## Key Learnings

### 1. Architecture Matters
- **Lesson**: Proxy pattern (Next.js rewrites) is superior to client-side URL manipulation
- **Why**: Solves the problem at infrastructure level, not application level

### 2. Don't Over-Engineer
- **Lesson**: Trailing slash normalization created more problems than it solved
- **Why**: Backend should handle URL normalization, not frontend

### 3. Fail-Fast in Production
- **Lesson**: Throw errors immediately for insecure calls in production
- **Why**: Better to fail loudly than silently make insecure requests

### 4. Consider All Environments
- **Lesson**: Don't just fix browser environment, handle SSR/Node too
- **Why**: Next.js runs code in multiple environments

### 5. Request Object Handling
- **Lesson**: When wrapping fetch, preserve all Request properties
- **Why**: Losing method/headers/body breaks API calls

## Testing Checklist
- [x] No `http://api.doxa.com.tw` in Network tab
- [x] No Mixed Content warnings in Console
- [x] ECPay status check working on billing page
- [x] All API calls functioning normally
- [x] ESLint catches insecure URLs
- [x] E2E tests pass

## Files Modified
1. `/apps/web/next.config.js` - Added rewrites
2. `/apps/web/components/billing/ECPayStatus.tsx` - Use proxy paths
3. `/apps/web/lib/api.ts` - Enhanced fetch wrapper, removed trailing slash logic
4. `/apps/web/.eslintrc.json` - Added security rule
5. `/apps/web/__tests__/e2e/no-insecure-requests.spec.ts` - E2E tests

## Previous Failed Attempts
1. ~~Force HTTPS in baseUrl getter~~ - Too late in request cycle
2. ~~Add trailing slashes~~ - Caused more redirects
3. ~~Simple string replacement~~ - Didn't handle Request objects
4. ~~Browser-only fix~~ - Missed SSR/Node environments
5. ~~Aggressive URL normalization~~ - Broke other API calls
6. ~~Client-side enforcement only~~ - Couldn't catch all cases

## Final Architecture
```
Browser → Next.js Server (rewrites) → HTTPS API
   ↓           ↓                          ↓
/api/proxy/* → Proxy Layer → https://api.doxa.com.tw/api/*
```

## Deployment Notes
- No backend changes required
- Cloudflare Workers handles Next.js rewrites
- Immediate effect after deployment
- No database migrations needed

## References
- [ChatGPT Analysis](./mixed-content-error-tracking.md)
- [Next.js Rewrites Documentation](https://nextjs.org/docs/api-reference/next.config.js/rewrites)
- [Mixed Content MDN](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)

## Credits
Solution developed with guidance from ChatGPT's architectural review and implemented by Claude.

---
*Resolution Date: 2025-09-06*
*Status: RESOLVED ✅*