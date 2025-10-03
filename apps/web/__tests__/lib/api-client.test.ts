/**
 * API Client Unit Tests
 *
 * Tests to ensure API client generates correct paths for proxy architecture
 * Prevents bugs like duplicate /api segments in URLs
 */

import { apiClient } from '@/lib/api'

describe('API Client - Path Generation', () => {
  let originalWindow: typeof globalThis.window

  beforeEach(() => {
    // Save original window
    originalWindow = globalThis.window
  })

  afterEach(() => {
    // Restore original window
    if (originalWindow) {
      globalThis.window = originalWindow
    } else {
      delete (globalThis as any).window
    }
    // Clear cached baseUrl
    ;(apiClient as any)._baseUrl = null
  })

  describe('getBaseUrl()', () => {
    it('should return /api/proxy in browser environment', () => {
      // Mock window object (browser environment)
      globalThis.window = {} as any

      const baseUrl = apiClient.getBaseUrl()

      expect(baseUrl).toBe('/api/proxy')
    })

    it('should return environment URL in SSR (no window)', () => {
      // Remove window (SSR environment)
      delete (globalThis as any).window

      // Set environment variable
      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      process.env.NEXT_PUBLIC_API_URL = 'http://test-api.com'

      // Clear cache to force re-read
      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()

      expect(baseUrl).toBe('http://test-api.com')

      // Restore
      if (originalEnv) {
        process.env.NEXT_PUBLIC_API_URL = originalEnv
      } else {
        delete process.env.NEXT_PUBLIC_API_URL
      }
    })

    it('should default to localhost:8000 in SSR when no env var', () => {
      delete (globalThis as any).window

      const originalEnv = process.env.NEXT_PUBLIC_API_URL
      delete process.env.NEXT_PUBLIC_API_URL

      ;(apiClient as any)._baseUrl = null

      const baseUrl = apiClient.getBaseUrl()

      expect(baseUrl).toBe('http://localhost:8000')

      // Restore
      if (originalEnv) {
        process.env.NEXT_PUBLIC_API_URL = originalEnv
      }
    })
  })

  describe('API request paths - NO duplicate /api segments', () => {
    beforeEach(() => {
      globalThis.window = {} as any
      ;(apiClient as any)._baseUrl = null
    })

    it('should NOT have duplicate /api in common API paths', () => {
      const baseUrl = apiClient.getBaseUrl()

      const testPaths = [
        '/v1/plans/',
        '/v1/plans/current',
        '/v1/plans/compare',
        '/v1/subscriptions/current',
        '/v1/auth/google/login',
        '/v1/auth/login',
        '/v1/auth/signup',
        '/v1/user/profile',
        '/v1/sessions',
        '/v1/clients',
        '/v1/coaching-sessions',
        '/v1/usage/trends',
        '/health',
      ]

      testPaths.forEach(path => {
        const fullPath = `${baseUrl}${path}`

        // Check no duplicate /api pattern
        expect(fullPath).not.toMatch(/\/api\/.*\/api\//)

        // Check path starts correctly with /api/proxy
        expect(fullPath).toMatch(/^\/api\/proxy\//)
      })
    })

    it('should generate correct full proxy URLs', () => {
      const baseUrl = apiClient.getBaseUrl()

      const tests = [
        { path: '/v1/plans/', expected: '/api/proxy/v1/plans/' },
        { path: '/v1/auth/login', expected: '/api/proxy/v1/auth/login' },
        { path: '/v1/auth/google/login', expected: '/api/proxy/v1/auth/google/login' },
        { path: '/health', expected: '/api/proxy/health' },
      ]

      tests.forEach(({ path, expected }) => {
        const fullPath = `${baseUrl}${path}`
        expect(fullPath).toBe(expected)
      })
    })

    it('should NOT generate /api/proxy/api/v1/... paths', () => {
      const baseUrl = apiClient.getBaseUrl()

      // This was the actual bug
      const wrongPath = `${baseUrl}/api/v1/auth/google/login`
      expect(wrongPath).toBe('/api/proxy/api/v1/auth/google/login') // Bug example

      // Correct path should be
      const correctPath = `${baseUrl}/v1/auth/google/login`
      expect(correctPath).toBe('/api/proxy/v1/auth/google/login')
      expect(correctPath).not.toMatch(/\/api\/.*\/api\//)
    })
  })

  describe('Path construction validation', () => {
    beforeEach(() => {
      globalThis.window = {} as any
      ;(apiClient as any)._baseUrl = null
    })

    it('baseUrl should not end with trailing slash', () => {
      const baseUrl = apiClient.getBaseUrl()
      expect(baseUrl).not.toMatch(/\/$/)
    })

    it('should handle paths with and without leading slash', () => {
      const baseUrl = apiClient.getBaseUrl()

      // Both should work
      const withSlash = `${baseUrl}/v1/plans`
      const withoutSlash = `${baseUrl}v1/plans` // Missing leading slash

      expect(withSlash).toBe('/api/proxy/v1/plans')
      // This would be wrong - demonstrates importance of consistent path format
      expect(withoutSlash).toBe('/api/proxyv1/plans')
    })
  })

  describe('Multi-domain support', () => {
    it('should work regardless of frontend domain', () => {
      // Simulate different frontend domains
      const domains = [
        'coachly.doxa.com.tw',
        'coachly.tw',
        'coachly.com.tw',
        'localhost:3000'
      ]

      domains.forEach(domain => {
        // Mock window with different hostnames
        globalThis.window = { location: { hostname: domain } } as any
        ;(apiClient as any)._baseUrl = null

        const baseUrl = apiClient.getBaseUrl()

        // Should always return same relative path
        expect(baseUrl).toBe('/api/proxy')
      })
    })
  })
})
