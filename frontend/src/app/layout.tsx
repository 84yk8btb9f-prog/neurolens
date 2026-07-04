import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ModelStatusBar } from "@/components/ModelStatusBar";
import { FolderOpen } from "lucide-react";

const geistSans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

const GITHUB_URL = "https://github.com/nikolas-sapa/neurolens";

const TITLE = "NeuroPulse — See how the brain reacts to your ad";
const DESCRIPTION =
  "Scores any ad — video, image, or copy — across 8 brain regions before you spend a dollar. Open source and self-hostable.";

export const metadata: Metadata = {
  metadataBase: new URL("https://neurolens-nine.vercel.app"),
  title: TITLE,
  description: DESCRIPTION,
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: "/",
    siteName: "NeuroPulse",
    type: "website",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "NeuroPulse — brain-region radar scores for any ad",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: ["/og.png"],
  },
};

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" className={className}>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <nav className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between px-4 py-2 border-b border-border bg-background/80 backdrop-blur-sm">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            NeuroPulse
          </Link>
          <div className="flex items-center gap-1">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-lg hover:bg-accent"
            >
              <GitHubIcon className="w-3.5 h-3.5" />
              GitHub
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="https://img.shields.io/github/stars/nikolas-sapa/neurolens?style=flat&label=stars"
                alt="GitHub stars"
                className="h-4"
              />
            </a>
            <Link
              href="/projects"
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-lg hover:bg-accent"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              Projects
            </Link>
          </div>
        </nav>
        <div className="pt-10">
          {children}
        </div>
        <ModelStatusBar />
      </body>
    </html>
  );
}
