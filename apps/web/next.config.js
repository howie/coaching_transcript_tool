/** @type {import('next').NextConfig} */

// Read version information from root version.json
function getVersionInfo() {
  try {
    const fs = require('fs')
    const path = require('path')
    
    // Look for version.json in the project root (../../version.json from apps/web)
    const versionPath = path.join(__dirname, '../../version.json')
    
    if (fs.existsSync(versionPath)) {
      const versionData = JSON.parse(fs.readFileSync(versionPath, 'utf8'))
      console.log('📦 Loaded version info from version.json:', versionData.displayVersion)
      return versionData
    }
    
    console.warn('⚠️  version.json not found, using fallback version')
    return {
      version: '2.11.0',
      displayVersion: 'v2.11.0',
      description: 'Coachly transcription service',
      releaseDate: new Date().toISOString().split('T')[0],
      author: 'Coachly Team'
    }
  } catch (error) {
    console.error('❌ Error reading version.json:', error)
    return {
      version: '2.11.0',
      displayVersion: 'v2.11.0',
      description: 'Coachly transcription service',
      releaseDate: new Date().toISOString().split('T')[0],
      author: 'Coachly Team'
    }
  }
}

const versionInfo = getVersionInfo()

const nextConfig = {
  eslint: {
    // Allow production builds to continue even with ESLint warnings
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Allow production builds to continue even with TypeScript errors
    ignoreBuildErrors: false,
  },
  async rewrites() {
    // Determine backend API URL based on environment
    // Supports multi-domain deployment (epic-new-domain)
    const backendApiUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL ||
                          process.env.NEXT_PUBLIC_API_URL ||
                          'https://api.doxa.com.tw'

    console.log(`🔗 Next.js API Proxy target: ${backendApiUrl}`)

    return [
      // Main API proxy - handles all /api/v1/* requests
      // Supports any backend domain via environment variables
      {
        source: '/api/proxy/v1/:path*',
        destination: `${backendApiUrl}/api/v1/:path*`,
      },
      // Legacy support - existing /api/proxy/* paths (non-v1)
      {
        source: '/api/proxy/:path*',
        destination: `${backendApiUrl}/api/:path*`,
      },
    ]
  },
  experimental: {
    typedRoutes: true,
  },
  images: {
    unoptimized: true,
    loader: 'custom',
    loaderFile: './image-loader.js',
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/**',
      },
    ],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    // Version information from root version.json
    NEXT_PUBLIC_APP_VERSION: versionInfo.version,
    NEXT_PUBLIC_APP_DISPLAY_VERSION: versionInfo.displayVersion,
    NEXT_PUBLIC_APP_DESCRIPTION: versionInfo.description,
    NEXT_PUBLIC_APP_RELEASE_DATE: versionInfo.releaseDate,
    NEXT_PUBLIC_APP_RELEASE_NOTES: versionInfo.releaseNotes,
    NEXT_PUBLIC_APP_AUTHOR: versionInfo.author,
  },
  // Generate consistent build ID to prevent chunk loading issues
  generateBuildId: async () => {
    // Priority 1: Use Git SHA from Cloudflare Pages (production)
    if (process.env.CF_PAGES_COMMIT_SHA) {
      return process.env.CF_PAGES_COMMIT_SHA
    }
    // Priority 2: Use Git SHA from Vercel (if migrating)
    if (process.env.VERCEL_GIT_COMMIT_SHA) {
      return process.env.VERCEL_GIT_COMMIT_SHA
    }
    // Priority 3: Try to get Git SHA locally
    try {
      const { execSync } = require('child_process')
      const gitSha = execSync('git rev-parse HEAD', {
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'ignore'] // Suppress error output
      }).trim()
      if (gitSha) {
        console.log('📦 Using Git SHA as Build ID:', gitSha.substring(0, 7))
        return gitSha
      }
    } catch (error) {
      // Git command failed, continue to fallback
    }
    // Fallback: Use package version only (stable, no timestamp)
    const buildId = `v${require('./package.json').version}`
    console.log('📦 Using package version as Build ID:', buildId)
    return buildId
  },
  // CSP headers are now managed by middleware.ts for dynamic nonce support
  // OpenNext Cloudflare configuration
  output: 'standalone',
}

module.exports = nextConfig
