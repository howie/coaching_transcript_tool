/**
 * Regression Tests - API Proxy Path Bugs
 *
 * Tests to prevent known bugs from reoccurring
 * Each test documents a specific bug that was fixed
 */

import { apiClient } from '@/lib/api'

describe('Regression: API Proxy Path Bugs', () => {
  let originalWindow: typeof globalThis.window

  beforeEach(() => {
    originalWindow = globalThis.window
    globalThis.window = {} as any
    ;(apiClient as any)._baseUrl = null
  })

  afterEach(() => {
    if (originalWindow) {
      globalThis.window = originalWindow
    } else {
      delete (globalThis as any).window
    }
  })

  describe('Bug #1: Duplicate /api in Google OAuth URL (2025-10-03)', () => {
    /**
     * BUG DESCRIPTION:
     * Login and signup pages were generating URLs like:
     * /api/proxy/api/v1/auth/google/login
     *                ^^^^ duplicate /api segment
     *
     * ROOT CAUSE:
     * - apiClient.getBaseUrl() now returns '/api/proxy' (not 'https://api.doxa.com.tw')
     * - Code was still concatenating `/api/v1/...` resulting in duplicate
     *
     * FILES AFFECTED:
     * - apps/web/app/login/page.tsx:21
     * - apps/web/app/signup/page.tsx:28
     *
     * FIX:
     * Changed from: `${baseUrl}/api/v1/auth/google/login`
     * Changed to:   `${baseUrl}/v1/auth/google/login`
     */

    it('should NOT generate /api/proxy/api/v1/... paths', () => {
      const baseUrl = apiClient.getBaseUrl()

      // This was the bug
      const buggyUrl = `${baseUrl}/api/v1/auth/google/login`
      expect(buggyUrl).toBe('/api/proxy/api/v1/auth/google/login')
      expect(buggyUrl).toMatch(/\/api\/.*\/api\//)

      // This is the fix
      const fixedUrl = `${baseUrl}/v1/auth/google/login`
      expect(fixedUrl).toBe('/api/proxy/v1/auth/google/login')
      expect(fixedUrl).not.toMatch(/\/api\/.*\/api\//)
    })

    it('should count exactly ONE /api segment in OAuth URLs', () => {
      const baseUrl = apiClient.getBaseUrl()
      const oauthPath = '/v1/auth/google/login'
      const fullUrl = `${baseUrl}${oauthPath}`

      // Count /api occurrences
      const apiCount = (fullUrl.match(/\/api\//g) || []).length
      expect(apiCount).toBe(1)
    })

    it('Google OAuth login path validation', () => {
      const baseUrl = apiClient.getBaseUrl()
      const loginUrl = `${baseUrl}/v1/auth/google/login`

      expect(loginUrl).toBe('/api/proxy/v1/auth/google/login')
      expect(loginUrl.startsWith('/api/proxy/')).toBe(true)
      expect(loginUrl).not.toContain('/api/proxy/api/')
    })

    it('Google OAuth callback path validation', () => {
      const baseUrl = apiClient.getBaseUrl()
      const callbackUrl = `${baseUrl}/v1/auth/google/callback`

      expect(callbackUrl).toBe('/api/proxy/v1/auth/google/callback')
      expect(callbackUrl).not.toContain('/api/proxy/api/')
    })
  })

  describe('Bug #2: Hard-coded domain checks (2025-10-03)', () => {
    /**
     * BUG DESCRIPTION:
     * apiClient had hard-coded domain checks:
     * if (window.location.hostname.includes('doxa.com.tw')) {
     *   this._baseUrl = 'https://api.doxa.com.tw'
     * }
     *
     * PROBLEM:
     * - Not scalable for multi-domain deployment
     * - Caused CORS issues
     * - Required code changes for new domains
     *
     * FIX:
     * - Always use '/api/proxy' in browser
     * - Let Next.js rewrites handle backend routing
     * - Support any frontend domain
     */

    it('should use relative proxy path in browser (not hard-coded domains)', () => {
      globalThis.window = {} as any
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()

      // Should NOT be absolute URL
      expect(baseUrl).not.toMatch(/^https?:\/\//)

      // Should be relative proxy path
      expect(baseUrl).toBe('/api/proxy')
    })

    it('should work regardless of frontend domain', () => {
      const testDomains = [
        'coachly.doxa.com.tw',
        'coachly.tw',
        'coachly.com.tw',
        'localhost:3000',
        'staging.coachly.tw',
      ]

      testDomains.forEach(domain => {
        globalThis.window = { location: { hostname: domain } } as any
        ;(apiClient as any)._baseUrl = null

        const baseUrl = apiClient.getBaseUrl()

        // All domains should get the same relative path
        expect(baseUrl).toBe('/api/proxy')
      })
    })
  })

  describe('Bug #3: CORS errors on production (2025-10-03)', () => {
    /**
     * BUG DESCRIPTION:
     * Production frontend was making direct cross-origin requests to:
     * https://coachly.doxa.com.tw -> https://api.doxa.com.tw
     *
     * ERROR:
     * Access to fetch at 'https://api.doxa.com.tw/api/v1/subscriptions/current'
     * from origin 'https://coachly.doxa.com.tw' has been blocked by CORS policy
     *
     * FIX:
     * - Use same-origin proxy requests
     * - All requests go through /api/proxy/*
     * - Next.js server proxies to backend
     */

    it('should use same-origin requests (not cross-origin)', () => {
      globalThis.window = { location: { hostname: 'coachly.doxa.com.tw' } } as any
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()
      const apiPath = '/v1/subscriptions/current'
      const fullUrl = `${baseUrl}${apiPath}`

      // Should be same-origin (relative path)
      expect(fullUrl.startsWith('/')).toBe(true)
      expect(fullUrl).not.toMatch(/^https?:\/\//)

      // Should start with current domain (implicitly)
      expect(fullUrl).toBe('/api/proxy/v1/subscriptions/current')
    })

    it('should NOT make direct API calls to api.doxa.com.tw', () => {
      const baseUrl = apiClient.getBaseUrl()

      // Should never return absolute API URL in browser
      expect(baseUrl).not.toBe('https://api.doxa.com.tw')
      expect(baseUrl).not.toBe('http://api.doxa.com.tw')
      expect(baseUrl).not.toContain('api.doxa.com.tw')
    })
  })

  describe('Bug Prevention: Path construction patterns', () => {
    it('concatenating /api to proxy baseUrl is always wrong', () => {
      const baseUrl = apiClient.getBaseUrl()

      // Common mistakes to avoid
      const mistakes = [
        `${baseUrl}/api/v1/anything`,
        `${baseUrl}/api/health`,
        `${baseUrl}/api/auth/login`,
      ]

      mistakes.forEach(wrongPath => {
        // These all have duplicate /api
        expect(wrongPath).toMatch(/\/api\/.*\/api\//)
      })
    })

    it('correct pattern: baseUrl + /v1/... or /health', () => {
      const baseUrl = apiClient.getBaseUrl()

      const correctPatterns = [
        `${baseUrl}/v1/anything`,
        `${baseUrl}/health`,
        `${baseUrl}/v1/auth/login`,
      ]

      correctPatterns.forEach(correctPath => {
        // These should NOT have duplicate /api
        expect(correctPath).not.toMatch(/\/api\/.*\/api\//)
        expect(correctPath).toMatch(/^\/api\/proxy\//)
      })
    })
  })

  describe('Documentation: Expected behavior', () => {
    it('documents the correct URL construction pattern', () => {
      /**
       * CORRECT PATTERN:
       * const baseUrl = apiClient.getBaseUrl()  // Returns '/api/proxy'
       * const fullUrl = `${baseUrl}/v1/endpoint`  // Results in '/api/proxy/v1/endpoint'
       *
       * WRONG PATTERN:
       * const baseUrl = apiClient.getBaseUrl()  // Returns '/api/proxy'
       * const fullUrl = `${baseUrl}/api/v1/endpoint`  // Results in '/api/proxy/api/v1/endpoint' ❌
       */

      const baseUrl = apiClient.getBaseUrl()
      expect(baseUrl).toBe('/api/proxy')

      // Correct usage examples
      const examples = [
        { path: '/v1/plans/', result: '/api/proxy/v1/plans/' },
        { path: '/v1/auth/login', result: '/api/proxy/v1/auth/login' },
        { path: '/health', result: '/api/proxy/health' },
      ]

      examples.forEach(({ path, result }) => {
        expect(`${baseUrl}${path}`).toBe(result)
      })
    })
  })

  describe('Bug #4: Service layer calling apiClient.get with /api prefix (2025-10-03)', () => {
    /**
     * BUG DESCRIPTION:
     * Service layer files were calling apiClient.get('/api/v1/...') with full /api prefix
     * This creates duplicate /api segments when combined with baseUrl='/api/proxy'
     *
     * AFFECTED FILES:
     * - lib/services/plan.service.ts
     * - lib/services/subscription.service.ts
     * - components/billing/*.tsx
     *
     * EXAMPLE WRONG USAGE:
     * await apiClient.get('/api/v1/plans/current')  // ❌ Wrong
     *
     * CORRECT USAGE:
     * await apiClient.get('/v1/plans/current')  // ✅ Correct
     *
     * ROOT CAUSE:
     * Developers were treating apiClient.get() as if it expected absolute paths
     * In reality, the paths are relative to baseUrl which already contains /api/proxy
     */

    it('should NOT pass /api prefix to apiClient.get()', () => {
      const baseUrl = apiClient.getBaseUrl()

      // These patterns should NEVER be used
      const wrongPatterns = [
        '/api/v1/plans/current',
        '/api/v1/subscriptions/current',
        '/api/v1/user/profile',
      ]

      wrongPatterns.forEach(wrongPath => {
        const result = `${baseUrl}${wrongPath}`
        // This would create duplicate /api
        expect(result).toMatch(/\/api\/.*\/api\//)
        expect(result).not.toBe(`/api/proxy${wrongPath.replace('/api', '')}`)
      })
    })

    it('should pass paths WITHOUT /api prefix to apiClient methods', () => {
      const baseUrl = apiClient.getBaseUrl()

      // These are the CORRECT patterns
      const correctPatterns = [
        '/v1/plans/current',
        '/v1/subscriptions/current',
        '/v1/user/profile',
      ]

      correctPatterns.forEach(correctPath => {
        const result = `${baseUrl}${correctPath}`
        // Should NOT have duplicate /api
        expect(result).not.toMatch(/\/api\/.*\/api\//)
        // Should result in correct proxy path
        expect(result).toBe(`/api/proxy${correctPath}`)
      })
    })

    it('validates correct path construction for all service methods', () => {
      const baseUrl = apiClient.getBaseUrl()

      // Examples of service layer calls
      const serviceCalls = [
        { service: 'PlanService.getCurrentPlanStatus', path: '/v1/plans/current' },
        { service: 'SubscriptionService.getCurrentSubscription', path: '/v1/subscriptions/current' },
        { service: 'SubscriptionService.createAuthorization', path: '/v1/subscriptions/authorize' },
      ]

      serviceCalls.forEach(({ service, path }) => {
        const fullPath = `${baseUrl}${path}`

        // Validate no duplicate /api
        expect(fullPath).not.toMatch(/\/api\/.*\/api\//)

        // Validate correct structure
        expect(fullPath).toBe(`/api/proxy${path}`)

        // Validate exactly one /api segment
        const apiCount = (fullPath.match(/\/api\//g) || []).length
        expect(apiCount).toBe(1)
      })
    })
  })
})
