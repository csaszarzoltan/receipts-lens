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
        brand: {
          50: "#eef6ff",
          100: "#d9ebff",
          200: "#bcdcff",
          300: "#8ec6ff",
          400: "#59a6ff",
          500: "#3380fc",
          600: "#1d5ef1",
          700: "#1548de",
          800: "#173cb4",
          900: "#19388d",
          950: "#142456",
        },
        surface: {
          DEFAULT: "#ffffff",
          dark: "#0f172a",
        },
      },
      borderRadius: {
        DEFAULT: "0.625rem",
      },
      boxShadow: {
        card: "0 1px 3px rgba(15, 23, 42, 0.08), 0 4px 14px rgba(15, 23, 42, 0.05)",
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
