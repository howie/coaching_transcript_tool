# Production Login Failure Fix Guide

**Date**: 2025-10-03
**Issue**: 404 errors on JavaScript chunks causing login failures
**Status**: ✅ Fixed

## 🔍 Root Cause Analysis

### Primary Issue
**Build/Deployment Synchronization Problem**: Next.js HTML references JavaScript chunk hashes that don't exist in deployed static assets.

### Error Signature
```
GET https://coachly.doxa.com.tw/_next/static/chunks/app/signup/page-9e8535ab586d093b.js
net::ERR_ABORTED 404 (Not Found)
```

### Root Causes Identified

1. **Unstable BUILD_ID Generation**
   - Previous: Used `Date.now()` which changes between builds
   - Problem: Different timestamps → Different chunk hashes
   - Impact: HTML references chunks that don't exist

2. **Two-Stage Build Without Verification**
   - `npm run build` → `.next/` directory
   - `npm run build:cf` → `.open-next/` directory
   - No verification step between stages

3. **Incomplete OpenNext Transformation**
   - OpenNext adapter may skip or incorrectly process certain chunks
   - No automated detection of missing files

## ✅ Implemented Solutions

### 1. Stabilized BUILD_ID Generation

**File**: `apps/web/next.config.js` (lines 98-126)

**Changes**:
- ✅ Use Git SHA as primary BUILD_ID (consistent across builds)
- ✅ Fallback to package version only (removed timestamp)
- ✅ Added clear logging for debugging

**Before**:
```javascript
return `v${require('./package.json').version}-${Date.now()}`
```

**After**:
```javascript
// Priority order:
// 1. CF_PAGES_COMMIT_SHA (production)
// 2. VERCEL_GIT_COMMIT_SHA (if migrating)
// 3. Local Git SHA (git rev-parse HEAD)
// 4. Package version only (no timestamp)
```

### 2. Added Chunk Verification Script

**File**: `apps/web/scripts/verify-chunks.js` (new)

**Features**:
- ✅ Compares `.next/static` with `.open-next/assets/_next/static`
- ✅ Verifies BUILD_ID consistency
- ✅ Detects missing chunks before deployment
- ✅ Provides actionable error messages

**Usage**:
```bash
cd apps/web && npm run verify:chunks
```

**Output Example**:
```
🔍 Starting chunk verification...

ℹ️ Found 46 chunks in Next.js build
ℹ️ Found 46 chunks in OpenNext output

✅ BUILD_ID verified: f0df151739c217a3f52ef7d77be7ee14c55c0e20
✅ All chunks verified successfully!
✅ Deployment package is ready

Deployment Summary:
  • BUILD_ID: f0df151739c217a3f52ef7d77be7ee14c55c0e20
  • Total chunks: 46
  • Ready for deployment: YES
```

### 3. Enhanced Deployment Process

**File**: `Makefile` (lines 134-162)

**Changes**:
- ✅ Added clean step before build (`npm run clean`)
- ✅ Integrated verification into deployment workflow
- ✅ Added post-deployment checklist
- ✅ Better progress indicators

**Updated Workflow**:
```bash
make deploy-frontend
# 1. Clean previous builds
# 2. Build Next.js application
# 3. Build Cloudflare Workers adapter
# 4. Verify chunk completeness (NEW)
# 5. Deploy to Cloudflare
```

### 4. Updated Package.json Scripts

**File**: `apps/web/package.json` (lines 6-20)

**Changes**:
```json
{
  "scripts": {
    "verify:chunks": "node scripts/verify-chunks.js",
    "deploy": "npm run build && npm run build:cf && npm run verify:chunks && npx wrangler deploy"
  }
}
```

## 🚀 Deployment Instructions

### Quick Deploy (Recommended)
```bash
# From project root
make deploy-frontend
```

This single command handles:
- Cleaning old builds
- Building Next.js app
- Building Cloudflare adapter
- Verifying chunks
- Deploying to production

### Manual Deploy (Debug Mode)
```bash
# Step 1: Clean
cd apps/web
npm run clean

# Step 2: Build Next.js
NODE_ENV=production NEXT_PUBLIC_API_URL=https://api.doxa.com.tw npm run build

# Step 3: Build Cloudflare adapter
npm run build:cf

# Step 4: Verify
npm run verify:chunks

# Step 5: Deploy (if verification passes)
npx wrangler deploy
```

### Emergency Rollback
If deployment fails:
```bash
# Check Cloudflare Workers dashboard for previous deployment
# Or deploy from known good commit:
git checkout <previous-working-commit>
make deploy-frontend
```

## 🔍 Verification & Testing

### After Deployment

1. **Check Build ID**:
   ```bash
   curl -s https://coachly.doxa.com.tw/_next/BUILD_ID
   ```

2. **Test Login Flow**:
   - Navigate to https://coachly.doxa.com.tw/login
   - Open browser DevTools (F12) → Console tab
   - Attempt login
   - Verify NO 404 errors for chunk files

3. **Test Navigation**:
   - Click "Sign up" link
   - Verify smooth navigation (no fallback to browser navigation)
   - Check console for "ChunkLoadError" messages

### Health Checks

```bash
# Frontend health
curl -I https://coachly.doxa.com.tw/

# API health
curl https://api.doxa.com.tw/api/health

# Check specific chunk (replace hash with actual from error)
curl -I https://coachly.doxa.com.tw/_next/static/chunks/app/signup/page-[hash].js
```

## 🐛 Troubleshooting

### Issue: Verification Fails with Missing Chunks

**Solution**:
```bash
# Clean everything and rebuild
cd apps/web
rm -rf .next .open-next .turbo node_modules/.cache
npm run build && npm run build:cf
npm run verify:chunks
```

### Issue: BUILD_ID Mismatch

**Symptom**: Verification script reports different BUILD_IDs

**Solution**:
1. Ensure Git working directory is clean: `git status`
2. Commit any changes: `git commit -m "fix: deployment"`
3. Rebuild: `npm run clean && npm run build && npm run build:cf`

### Issue: Still Getting 404s After Deployment

**Investigation Steps**:
1. Check Cloudflare Workers logs:
   ```bash
   cd apps/web
   npx wrangler tail
   ```

2. Verify assets uploaded:
   ```bash
   # Check local build
   ls -la .open-next/assets/_next/static/chunks/app/signup/

   # Compare with production
   curl -I https://coachly.doxa.com.tw/_next/static/chunks/app/signup/page-[hash].js
   ```

3. Clear Cloudflare cache:
   - Go to Cloudflare Dashboard
   - Select "Caching" → "Configuration"
   - Click "Purge Everything"

### Issue: OpenNext Build Fails

**Common Causes**:
- Node version incompatibility (ensure Node 18+)
- Insufficient memory
- File permission issues

**Solution**:
```bash
# Check Node version
node --version  # Should be v18 or higher

# Increase Node memory if needed
NODE_OPTIONS="--max-old-space-size=4096" npm run build:cf

# Check disk space
df -h
```

## 📊 Monitoring

### Key Metrics to Watch

1. **404 Error Rate**:
   - Monitor Cloudflare Analytics
   - Filter for `_next/static/chunks/*` paths

2. **Build Success Rate**:
   - Track successful chunk verifications
   - Monitor deployment failures

3. **User Impact**:
   - Login success rate
   - Session creation metrics
   - Bounce rate on login page

### Alerts to Set Up

- Cloudflare Workers error rate > 5%
- 404 rate spike on static assets
- Deployment failures
- BUILD_ID mismatches in logs

## 📝 Related Files

### Modified Files
- `apps/web/next.config.js` - Stable BUILD_ID generation
- `apps/web/package.json` - Added verification script
- `Makefile` - Enhanced deployment workflow

### New Files
- `apps/web/scripts/verify-chunks.js` - Chunk verification utility
- `docs/deployment/production-fix-guide.md` - This document

### Configuration Files (Unchanged)
- `apps/web/wrangler.toml` - Cloudflare Workers config
- `.github/workflows/ci-cd.yml` - CI/CD pipeline

## 🎯 Future Improvements

1. **Automated Testing**:
   - Add E2E tests for login flow
   - Verify chunk loading in CI/CD

2. **Build Monitoring**:
   - Track BUILD_ID across deployments
   - Alert on BUILD_ID changes without Git commit

3. **Deployment Pipeline**:
   - Add smoke tests after deployment
   - Implement blue-green deployment for zero-downtime

4. **Documentation**:
   - Add troubleshooting playbook
   - Document known OpenNext issues

## 📚 References

- [Next.js Build ID Documentation](https://nextjs.org/docs/app/api-reference/next-config-js/generateBuildId)
- [OpenNext Cloudflare Adapter](https://github.com/opennextjs/opennextjs-cloudflare)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)

---

**Last Updated**: 2025-10-03
**Maintainer**: DevOps Team
**Emergency Contact**: Check team escalation guide
