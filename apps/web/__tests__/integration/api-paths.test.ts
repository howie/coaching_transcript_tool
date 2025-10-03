/**
 * API Paths Integration Test
 *
 * Validates all API endpoints used in the application have correct proxy paths
 * Ensures consistency across the entire application
 */

import { apiClient } from '@/lib/api'

describe('API Paths Integration Test', () => {
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

  // Comprehensive list of all API endpoints used in the application
  const apiEndpoints = [
    { name: 'Health Check', path: '/health', category: 'system' },
    { name: 'Plans List', path: '/v1/plans/', category: 'billing' },
    { name: 'Current Plan Status', path: '/v1/plans/current', category: 'billing' },
    { name: 'Compare Plans', path: '/v1/plans/compare', category: 'billing' },
    { name: 'Current Subscription', path: '/v1/subscriptions/current', category: 'billing' },
    { name: 'Create Subscription', path: '/v1/subscriptions/authorize', category: 'billing' },
    { name: 'Cancel Subscription', path: '/v1/subscriptions/cancel', category: 'billing' },
    { name: 'Billing History', path: '/v1/subscriptions/billing-history', category: 'billing' },
    { name: 'Google OAuth Login', path: '/v1/auth/google/login', category: 'auth' },
    { name: 'Google OAuth Callback', path: '/v1/auth/google/callback', category: 'auth' },
    { name: 'Login', path: '/v1/auth/login', category: 'auth' },
    { name: 'Signup', path: '/v1/auth/signup', category: 'auth' },
    { name: 'Refresh Token', path: '/v1/auth/refresh', category: 'auth' },
    { name: 'User Profile', path: '/v1/user/profile', category: 'user' },
    { name: 'User Preferences', path: '/v1/user/preferences', category: 'user' },
    { name: 'Set Password', path: '/v1/user/set-password', category: 'user' },
    { name: 'Change Password', path: '/v1/user/change-password', category: 'user' },
    { name: 'Delete Account', path: '/v1/user/account', category: 'user' },
    { name: 'Transcription Sessions List', path: '/v1/sessions', category: 'transcription' },
    { name: 'Get Session', path: '/v1/sessions/:id', category: 'transcription' },
    { name: 'Create Session', path: '/v1/sessions', category: 'transcription' },
    { name: 'Upload URL', path: '/v1/sessions/:id/upload-url', category: 'transcription' },
    { name: 'Confirm Upload', path: '/v1/sessions/:id/confirm-upload', category: 'transcription' },
    { name: 'Start Transcription', path: '/v1/sessions/:id/start-transcription', category: 'transcription' },
    { name: 'Export Transcript', path: '/v1/sessions/:id/transcript', category: 'transcription' },
    { name: 'Clients List', path: '/v1/clients', category: 'clients' },
    { name: 'Get Client', path: '/v1/clients/:id', category: 'clients' },
    { name: 'Create Client', path: '/v1/clients', category: 'clients' },
    { name: 'Update Client', path: '/v1/clients/:id', category: 'clients' },
    { name: 'Delete Client', path: '/v1/clients/:id', category: 'clients' },
    { name: 'Anonymize Client', path: '/v1/clients/:id/anonymize', category: 'clients' },
    { name: 'Client Sources', path: '/v1/clients/options/sources', category: 'clients' },
    { name: 'Client Types', path: '/v1/clients/options/types', category: 'clients' },
    { name: 'Client Statuses', path: '/v1/clients/options/statuses', category: 'clients' },
    { name: 'Client Statistics', path: '/v1/clients/statistics', category: 'clients' },
    { name: 'Coaching Sessions List', path: '/v1/coaching-sessions', category: 'sessions' },
    { name: 'Get Coaching Session', path: '/v1/coaching-sessions/:id', category: 'sessions' },
    { name: 'Create Coaching Session', path: '/v1/coaching-sessions', category: 'sessions' },
    { name: 'Update Coaching Session', path: '/v1/coaching-sessions/:id', category: 'sessions' },
    { name: 'Delete Coaching Session', path: '/v1/coaching-sessions/:id', category: 'sessions' },
    { name: 'Session Currencies', path: '/v1/coaching-sessions/options/currencies', category: 'sessions' },
    { name: 'Dashboard Summary', path: '/v1/dashboard/summary', category: 'dashboard' },
    { name: 'Usage History', path: '/v1/usage/trends', category: 'usage' },
    { name: 'Usage Insights', path: '/v1/usage/insights', category: 'usage' },
    { name: 'Usage Predictions', path: '/v1/usage/predictions', category: 'usage' },
    { name: 'Export Usage Data', path: '/v1/usage/export', category: 'usage' },
  ]

  describe('Path format validation', () => {
    it('all endpoints should have correct proxy paths', () => {
      const baseUrl = apiClient.getBaseUrl()

      apiEndpoints.forEach(({ name, path }) => {
        // Remove :id parameters for testing
        const cleanPath = path.replace(/:id/g, 'test-id')
        const fullPath = `${baseUrl}${cleanPath}`

        // Should start with /api/proxy
        expect(fullPath).toMatch(/^\/api\/proxy\//)

        // Should NOT have duplicate /api
        expect(fullPath).not.toMatch(/\/api\/.*\/api\//)

        // Should match expected pattern
        const expectedPath = `/api/proxy${cleanPath}`
        expect(fullPath).toBe(expectedPath)
      })
    })

    it('should categorize endpoints correctly', () => {
      const categories = [...new Set(apiEndpoints.map(e => e.category))]

      expect(categories).toContain('auth')
      expect(categories).toContain('billing')
      expect(categories).toContain('user')
      expect(categories).toContain('transcription')
      expect(categories).toContain('clients')
      expect(categories).toContain('sessions')
    })
  })

  describe('Path segment validation', () => {
    it('should not have consecutive duplicate segments', () => {
      const baseUrl = apiClient.getBaseUrl()

      apiEndpoints.forEach(({ name, path }) => {
        const cleanPath = path.replace(/:id/g, 'test-id')
        const fullPath = `${baseUrl}${cleanPath}`
        const segments = fullPath.split('/').filter(s => s)

        // Check no consecutive duplicates
        for (let i = 0; i < segments.length - 1; i++) {
          expect(segments[i]).not.toBe(segments[i + 1])
        }
      })
    })

    it('should not have empty segments', () => {
      const baseUrl = apiClient.getBaseUrl()

      apiEndpoints.forEach(({ path }) => {
        const cleanPath = path.replace(/:id/g, 'test-id')
        const fullPath = `${baseUrl}${cleanPath}`

        // Should not have double slashes (empty segments)
        expect(fullPath).not.toMatch(/\/\//)
      })
    })
  })

  describe('Proxy rewrite compatibility', () => {
    it('paths should match Next.js rewrite rules', () => {
      // Expected rewrite patterns from next.config.js
      const rewritePatterns = [
        { pattern: /^\/api\/proxy\/v1\/.+/, name: 'Main v1 API' },
        { pattern: /^\/api\/proxy\/health$/, name: 'Health check' },
      ]

      apiEndpoints.forEach(({ name, path }) => {
        const cleanPath = path.replace(/:id/g, 'test-id')
        const fullPath = `/api/proxy${cleanPath}`

        const matchesAnyPattern = rewritePatterns.some(({ pattern }) =>
          pattern.test(fullPath)
        )

        expect(matchesAnyPattern).toBe(true)
      })
    })
  })

  describe('Consistency checks', () => {
    it('all v1 endpoints should use /v1/ prefix', () => {
      const v1Endpoints = apiEndpoints.filter(e => e.path.includes('/v1/'))

      v1Endpoints.forEach(({ name, path }) => {
        expect(path).toMatch(/^\/v1\//)
      })
    })

    it('all endpoints should be lowercase', () => {
      apiEndpoints.forEach(({ path }) => {
        expect(path).toBe(path.toLowerCase())
      })
    })

    it('all endpoints should use kebab-case', () => {
      apiEndpoints.forEach(({ path }) => {
        // Remove parameters first
        const cleanPath = path.replace(/:id/g, '')

        // Should not have underscores or camelCase
        expect(cleanPath).not.toMatch(/_/)
        expect(cleanPath).not.toMatch(/[A-Z]/)
      })
    })
  })

  describe('Critical endpoints validation', () => {
    const criticalEndpoints = [
      '/v1/auth/google/login',
      '/v1/auth/login',
      '/v1/subscriptions/current',
      '/v1/plans/current',
      '/v1/user/profile',
    ]

    it('critical endpoints must have NO path errors', () => {
      const baseUrl = apiClient.getBaseUrl()

      criticalEndpoints.forEach(path => {
        const fullPath = `${baseUrl}${path}`

        // Multiple checks for critical paths
        expect(fullPath).toMatch(/^\/api\/proxy\//)
        expect(fullPath).not.toMatch(/\/api\/.*\/api\//)
        expect(fullPath).not.toMatch(/\/\//)
        expect(fullPath).toBe(`/api/proxy${path}`)
      })
    })
  })
})
