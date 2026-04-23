import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ModelStatusBar } from "@/components/ModelStatusBar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NeuroPulse — Brain Analysis for Marketing",
  description: "See how your content activates key brain regions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <ModelStatusBar />
      </body>
    </html>
  );
}
