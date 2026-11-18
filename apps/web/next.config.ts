import type { NextConfig } from "next";

const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH?.replace(/\/$/, "") ?? "";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: demoMode ? "export" : "standalone",
  basePath: basePath || undefined,
  assetPrefix: basePath || undefined,
  trailingSlash: demoMode,
  images: { unoptimized: demoMode },
};

export default nextConfig;
