import type { NextConfig } from "next";

/**
 * ReceiptLens frontend configuration.
 *
 * The API base URL is provided at build/run time via NEXT_PUBLIC_API_BASE_URL
 * and defaults to the local FastAPI dev server. All API traffic goes straight
 * to the backend (CORS is enabled server-side with allow_origins=["*"]).
 */
const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
};

export default nextConfig;
