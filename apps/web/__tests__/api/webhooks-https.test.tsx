/**
 * 單元測試：確保 Webhooks API 調用使用 HTTPS
 */

import { apiClient } from '@/lib/api'

// Mock window.location for HTTPS environment
const mockLocation = {
  protocol: 'https:',
  hostname: 'coachly.doxa.com.tw',
  href: 'https://coachly.doxa.com.tw/dashboard/billing'
}

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
})

// Mock fetch to capture the actual URLs being called
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('Webhooks HTTPS Enforcement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
      status: 200,
      statusText: 'OK'
    } as Response)
  })

  test('should force HTTPS for webhooks health check via get() method', async () => {
    // Test the actual get method that ECPay uses
    try {
      await apiClient.get('/api/webhooks/health/')
    } catch (error) {
      // We don't care if the call fails, we just want to check the URL
    }

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('https://api.doxa.com.tw'),
      expect.any(Object)
    )

    const calledUrl = mockFetch.mock.calls[0][0]
    expect(calledUrl).toMatch(/^https:\/\/api\.doxa\.com\.tw/)
    expect(calledUrl).not.toMatch(/^http:\/\//)
  })

  test('should force HTTPS for various doxa.com.tw endpoints', async () => {
    const endpoints = [
      '/api/webhooks/health/',
      '/api/v1/user/profile',
      '/api/v1/clients'
    ]

    for (const endpoint of endpoints) {
      try {
        await apiClient.get(endpoint)
      } catch (error) {
        // Ignore errors, we just want to check URLs
      }
    }

    // Check that all calls used HTTPS
    mockFetch.mock.calls.forEach((call, index) => {
      const url = call[0]
      expect(url).toMatch(/^https:\/\/api\.doxa\.com\.tw/, 
        `Call ${index + 1} should use HTTPS: ${url}`)
    })
  })

  test('should preserve localhost URLs (development)', async () => {
    // Mock development environment
    const originalBaseUrl = (apiClient as any)._baseUrl
    ;(apiClient as any)._baseUrl = 'http://localhost:8000'

    try {
      await apiClient.get('/api/health/')
    } catch (error) {
      // Ignore errors
    }

    const calledUrl = mockFetch.mock.calls[mockFetch.mock.calls.length - 1][0]
    expect(calledUrl).toMatch(/^http:\/\/localhost:8000/)

    // Restore original baseUrl
    ;(apiClient as any)._baseUrl = originalBaseUrl
  })

  test('should handle trailing slash enforcement for specific endpoints', async () => {
    try {
      await apiClient.get('/api/webhooks/health')  // Without trailing slash
    } catch (error) {
      // Ignore errors
    }

    const calledUrl = mockFetch.mock.calls[mockFetch.mock.calls.length - 1][0]
    expect(calledUrl).toContain('/api/webhooks/health/')  // Should have trailing slash
  })
})