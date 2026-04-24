import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ModelStatusBar } from "@/components/ModelStatusBar";
import { FolderOpen } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NeuroPulse — Brain Analysis for Marketing",
  description: "See how your content activates key brain regions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="fixed top-0 left-0 right-0 z-40 flex items-center justify-end px-4 py-2 border-b border-border bg-background/80 backdrop-blur-sm">
          <Link
            href="/projects"
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-lg hover:bg-accent"
          >
            <FolderOpen className="w-3.5 h-3.5" />
            Projects
          </Link>
        </nav>
        <div className="pt-10">
          {children}
        </div>
        <ModelStatusBar />
      </body>
    </html>
  );
}
