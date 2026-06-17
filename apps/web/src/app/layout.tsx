import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Noto_Sans_Devanagari } from "next/font/google";
import { PatientProvider } from "@/lib/hooks/use-patient";
import { ServiceWorkerRegister } from "@/components/layout/service-worker-register";
import { LocaleHtmlLang } from "@/components/layout/locale-html-lang";
import "./globals.css";

const ibmPlex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex",
  display: "swap",
});

const ibmMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-ibm-mono",
  display: "swap",
});

const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-devanagari",
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
  themeColor: "#1B4332",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        className={`${ibmPlex.variable} ${ibmMono.variable} ${notoDevanagari.variable} font-sans`}
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
