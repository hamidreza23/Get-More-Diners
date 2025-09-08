import type { NextConfig } from "next";

// Rely on tsconfig.json paths for aliasing (no custom webpack config)
const nextConfig: NextConfig = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
};

export default nextConfig;
