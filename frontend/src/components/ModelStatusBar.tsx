"use client";
import { useEffect, useState, useCallback } from "react";
import { Cpu, X } from "lucide-react";

interface StatusData {
  loaded: boolean;
  idle_timeout_seconds: number;
  idle_for_seconds: number | null;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ModelStatusBar() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [unloading, setUnloading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/model/status`);
      if (res.ok) setStatus(await res.json());
    } catch {
      // backend not running — silently ignore
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 30_000);
    return () => clearInterval(id);
  }, [fetchStatus]);

  async function handleUnload() {
    setUnloading(true);
    try {
      await fetch(`${BASE}/model/unload`, { method: "POST" });
      await fetchStatus();
    } finally {
      setUnloading(false);
    }
  }

  if (!status) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs shadow-sm backdrop-blur-sm ${
        status.loaded
          ? "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-400"
          : "bg-zinc-50 border-zinc-200 text-zinc-500 dark:bg-zinc-900/50 dark:border-zinc-700 dark:text-zinc-500"
      }`}>
        <Cpu className="w-3.5 h-3.5 shrink-0" />
        <span className="font-medium">
          {status.loaded ? "Model in memory" : "Model unloaded"}
        </span>
        {status.loaded && status.idle_for_seconds !== null && (
          <span className="text-xs opacity-70">
            · idle {Math.round(status.idle_for_seconds)}s
          </span>
        )}
        {status.loaded && (
          <button
            onClick={handleUnload}
            disabled={unloading}
            className="ml-1 hover:opacity-70 transition-opacity disabled:opacity-40"
            title="Unload model to free RAM"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
