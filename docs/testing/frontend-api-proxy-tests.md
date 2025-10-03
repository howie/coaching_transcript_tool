# Frontend API Proxy Testing Suite

**Date**: 2025-10-03
**Purpose**: Protect against API path errors in proxy architecture
**Context**: After implementing Next.js API proxy, discovered duplicate `/api` path bug

---

## Problem Discovered

### Bug Description
Login and signup pages were generating incorrect Google OAuth URLs:
```
❌ Wrong: http://localhost:3000/api/proxy/api/v1/auth/google/login
                                        ^^^^ duplicate /api
```

**Root Cause**:
- `apiClient.getBaseUrl()` now returns `/api/proxy` (relative path)
- Code was still concatenating `/api/v1/...` (old pattern for absolute URLs)
- Result: `/api/proxy` + `/api/v1/...` = duplicate `/api` segment

**Impact**:
- 404 errors on Google OAuth login
- Broken authentication flow
- Poor user experience

---

## Solution Implemented

### 1. Created Comprehensive Test Suite

#### Test Files Created

**`apps/web/__tests__/lib/api-client.test.ts`** (9 tests)
- ✅ Validates `getBaseUrl()` behavior in browser vs SSR
- ✅ Ensures NO duplicate `/api` segments in paths
- ✅ Tests multi-domain support
- ✅ Validates path construction patterns

**`apps/web/__tests__/pages/auth/google-oauth-paths.test.ts`** (10 tests)
- ✅ Google OAuth URL generation
- ✅ OAuth callback URL generation
- ✅ Multi-environment support (dev, production, new domains)
- ✅ Regression tests for known bugs
- ✅ Path validation helpers

**`apps/web/__tests__/integration/api-paths.test.ts`** (9 tests)
- ✅ Validates ALL 40+ API endpoints used in app
- ✅ Path format validation (no duplicates, correct structure)
- ✅ Next.js rewrite compatibility
- ✅ Consistency checks (lowercase, kebab-case)
- ✅ Critical endpoints validation

**`apps/web/__tests__/regression/api-proxy-paths.test.ts`** (14 tests)
- ✅ Documents Bug #1: Duplicate /api in Google OAuth URL
- ✅ Documents Bug #2: Hard-coded domain checks
- ✅ Documents Bug #3: CORS errors on production
- ✅ Documents Bug #4: Service layer /api prefix errors
- ✅ Bug prevention patterns
- ✅ Documentation of correct usage

### 2. Fixed Application Code

**`apps/web/app/login/page.tsx`** (line 20-21)
```typescript
// Before
const baseUrl = apiClient.getBaseUrl() || ...complex fallback...
window.location.href = `${baseUrl}/api/v1/auth/google/login`  // ❌ Wrong

// After
const baseUrl = apiClient.getBaseUrl()
window.location.href = `${baseUrl}/v1/auth/google/login`  // ✅ Correct
```

**`apps/web/app/signup/page.tsx`** (line 27-28)
```typescript
// Before
window.location.href = `${baseUrl}/api/v1/auth/google/login`  // ❌ Wrong

// After
window.location.href = `${baseUrl}/v1/auth/google/login`  // ✅ Correct
```

---

## Test Results

### All Tests Passing ✅

```bash
# API Client Tests
npm test -- __tests__/lib/api-client.test.ts
✓ 9 passed, 9 total (0.474s)

# Google OAuth Path Tests
npm test -- __tests__/pages/auth/google-oauth-paths.test.ts
✓ 10 passed, 10 total (0.428s)

# API Paths Integration Tests
npm test -- __tests__/integration/api-paths.test.ts
✓ 9 passed, 9 total (0.3s)

# Regression Tests
npm test -- __tests__/regression/api-proxy-paths.test.ts
✓ 14 passed, 14 total (0.296s)

TOTAL: 42 tests passed
```

---

## Test Coverage

### What's Covered

1. **API Client Path Generation** ✅
   - Browser environment returns `/api/proxy`
   - SSR environment uses environment variables
   - No duplicate `/api` segments
   - Multi-domain support

2. **OAuth Flow** ✅
   - Google login URL generation
   - Google callback URL generation
   - All frontend domains supported
   - Regression protection for known bugs

3. **All API Endpoints** ✅
   - 40+ endpoints validated
   - Path format consistency
   - Next.js rewrite compatibility
   - Critical endpoints verified

4. **Regression Prevention** ✅
   - Bug #1: Duplicate /api segments (documented & tested)
   - Bug #2: Hard-coded domains (documented & tested)
   - Bug #3: CORS errors (documented & tested)
   - Incorrect patterns prevented

---

## Key Lessons

### Correct Pattern ✅
```typescript
const baseUrl = apiClient.getBaseUrl()  // Returns '/api/proxy'
const url = `${baseUrl}/v1/endpoint`     // Results in '/api/proxy/v1/endpoint'
```

### Wrong Pattern ❌
```typescript
const baseUrl = apiClient.getBaseUrl()      // Returns '/api/proxy'
const url = `${baseUrl}/api/v1/endpoint`    // Results in '/api/proxy/api/v1/endpoint'
                      ^^^^ DO NOT include /api prefix!
```

### Why This Matters

**Before proxy architecture**:
- `baseUrl` was absolute: `https://api.doxa.com.tw`
- Path concatenation: `https://api.doxa.com.tw` + `/api/v1/...` = ✅ Correct

**After proxy architecture**:
- `baseUrl` is relative: `/api/proxy`
- Path concatenation: `/api/proxy` + `/api/v1/...` = ❌ **Duplicate /api**

**Solution**:
- `baseUrl` is relative: `/api/proxy`
- Path concatenation: `/api/proxy` + `/v1/...` = ✅ **Correct**

---

## Benefits of This Test Suite

### 1. Automatic Bug Detection 🐛
Any code that generates paths like `/api/proxy/api/v1/...` will immediately fail tests.

### 2. Regression Prevention 🛡️
Same bugs won't happen again - tests document and prevent known issues.

### 3. Refactoring Safety 🔧
Can safely refactor API client without fear of breaking paths.

### 4. Documentation 📚
Tests serve as documentation of correct usage patterns.

### 5. CI/CD Protection 🚀
Tests run automatically in CI pipeline, preventing bad deploys.

### 6. Multi-Domain Confidence 🌍
Validates architecture works across all current and future domains.

---

## Running the Tests

### Run All API Proxy Tests
```bash
cd apps/web

# Run all tests
npm test

# Run specific test suites
npm test -- __tests__/lib/api-client.test.ts
npm test -- __tests__/pages/auth/google-oauth-paths.test.ts
npm test -- __tests__/integration/api-paths.test.ts
npm test -- __tests__/regression/api-proxy-paths.test.ts

# Run with coverage
npm test -- --coverage
```

### Pre-commit Hook (Recommended)
```bash
# .husky/pre-commit
npm test -- __tests__/integration/api-paths.test.ts
```

---

## Future Enhancements

### Potential Additions

1. **E2E Tests**
   - Actual browser testing of OAuth flow
   - Real API requests through proxy
   - Full authentication flow validation

2. **Visual Regression Tests**
   - Capture screenshots of login/signup pages
   - Verify Google button renders correctly
   - Check for UI errors

3. **Performance Tests**
   - Measure proxy overhead
   - Compare direct vs proxy request times
   - Validate caching behavior

4. **Security Tests**
   - Validate no API tokens in URLs
   - Check HTTPS enforcement
   - Verify secure cookie settings

---

## Related Documentation

- **API Proxy Implementation**: `docs/architecture/api-proxy-implementation.md`
- **Multi-Domain Migration**: `docs/features/epic-new-domain/README.md`
- **Testing Strategy**: `docs/claude/testing.md`

---

## Summary

✅ **42 comprehensive tests** protect API proxy architecture
✅ **All tests passing** - validated correct implementation
✅ **4 known bugs** documented and prevented (including service layer errors)
✅ **40+ API endpoints** validated for correctness
✅ **Multi-domain ready** for future migrations

This test suite ensures the API proxy architecture remains stable and correct, preventing the types of path errors that caused production issues.
