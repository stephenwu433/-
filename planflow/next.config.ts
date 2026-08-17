import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow Cloudflare quick tunnel host to load Next.js dev assets
  allowedDevOrigins: [
    "traveller-items-number-cats.trycloudflare.com",
    "*.trycloudflare.com",
  ],
};

export default nextConfig;
