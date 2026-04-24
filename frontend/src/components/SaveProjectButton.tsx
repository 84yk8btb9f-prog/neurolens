"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { BookmarkPlus, Check, Loader2 } from "lucide-react";
import { saveProject } from "@/lib/api";
import type { AnalysisResult } from "@/types/analysis";

interface Props {
  result: AnalysisResult;
}

export function SaveProjectButton({ result }: Props) {
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await saveProject(name.trim(), result);
      setSaved(true);
      setOpen(false);
      setName("");
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  if (saved) {
    return (
      <Button variant="ghost" size="sm" className="text-emerald-600 pointer-events-none">
        <Check className="w-4 h-4 mr-1" /> Saved
      </Button>
    );
  }

  if (!open) {
    return (
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <BookmarkPlus className="w-4 h-4 mr-1" /> Save
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        autoFocus
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") handleSave(); if (e.key === "Escape") setOpen(false); }}
        placeholder="Project name…"
        className="px-3 py-1.5 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary w-44"
      />
      <Button size="sm" disabled={!name.trim() || saving} onClick={handleSave}>
        {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Save"}
      </Button>
      <Button variant="ghost" size="sm" onClick={() => { setOpen(false); setName(""); }}>
        Cancel
      </Button>
      {error && <p className="text-xs text-rose-500">{error}</p>}
    </div>
  );
}
