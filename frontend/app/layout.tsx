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
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#1d5ef1" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
  width: "device-width",
  initialScale: 1,
};

/**
 * FOUC guard — runs synchronously in <head> before first paint. Applies the
 * `dark` class straight from localStorage (receiptlens.theme) or the OS
 * prefers-color-scheme, so a dark-preference reload never flashes white.
 * Keep in sync with components/ThemeToggle.tsx.
 */
const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem('receiptlens.theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark')}}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('receiptlens.theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark')}catch(e){}})();`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
