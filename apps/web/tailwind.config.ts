import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F7F3EE",
        surface: "#FFFDFC",
        ink: {
          DEFAULT: "#181613",
          secondary: "#6F6962",
        },
        burgundy: {
          DEFAULT: "#6E1835",
          hover: "#551229",
        },
        rose: "#EAD7DC",
        taupe: "#C7B9AA",
        border: "#E8E0D8",
        success: "#2F6B4F",
        warning: "#A86B22",
        error: "#A63D40",
      },
      fontFamily: {
        display: ["'Playfair Display'", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(24, 22, 19, 0.04), 0 8px 24px -12px rgba(24, 22, 19, 0.12)",
        elevated: "0 4px 8px rgba(24, 22, 19, 0.06), 0 16px 40px -16px rgba(24, 22, 19, 0.18)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
