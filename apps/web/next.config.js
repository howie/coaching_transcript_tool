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
  // OpenNext Cloudflare configuration
  output: 'standalone',
}

module.exports = nextConfig
