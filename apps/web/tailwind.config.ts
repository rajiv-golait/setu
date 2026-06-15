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
        surface: "#FAFAF7",
        "surface-raised": "#FFFFFF",
        primary: {
          DEFAULT: "#1B4332",
          pressed: "#143528",
          light: "#40916C",
        },
        text: {
          DEFAULT: "#1A1A18",
          muted: "#6B7280",
          faint: "#9AA0A6",
        },
        warning: {
          DEFAULT: "#B45309",
          bg: "#FBF3E7",
          border: "#ECD8B6",
        },
        info: {
          DEFAULT: "#2A5BA8",
          bg: "#E9EFFB",
          border: "#CBD9F2",
          title: "#1F3F73",
        },
        danger: {
          DEFAULT: "#991B1B",
          bg: "#FBEAEA",
          border: "#EFD2D2",
        },
        success: {
          DEFAULT: "#166534",
          bg: "#E7F0E9",
          border: "#CFE3D6",
        },
        border: {
          DEFAULT: "#ECECE6",
          warm: "#E5E7EB",
        },
      },
      fontFamily: {
        sans: ["var(--font-ibm-plex)", "system-ui", "sans-serif"],
        mono: ["var(--font-ibm-mono)", "monospace"],
        devanagari: ["var(--font-noto-devanagari)", "var(--font-ibm-plex)", "sans-serif"],
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
