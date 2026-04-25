"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Share2, Check, Loader2, Copy } from "lucide-react";
import { saveProject, shareProject } from "@/lib/api";
import type { AnalysisResult } from "@/types/analysis";

interface Props {
  result: AnalysisResult;
}

function defaultName(result: AnalysisResult): string {
  const stamp = new Date().toISOString().slice(0, 16).replace("T", " ");
  return `${result.type[0].toUpperCase() + result.type.slice(1)} — ${stamp}`;
}

export function ShareButton({ result }: Props) {
  const [loading, setLoading] = useState(false);
  const [url, setUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleShare() {
    setLoading(true);
    setError(null);
    try {
      const { id } = await saveProject(defaultName(result), result);
      const { token } = await shareProject(id);
      const shareUrl = `${window.location.origin}/share/${token}`;
      setUrl(shareUrl);
      try {
        await navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2400);
      } catch {
        // Clipboard blocked — URL still shown for manual copy
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Share failed");
    } finally {
      setLoading(false);
    }
  }

  async function copyAgain() {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2400);
    } catch {
      /* clipboard unavailable */
    }
  }

  if (url) {
    return (
      <div className="flex items-center gap-2">
        <code className="text-xs px-2.5 py-1.5 rounded-lg border border-border bg-muted/40 text-muted-foreground max-w-[260px] truncate">
          {url}
        </code>
        <Button variant="outline" size="sm" onClick={copyAgain} className="shrink-0">
          {copied ? (
            <><Check className="w-3.5 h-3.5 mr-1 text-emerald-600" /> Copied</>
          ) : (
            <><Copy className="w-3.5 h-3.5 mr-1" /> Copy</>
          )}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" disabled={loading} onClick={handleShare}>
        {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Share2 className="w-4 h-4 mr-1" />}
        {loading ? "Creating link…" : "Share"}
      </Button>
      {error && <p className="text-xs text-rose-500">{error}</p>}
    </div>
  );
}
