import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  webpack: (config) => {
    // Ensure path aliases work properly
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve('./src'),
      '@/lib': path.resolve('./src/lib'),
      '@/components': path.resolve('./src/components'),
      '@/hooks': path.resolve('./src/hooks'),
      '@/app': path.resolve('./src/app'),
    };
    return config;
  },
};

export default nextConfig;
