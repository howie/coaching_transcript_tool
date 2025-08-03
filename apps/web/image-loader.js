// Custom image loader for Cloudflare Workers
export default function imageLoader({ src, width, quality }) {
  // For unoptimized images, just return the src as-is
  return src
}
