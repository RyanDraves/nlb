import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // TODO: don't steamroll through typescript errors
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: true,
};

export default nextConfig;
