import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Next.js Middleware for Security Headers and OAuth Support
 *
 * This middleware sets security headers including CSP (Content Security Policy)
 * that allows Google OAuth authentication while maintaining security.
 */

export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  // Generate nonce for inline scripts (for CSP)
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  // Content Security Policy for Google OAuth
  // This policy allows:
  // - Google authentication domains
  // - Google Analytics and Tag Manager
  // - Font Awesome CDN
  // - Same-origin resources
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://www.google.com https://www.googletagmanager.com https://www.google-analytics.com https://ssl.google-analytics.com https://www.gstatic.com https://apis.google.com;
    style-src 'self' 'unsafe-inline' https://accounts.google.com https://fonts.googleapis.com https://cdnjs.cloudflare.com;
    img-src 'self' data: blob: https: http:;
    font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com;
    connect-src 'self' https://accounts.google.com https://www.google.com https://www.googleapis.com https://www.googletagmanager.com https://www.google-analytics.com https://api.doxa.com.tw;
    frame-src 'self' https://accounts.google.com https://www.google.com https://content-autofill.googleapis.com;
    base-uri 'self';
    form-action 'self' https://accounts.google.com;
    object-src 'none';
  `.replace(/\s{2,}/g, ' ').trim()

  // Set security headers
  response.headers.set('Content-Security-Policy', cspHeader)
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'SAMEORIGIN')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  // IMPORTANT: Allow credentials for OAuth flow
  response.headers.set('Access-Control-Allow-Credentials', 'true')

  // For CORS preflight requests
  if (request.method === 'OPTIONS') {
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.set('Access-Control-Max-Age', '86400')
  }

  return response
}

// Configure which routes this middleware applies to
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     * - api/proxy/v1/auth/google/* (Google OAuth redirects - use Google's own CSP)
     */
    '/((?!_next/static|_next/image|favicon.ico|images/|api/proxy/v1/auth/google/).*)',
  ],
}
