/** @type {import('next').NextConfig} */
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
  // OpenNext Cloudflare configuration
  output: 'standalone',
}

module.exports = nextConfig
