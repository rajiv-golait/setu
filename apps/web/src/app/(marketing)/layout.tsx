import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Setu — for families",
  description: "Understand medical documents in your language. Share a doctor-ready brief.",
};

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
