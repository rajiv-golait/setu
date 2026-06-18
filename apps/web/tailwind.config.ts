import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm cream canvas — never clinical white.
        surface: "#FFF8F0",
        "surface-raised": "#FFFCF6",
        // SETU = teal, the calm keeper.
        primary: {
          DEFAULT: "#0F766E",
          pressed: "#0B5E57",
          light: "#14B8A6",
        },
        // Saathi = coral, the warm friend (Saathi surfaces only).
        saathi: {
          DEFAULT: "#F4795B",
          deep: "#EC6A50",
          soft: "#FBBF9D",
          bg: "#FEEDE6",
          border: "#F8D3C5",
        },
        // Marigold = highlight / celebration / new-med pulse.
        marigold: {
          DEFAULT: "#F4A93C",
          bg: "#FDF1DD",
          border: "#F3DCB0",
        },
        text: {
          DEFAULT: "#1C2A2A",
          muted: "#6B7280",
          faint: "#9AA0A6",
        },
        // "Discuss with your doctor" — calm amber, caring not alarm.
        warning: {
          DEFAULT: "#F59E0B",
          bg: "#FDF1DD",
          border: "#F3DCB0",
        },
        info: {
          DEFAULT: "#2A5BA8",
          bg: "#E9EFFB",
          border: "#CBD9F2",
          title: "#1F3F73",
        },
        // Urgent only — genuine red-flag escalation.
        danger: {
          DEFAULT: "#DC2626",
          bg: "#FCEBEB",
          border: "#F4CFCF",
        },
        success: {
          DEFAULT: "#16A34A",
          bg: "#E7F5EC",
          border: "#C8E9D4",
        },
        border: {
          DEFAULT: "#F0E5D6",
          warm: "#E5D9C8",
        },
      },
      fontFamily: {
        sans: ["var(--font-mukta)", "system-ui", "sans-serif"],
        display: ["var(--font-baloo)", "var(--font-mukta)", "sans-serif"],
        mono: ["var(--font-ibm-mono)", "monospace"],
        devanagari: ["var(--font-mukta)", "var(--font-baloo)", "sans-serif"],
      },
      borderRadius: {
        card: "13px",
        hero: "18px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04)",
        raised: "0 6px 18px rgba(27,67,50,0.12)",
        phone: "0 30px 70px rgba(27,67,50,0.18)",
      },
      keyframes: {
        "setu-fade": {
          from: { transform: "translateY(7px)" },
          to: { transform: "none" },
        },
        "setu-pop": {
          from: { transform: "scale(0.94)" },
          to: { transform: "scale(1)" },
        },
        "pulse-dot": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(0.55)" },
        },
      },
      animation: {
        "setu-fade": "setu-fade 0.22s ease both",
        "setu-pop": "setu-pop 0.32s ease-out both",
        "pulse-dot": "pulse-dot 1s ease infinite",
      },
    },
  },
  plugins: [],
};

export default config;
