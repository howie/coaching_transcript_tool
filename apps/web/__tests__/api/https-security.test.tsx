/**
 * Security tests for API client HTTPS enforcement
 * These tests ensure that Mixed Content vulnerabilities are prevented
 */

import { apiClient } from '@/lib/api'

// Mock window object for different scenarios
const mockWindow = (protocol: string, hostname: string) => {
  Object.defineProperty(global, 'window', {
    value: {
      location: {
        protocol,
        hostname
      },
      localStorage: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn()
      },
      fetch: jest.fn()
    },
    writable: true,
    configurable: true
  })
}

describe('API Client HTTPS Security', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset any previous window mocks
    delete (global as any).window
    // Reset the apiClient's baseUrl to force re-initialization
    ;(apiClient as any)._baseUrl = null
  })

  afterEach(() => {
    // Clean up
    delete (global as any).window
    ;(apiClient as any)._baseUrl = null
  })

  describe('Runtime HTTPS Enforcement', () => {
    it('should force HTTPS for secure context (https: protocol)', () => {
      // Arrange: Mock HTTPS environment
      mockWindow('https:', 'coachly.doxa.com.tw')
      
      // Act: Use existing API client (triggers lazy initialization)
      const baseUrl = apiClient.getBaseUrl()
      
      // Assert: Should use HTTPS
      expect(baseUrl).toBe('https://api.doxa.com.tw')
    })

    it('should force HTTPS for doxa.com.tw domains', () => {
      // Arrange: Mock doxa domain
      mockWindow('http:', 'coachly.doxa.com.tw')
      
      // Act: Use existing API client
      const baseUrl = apiClient.getBaseUrl()
      
      // Assert: Should still use HTTPS for security
      expect(baseUrl).toBe('https://api.doxa.com.tw')
    })

    it('should use localhost for development', () => {
      // Arrange: Mock development environment
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
      mockWindow('http:', 'localhost')
      
      // Act: Use existing API client
      const baseUrl = apiClient.getBaseUrl()
      
      // Assert: Should use environment variable for development
      expect(baseUrl).toBe('http://localhost:8000')
      
      // Cleanup
      delete process.env.NEXT_PUBLIC_API_URL
    })
  })

  describe('Health Check HTTPS Enforcement', () => {
    it('should force HTTPS for health check in secure context', async () => {
      // Arrange: Mock HTTPS environment and fetch
      mockWindow('https:', 'coachly.doxa.com.tw')
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'healthy' })
      }
      const mockFetch = jest.fn().mockResolvedValue(mockResponse)
      global.window.fetch = mockFetch
      // Also set apiClient's fetcher to use the mock
      ;(apiClient as any).fetcher = mockFetch
      
      // Act: Call health check
      await apiClient.healthCheck()
      
      // Assert: Should call HTTPS URL
      expect(mockFetch).toHaveBeenCalledWith('https://api.doxa.com.tw/api/health')
    })

    it('should replace http with https in health check URL', async () => {
      // Arrange: Mock scenario where baseUrl has HTTP but context is HTTPS
      mockWindow('https:', 'coachly.doxa.com.tw')
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'healthy' })
      }
      const mockFetch = jest.fn().mockResolvedValue(mockResponse)
      global.window.fetch = mockFetch
      ;(apiClient as any).fetcher = mockFetch
      
      // Force HTTP baseUrl to test emergency fix
      ;(apiClient as any)._baseUrl = 'http://api.doxa.com.tw'
      
      // Act: Call health check
      await apiClient.healthCheck()
      
      // Assert: Emergency hotfix should convert to HTTPS
      expect(mockFetch).toHaveBeenCalledWith('https://api.doxa.com.tw/api/health')
    })
  })

  describe('Mixed Content Prevention', () => {
    it('should never use HTTP in HTTPS context', () => {
      // Test all HTTPS scenarios
      const httpsScenarios = [
        { protocol: 'https:', hostname: 'coachly.doxa.com.tw' },
        { protocol: 'https:', hostname: 'doxa.com.tw' },
        { protocol: 'https:', hostname: 'app.example.com' }
      ]
      
      httpsScenarios.forEach(({ protocol, hostname }) => {
        // Reset for each test
        ;(apiClient as any)._baseUrl = null
        mockWindow(protocol, hostname)
        
        const baseUrl = apiClient.getBaseUrl()
        
        // Should never use HTTP in HTTPS context
        expect(baseUrl).not.toMatch(/^http:\/\//)
        expect(baseUrl).toMatch(/^https:\/\//)
      })
    })
  })

  describe('Console Warning Verification', () => {
    it('should log runtime hotfix warning for production domains', () => {
      // Arrange: Mock console.warn
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
      mockWindow('https:', 'coachly.doxa.com.tw')
      
      // Act: Trigger lazy initialization
      apiClient.getBaseUrl()
      
      // Assert: Should log security warning
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '🔒 RUNTIME HOTFIX: Using HTTPS API URL for secure context:',
        'https://api.doxa.com.tw'
      )
      
      consoleWarnSpy.mockRestore()
    })

    it('should log emergency hotfix warning for health check', async () => {
      // Arrange: Mock console.warn and fetch
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
      mockWindow('https:', 'coachly.doxa.com.tw')
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'healthy' })
      }
      const mockFetch = jest.fn().mockResolvedValue(mockResponse)
      global.window.fetch = mockFetch
      ;(apiClient as any).fetcher = mockFetch
      
      // Force HTTP baseUrl to trigger emergency fix
      ;(apiClient as any)._baseUrl = 'http://api.doxa.com.tw'
      
      // Act: Call health check
      await apiClient.healthCheck()
      
      // Assert: Should log emergency hotfix warning
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '🚑 EMERGENCY HOTFIX: Forced HTTPS for health check:',
        'https://api.doxa.com.tw/api/health'
      )
      
      consoleWarnSpy.mockRestore()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing window object gracefully', () => {
      // Arrange: No window object (SSR scenario)
      delete (global as any).window
      
      // Act & Assert: Should not throw
      expect(() => {
        apiClient.getBaseUrl()
      }).not.toThrow()
    })
  })
})

describe('API Client Security Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    delete (global as any).window
    ;(apiClient as any)._baseUrl = null
  })

  it('should maintain HTTPS consistency across multiple method calls', async () => {
    // Arrange: Mock HTTPS environment
    mockWindow('https:', 'coachly.doxa.com.tw')
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({ data: 'test' })
    }
    const mockFetch = jest.fn().mockResolvedValue(mockResponse)
    global.window.fetch = mockFetch
    ;(apiClient as any).fetcher = mockFetch
    
    // Act: Multiple API calls
    const baseUrl1 = apiClient.getBaseUrl()
    const baseUrl2 = apiClient.getBaseUrl()
    await apiClient.healthCheck()
    const baseUrl3 = apiClient.getBaseUrl()
    
    // Assert: All calls should return consistent HTTPS URL
    expect(baseUrl1).toBe('https://api.doxa.com.tw')
    expect(baseUrl2).toBe('https://api.doxa.com.tw')
    expect(baseUrl3).toBe('https://api.doxa.com.tw')
    
    // Verify health check used HTTPS
    expect(mockFetch).toHaveBeenCalledWith('https://api.doxa.com.tw/api/health')
  })
})