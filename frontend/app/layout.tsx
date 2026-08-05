import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "ReceiptLens — Smart Receipt Scanning & Expense Tracking",
    template: "%s · ReceiptLens",
  },
  description:
    "Scan receipts with OCR, track spending, forecast budgets and catch anomalies — all self-hosted.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "ReceiptLens",
    statusBarStyle: "default",
  },
};

export const viewport: Viewport = {
  themeColor: "#1d5ef1",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
