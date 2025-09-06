/**
 * E2E Test: Ensure no insecure HTTP requests to api.doxa.com.tw
 * This test helps prevent Mixed Content errors in production
 */

import { test, expect } from '@playwright/test'

test.describe('Mixed Content Prevention', () => {
  test('billing page should not make insecure API calls', async ({ page }) => {
    const insecureRequests: string[] = []
    
    // Monitor all network requests
    page.on('request', (request) => {
      const url = request.url()
      // Check for insecure API calls
      if (url.startsWith('http://api.doxa.com.tw')) {
        insecureRequests.push(url)
        console.error(`❌ Insecure request detected: ${url}`)
      }
    })

    // Navigate to billing page (most problematic area)
    await page.goto('/dashboard/billing', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    })

    // Assert no insecure requests were made
    expect(insecureRequests, 'Found insecure HTTP requests to api.doxa.com.tw').toHaveLength(0)
  })

  test('dashboard should not make insecure API calls', async ({ page }) => {
    const insecureRequests: string[] = []
    
    page.on('request', (request) => {
      const url = request.url()
      if (url.startsWith('http://api.doxa.com.tw')) {
        insecureRequests.push(url)
      }
    })

    await page.goto('/dashboard', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    })

    expect(insecureRequests, 'Found insecure HTTP requests').toHaveLength(0)
  })

  test('all API calls should use HTTPS or proxy', async ({ page }) => {
    const apiCalls: { url: string; isSecure: boolean }[] = []
    
    page.on('request', (request) => {
      const url = request.url()
      // Track all API calls
      if (url.includes('api.doxa.com.tw') || url.includes('/api/proxy/')) {
        apiCalls.push({
          url,
          isSecure: url.startsWith('https://') || url.startsWith('/api/proxy/')
        })
      }
    })

    // Test multiple pages
    const pages = ['/dashboard', '/dashboard/billing', '/dashboard/sessions']
    
    for (const pagePath of pages) {
      await page.goto(pagePath, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      })
    }

    // Check all API calls were secure
    const insecureCalls = apiCalls.filter(call => !call.isSecure)
    
    if (insecureCalls.length > 0) {
      console.error('Insecure API calls found:')
      insecureCalls.forEach(call => console.error(`  - ${call.url}`))
    }
    
    expect(insecureCalls).toHaveLength(0)
  })

  test('ECPay health check should use proxy', async ({ page }) => {
    const healthCheckRequests: string[] = []
    
    page.on('request', (request) => {
      const url = request.url()
      if (url.includes('webhooks/health')) {
        healthCheckRequests.push(url)
      }
    })

    await page.goto('/dashboard/billing', {
      waitUntil: 'networkidle',
      timeout: 30000
    })

    // Verify health check uses the proxy
    expect(healthCheckRequests.length).toBeGreaterThan(0)
    
    healthCheckRequests.forEach(url => {
      expect(
        url.includes('/api/proxy/') || url.startsWith('https://'),
        `Health check should use proxy or HTTPS: ${url}`
      ).toBeTruthy()
    })
  })
})

// Test configuration for Playwright
export const config = {
  use: {
    // Base URL for tests
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    
    // Don't fail on console errors/warnings (but we log them)
    ignoreHTTPSErrors: false,
    
    // Viewport and browser settings
    viewport: { width: 1280, height: 720 },
    
    // Authentication state if needed
    storageState: process.env.PLAYWRIGHT_STORAGE_STATE,
  },
  
  // Test timeout
  timeout: 60000,
  
  // Retry failed tests
  retries: process.env.CI ? 2 : 0,
}