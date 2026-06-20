import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.vinted.net" },
      { protocol: "https", hostname: "**.vinted.com" },
      { protocol: "https", hostname: "oskelly.ru" },
      { protocol: "https", hostname: "**.oskelly.ru" },
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
  },
};

export default nextConfig;
