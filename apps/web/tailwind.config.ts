import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f4f7fb",
        ink: "#152033",
        panel: "#ffffff",
        chrome: "#d7dfe9",
        accent: "#1257d5",
        danger: "#b42318",
        success: "#067647",
        warning: "#b54708"
      },
      fontFamily: {
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"]
      },
      boxShadow: {
        panel: "0 6px 24px rgba(21, 32, 51, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
