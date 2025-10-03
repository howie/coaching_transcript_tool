# Worktree: Google OAuth CSP Fix

**Created**: 2025-10-03
**Branch**: hotfix/google-oauth-csp-fix
**Base**: main (commit d08f8d9)
**Worktree Path**: /Users/howie/Workspace/github/coaching_transcript_tool-google-oauth-fix

---

## Purpose

Fix the Google OAuth login failure caused by Content Security Policy (CSP) conflicts between Next.js middleware and Google's authentication page.

### Issue Summary
- **Severity**: High - Blocks Google OAuth login functionality
- **Root Cause**: Next.js middleware applies CSP headers to OAuth redirect endpoints
- **Impact**: Google's inline scripts fail to execute, breaking login flow
- **Affected URL**: https://coachly.doxa.com.tw/api/proxy/v1/auth/google/login

### Reference Documentation
See: `docs/issues/google-oauth-csp-conflict.md`

---

## Recommended Solution

**Exclude OAuth routes from middleware matcher** (Option A from documentation)

### File to Modify
`apps/web/middleware.ts` - Line 66

### Required Change
Update matcher to exclude Google OAuth routes:

```typescript
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - images/ (public images)
     * - api/proxy/v1/auth/google/* (Google OAuth redirects) ← ADD THIS
     */
    '/((?!_next/static|_next/image|favicon.ico|images/|api/proxy/v1/auth/google/).*)',
  ],
}
```

---

## Development Setup Status

- ✅ Worktree created
- ✅ .env file created from template
- ✅ Next.js dependencies installed (apps/web/node_modules)
- ⚠️  Python virtual environment NOT created (not needed for this fix)
- ⚠️  Backend dependencies NOT installed (not needed for this fix)

---

## Testing Checklist

### 1. Local Testing
```bash
cd apps/web
npm run dev
```
- [ ] Navigate to http://localhost:3000/login
- [ ] Click "Google Login"
- [ ] Verify no CSP errors in console
- [ ] Verify Google login page loads correctly
- [ ] Complete OAuth flow successfully

### 2. Build Verification
```bash
cd apps/web
npm run build
```
- [ ] Build completes without errors
- [ ] No TypeScript errors
- [ ] No linting errors

### 3. Production Deployment Testing
```bash
cd apps/web
npm run build:cf
npm run deploy
```
- [ ] Test at: https://coachly.doxa.com.tw/login
- [ ] Open DevTools Console
- [ ] Click "Login with Google"
- [ ] Verify no CSP errors
- [ ] Complete login flow
- [ ] Verify redirect to dashboard

### 4. CSP Header Verification
```bash
# OAuth routes should NOT have CSP headers
curl -I https://coachly.doxa.com.tw/api/proxy/v1/auth/google/login

# Other routes SHOULD still have CSP headers
curl -I https://coachly.doxa.com.tw/
curl -I https://coachly.doxa.com.tw/dashboard
```

---

## Commit Message Template

```
fix(middleware): exclude Google OAuth routes from CSP middleware

Resolves production Google OAuth login failures caused by CSP conflicts.

Problem:
- Next.js middleware was applying CSP headers to OAuth redirect endpoints
- Google's authentication page has its own nonce-based CSP
- Our CSP headers conflicted with Google's, blocking inline scripts
- Result: Login flow failed with "Refused to execute inline script" errors

Solution:
- Exclude /api/proxy/v1/auth/google/* routes from middleware matcher
- Allows Google's OAuth pages to use their own CSP without conflicts
- No security impact (we don't serve these pages, only redirect to them)

Testing:
- ✅ Local development server: OAuth flow works
- ✅ Production deployment: No CSP errors in console
- ✅ Login flow completes successfully
- ✅ Other routes still have CSP headers applied

Fixes: Production Google SSO login failure
Ref: docs/issues/google-oauth-csp-conflict.md
```

---

## Post-Fix Actions

After successful deployment:
1. Update issue documentation status to "Fixed"
2. Test on all environments (staging/production)
3. Monitor error logs for any CSP-related issues
4. Clean up this worktree after merge
5. Delete remote branch after successful merge

---

## Cleanup Commands

When ready to remove this worktree:

```bash
# From main repository
cd /Users/howie/Workspace/github/coaching_transcript_tool

# Remove worktree
git worktree remove /Users/howie/Workspace/github/coaching_transcript_tool-google-oauth-fix

# Delete local branch (after merge)
git branch -D hotfix/google-oauth-csp-fix

# Delete remote branch (after merge)
git push origin --delete hotfix/google-oauth-csp-fix
```

---

## Notes

- This is a frontend-only fix (middleware.ts change)
- No database migrations required
- No backend changes needed
- Single file modification
- Low risk, high impact fix
- Can be deployed independently
