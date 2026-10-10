import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Netlify keeps static export; the Docker runtime requires server.js.
  output: process.env.NEXT_BUILD_STANDALONE === "1" ? "standalone" : "export",
  trailingSlash: true,
  poweredByHeader: false,
  devIndicators: false,
};

export default nextConfig;
