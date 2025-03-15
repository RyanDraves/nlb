import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // TODO: don't steamroll through typescript errors
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: true,
  // https://nextjs.org/docs/messages/export-image-api
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
