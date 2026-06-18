import type { Metadata, Viewport } from "next";
import { Baloo_2, IBM_Plex_Mono, Mukta } from "next/font/google";
import { PatientProvider } from "@/lib/hooks/use-patient";
import { ServiceWorkerRegister } from "@/components/layout/service-worker-register";
import { LocaleHtmlLang } from "@/components/layout/locale-html-lang";
import "./globals.css";

// Baloo 2 — rounded, warm display + Saathi's voice. Covers Latin + Devanagari.
const baloo = Baloo_2({
  subsets: ["latin", "devanagari"],
  weight: ["500", "600", "700"],
  variable: "--font-baloo",
  display: "swap",
});

// Mukta — clean, legible body. Covers Latin + Devanagari, vernacular-first.
const mukta = Mukta({
  subsets: ["latin", "devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-mukta",
  display: "swap",
});

const ibmMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-ibm-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Setu — a bridge to your doctor",
  description: "Understand medical documents in your language. Share a doctor-ready brief.",
  icons: { icon: "/icon.svg" },
  manifest: "/manifest.json",
  appleWebApp: { capable: true, title: "Setu" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0F766E",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        className={`${baloo.variable} ${mukta.variable} ${ibmMono.variable} font-sans`}
      >
        <PatientProvider>
          <LocaleHtmlLang />
          <ServiceWorkerRegister />
          {children}
        </PatientProvider>
      </body>
    </html>
  );
}
