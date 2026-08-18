import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow local + Cloudflare tunnel hosts to load Next.js dev assets
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "traveller-items-number-cats.trycloudflare.com",
    "*.trycloudflare.com",
  ],
};

export default nextConfig;
