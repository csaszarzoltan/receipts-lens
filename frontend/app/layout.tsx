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
    { media: "(prefers-color-scheme: light)", color: "#0f766e" },
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
 * Also sets html lang from receiptlens.locale so pre-login E2E (addInitScript)
 * is visible before hydration.
 */
const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem('receiptlens.theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark')}}catch(e){}})();`;
const LOCALE_INIT_SCRIPT = `(function(){try{var S=['en','hu','de','fr','es','it','pt','nl','pl','ro'];var l=localStorage.getItem('receiptlens.locale');if(!l||S.indexOf(l)<0){l=null;var P=navigator.languages||[navigator.language];for(var i=0;i<P.length&&!l;i++){var b=String(P[i]||'').toLowerCase().split('-')[0];if(S.indexOf(b)>=0)l=b;}}if(l)document.documentElement.lang=l;}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: LOCALE_INIT_SCRIPT,
          }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: THEME_INIT_SCRIPT,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
