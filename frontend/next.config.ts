import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images1.vinted.net" },
      { protocol: "https", hostname: "images2.vinted.net" },
      { protocol: "https", hostname: "**.vinted.net" },
      { protocol: "https", hostname: "oskelly.ru" },
      { protocol: "https", hostname: "**.oskelly.ru" },
      { protocol: "https", hostname: "cdn.oskelly.ru" },
    ],
  },
};

export default nextConfig;
