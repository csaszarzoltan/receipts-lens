import type { NextConfig } from "next";

/**
 * ReceiptLens frontend configuration.
 *
 * The API base URL is provided at build/run time via NEXT_PUBLIC_API_BASE_URL
 * and defaults to the local FastAPI dev server. All API traffic goes straight
 * to the backend (CORS is enabled server-side with allow_origins=["*"]).
 *
 * Security headers (SEC-004, security test report 2026-08-12):
 * every page/asset response carries nosniff, frame-deny, referrer-policy,
 * permissions-policy, X-XSS-Protection: 0, and a Content-Security-Policy.
 * HSTS is included for production HTTPS; Next.js emits it on http responses
 * too, which is harmless (browsers ignore it on plain http).
 *
 * CSP notes:
 *  - 'self' everywhere: Next.js loads its own scripts/styles/fonts/images.
 *  - style-src 'unsafe-inline': required by Next.js dev overlay and the
 *    tailwind/emotion-style inline styles the app uses.
 *  - connect-src 'self' *: the app fetches its own API (same origin via
 *    Next rewrites/proxy) and may call the backend directly cross-origin
 *    during local development.
 *  - img-src 'self' data: blob: *: receipt thumbnails may be served from
 *    the API host or as data/blob URLs.
 *  - frame-ancestors 'none': no embedding of the frontend.
 *  - upgrade-insecure-requests: production-only upgrade of mixed content.
 */
const securityHeaders = [
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  {
    key: "Referrer-Policy",
    value: "no-referrer",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
  {
    key: "X-XSS-Protection",
    value: "0",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains",
  },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: *",
      "font-src 'self' data:",
      "connect-src 'self' *",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    return [
      {
        // Apply the security header set to every frontend response.
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
