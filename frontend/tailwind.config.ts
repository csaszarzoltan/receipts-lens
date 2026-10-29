import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary: sage green. 600 is the action colour (#3F7150, 5.7:1 on white).
        brand: {
          50: "#F3F7F4",
          100: "#E3EEE6",
          200: "#C5DCCB",
          300: "#9EC3A7",
          400: "#74A583",
          500: "#528A63",
          600: "#3F7150",
          700: "#345D42",
          800: "#2A4A36",
          900: "#223C2D",
          950: "#13231A",
        },
        // Accent: terracotta, used sparingly for highlights and warm callouts.
        clay: {
          50: "#FBF3EF",
          100: "#F6E3DA",
          200: "#EDC7B5",
          300: "#E0A38A",
          400: "#D07F62",
          500: "#BE6446",
          600: "#A34F34",
          700: "#853F2A",
          800: "#6B3424",
          900: "#55301F",
          950: "#2E190F",
        },
        // Warm neutrals. `slate` keeps its class names but is tinted cream and
        // espresso, so the whole app shifts without touching every component.
        slate: {
          50: "#FBF8F4",
          100: "#F4EEE6",
          200: "#E7DDD1",
          300: "#D5C8BA",
          400: "#A7998B",
          500: "#7A6B5F",
          600: "#5E5148",
          700: "#4A403A",
          800: "#36302B",
          900: "#262120",
          950: "#17120F",
        },
        surface: {
          DEFAULT: "#ffffff",
          dark: "#221B17",
        },
      },
      fontFamily: {
        // Inter and Fraunces are self-hosted by next/font in app/layout.tsx.
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      borderRadius: {
        DEFAULT: "0.875rem",
      },
      boxShadow: {
        // Soft, low-contrast lift. Hairline borders still carry the structure.
        card: "0 1px 2px rgba(38, 33, 32, 0.04), 0 10px 24px -16px rgba(38, 33, 32, 0.18)",
        lift: "0 2px 4px rgba(38, 33, 32, 0.06), 0 18px 40px -20px rgba(38, 33, 32, 0.28)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out",
        shimmer: "shimmer 1.6s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
