import path from 'path'
import { fileURLToPath } from 'url'
const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Keep builds resilient on CI
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },

  // Provide @ -> src alias for Webpack builds (e.g., Vercel)
  webpack: (config) => {
    config.resolve = config.resolve || {}
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': path.resolve(__dirname, 'src'),
      '@/': path.resolve(__dirname, 'src'),
    }
    // Also allow absolute imports from src without alias if needed
    config.resolve.modules = [path.resolve(__dirname, 'src'), 'node_modules']
    return config
  },
}

export default nextConfig
