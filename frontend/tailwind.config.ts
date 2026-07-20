import type { Config } from "tailwindcss";

// Colours are driven by the CSS custom properties in globals.css, so the whole
// palette themes (light/dark) from one attribute flip — Tailwind just names them.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        line: "var(--line)",
        ink: "var(--ink)",
        "ink-muted": "var(--ink-muted)",
        accent: "var(--accent)",
        "accent-2": "var(--accent-2)",
        band: {
          low: "var(--band-low)",
          medium: "var(--band-medium)",
          high: "var(--band-high)",
          critical: "var(--band-critical)",
        },
      },
      boxShadow: { card: "var(--shadow)" },
      borderRadius: { xl: "14px" },
    },
  },
  plugins: [],
};

export default config;
