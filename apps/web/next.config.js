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
    // Use Git SHA if available, otherwise use timestamp
    if (process.env.VERCEL_GIT_COMMIT_SHA) {
      return process.env.VERCEL_GIT_COMMIT_SHA
    }
    if (process.env.CF_PAGES_COMMIT_SHA) {
      return process.env.CF_PAGES_COMMIT_SHA
    }
    // Fallback to package version + timestamp for local builds
    return `v${require('./package.json').version}-${Date.now()}`
  },
  // CSP headers are now managed by middleware.ts for dynamic nonce support
  // OpenNext Cloudflare configuration
  output: 'standalone',
}

module.exports = nextConfig
