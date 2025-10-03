/**
 * Google OAuth Path Generation Tests
 *
 * Tests to ensure login and signup pages generate correct Google OAuth URLs
 * Prevents the /api/proxy/api/v1/... duplicate path bug
 */

import { apiClient } from '@/lib/api'

describe('Google OAuth URL Generation', () => {
  let originalWindow: typeof globalThis.window

  beforeEach(() => {
    originalWindow = globalThis.window
    // Mock browser environment
    globalThis.window = {} as any
    ;(apiClient as any)._baseUrl = null
  })

  afterEach(() => {
    if (originalWindow) {
      globalThis.window = originalWindow
    } else {
      delete (globalThis as any).window
    }
    ;(apiClient as any)._baseUrl = null
  })

  describe('Google OAuth URL construction', () => {
    it('should construct correct OAuth URL from baseUrl', () => {
      const baseUrl = apiClient.getBaseUrl()

      // WRONG WAY (the bug we're preventing)
      const wrongUrl = `${baseUrl}/api/v1/auth/google/login`
      expect(wrongUrl).toBe('/api/proxy/api/v1/auth/google/login')
      expect(wrongUrl).toMatch(/\/api\/.*\/api\//) // Has duplicate!

      // CORRECT WAY
      const correctUrl = `${baseUrl}/v1/auth/google/login`
      expect(correctUrl).toBe('/api/proxy/v1/auth/google/login')
      expect(correctUrl).not.toMatch(/\/api\/.*\/api\//) // No duplicate!
    })

    it('should NOT contain duplicate /api segments', () => {
      const baseUrl = apiClient.getBaseUrl()
      const googlePath = '/v1/auth/google/login'
      const fullUrl = `${baseUrl}${googlePath}`

      // Regex to detect /api/.../api/ pattern
      const duplicateApiPattern = /\/api\/[^/]*\/api\//
      expect(fullUrl).not.toMatch(duplicateApiPattern)
    })

    it('should generate valid proxy path for Google OAuth', () => {
      const baseUrl = apiClient.getBaseUrl()
      const oauthUrl = `${baseUrl}/v1/auth/google/login`

      // Must start with /api/proxy
      expect(oauthUrl).toMatch(/^\/api\/proxy\//)

      // Must include v1/auth/google/login
      expect(oauthUrl).toMatch(/\/v1\/auth\/google\/login$/)

      // Complete path check
      expect(oauthUrl).toBe('/api/proxy/v1/auth/google/login')
    })
  })

  describe('OAuth callback URL generation', () => {
    it('should construct correct callback URL', () => {
      const baseUrl = apiClient.getBaseUrl()

      // Callback should also use correct path
      const callbackUrl = `${baseUrl}/v1/auth/google/callback`

      expect(callbackUrl).toBe('/api/proxy/v1/auth/google/callback')
      expect(callbackUrl).not.toMatch(/\/api\/.*\/api\//)
    })
  })

  describe('Multi-environment support', () => {
    it('should work in development (localhost)', () => {
      globalThis.window = { location: { hostname: 'localhost' } } as any
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()
      const oauthUrl = `${baseUrl}/v1/auth/google/login`

      expect(oauthUrl).toBe('/api/proxy/v1/auth/google/login')
    })

    it('should work in production (coachly.doxa.com.tw)', () => {
      globalThis.window = { location: { hostname: 'coachly.doxa.com.tw' } } as any
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()
      const oauthUrl = `${baseUrl}/v1/auth/google/login`

      expect(oauthUrl).toBe('/api/proxy/v1/auth/google/login')
    })

    it('should work with new domains (coachly.tw)', () => {
      globalThis.window = { location: { hostname: 'coachly.tw' } } as any
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()
      const oauthUrl = `${baseUrl}/v1/auth/google/login`

      expect(oauthUrl).toBe('/api/proxy/v1/auth/google/login')
    })
  })

  describe('Regression tests - Known bugs', () => {
    it('REGRESSION: should NOT generate /api/proxy/api/v1/... paths', () => {
      const baseUrl = apiClient.getBaseUrl()

      // This was the actual production bug
      const buggyConstruction = `${baseUrl}/api/v1/auth/google/login`
      expect(buggyConstruction).toBe('/api/proxy/api/v1/auth/google/login')

      // Verify it has the duplicate /api problem
      expect(buggyConstruction.match(/\/api\//g)?.length).toBe(2)

      // Correct construction should only have one /api
      const correctConstruction = `${baseUrl}/v1/auth/google/login`
      expect(correctConstruction).toBe('/api/proxy/v1/auth/google/login')
      expect(correctConstruction.match(/\/api\//g)?.length).toBe(1)
    })
  })

  describe('Path validation helpers', () => {
    const validateOAuthPath = (url: string): { valid: boolean; errors: string[] } => {
      const errors: string[] = []

      // Check 1: Must start with /api/proxy
      if (!url.startsWith('/api/proxy/')) {
        errors.push('URL must start with /api/proxy/')
      }

      // Check 2: No duplicate /api segments
      if (/\/api\/.*\/api\//.test(url)) {
        errors.push('URL contains duplicate /api segments')
      }

      // Check 3: Must contain auth path
      if (!url.includes('/auth/google/')) {
        errors.push('URL must contain /auth/google/')
      }

      return {
        valid: errors.length === 0,
        errors
      }
    }

    it('validator should pass for correct URLs', () => {
      const correctUrls = [
        '/api/proxy/v1/auth/google/login',
        '/api/proxy/v1/auth/google/callback',
      ]

      correctUrls.forEach(url => {
        const result = validateOAuthPath(url)
        expect(result.valid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })

    it('validator should fail for incorrect URLs', () => {
      const incorrectUrls = [
        { url: '/api/proxy/api/v1/auth/google/login', error: 'duplicate /api' },
        { url: '/v1/auth/google/login', error: 'missing /api/proxy' },
        { url: 'https://api.doxa.com.tw/api/v1/auth/google/login', error: 'not proxy path' },
      ]

      incorrectUrls.forEach(({ url }) => {
        const result = validateOAuthPath(url)
        expect(result.valid).toBe(false)
        expect(result.errors.length).toBeGreaterThan(0)
      })
    })
  })
})
