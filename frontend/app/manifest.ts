import type { MetadataRoute } from "next";

/** Dynamic PWA web app manifest. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ReceiptLens — Smart Receipt Scanning & Expense Tracking",
    short_name: "ReceiptLens",
    description:
      "Scan receipts with OCR, track spending, forecast budgets and catch anomalies.",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#1d5ef1",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
