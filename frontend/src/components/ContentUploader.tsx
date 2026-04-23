"use client";
import { useState, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Upload, Link, FileText, Loader2 } from "lucide-react";

interface Props {
  onResult: (result: unknown) => void;
  onError: (msg: string) => void;
  label?: string;
}

export function ContentUploader({ onResult, onError, label }: Props) {
  const [loading, setLoading] = useState(false);
  const [ytUrl, setYtUrl] = useState("");
  const [txt, setTxt] = useState("");
  const [dragging, setDragging] = useState(false);

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  async function submit(form: FormData) {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/analyze`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
      onResult(await res.json());
    } catch (e) {
      onError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const handleFile = useCallback((file: File) => {
    const f = new FormData(); f.append("file", file); submit(f);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="w-full max-w-xl">
      {label && <p className="text-sm font-medium text-muted-foreground mb-2">{label}</p>}
      <Tabs defaultValue="file">
        <TabsList className="w-full">
          <TabsTrigger value="file" className="flex-1"><Upload className="w-4 h-4 mr-1" />File</TabsTrigger>
          <TabsTrigger value="youtube" className="flex-1"><Link className="w-4 h-4 mr-1" />Video URL</TabsTrigger>
          <TabsTrigger value="text" className="flex-1"><FileText className="w-4 h-4 mr-1" />Text</TabsTrigger>
        </TabsList>

        <TabsContent value="file">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
            onClick={() => document.getElementById("file-in")?.click()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
          >
            <Upload className="w-8 h-8 mx-auto mb-3 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Drop image, video, or PDF<br />
              <span className="text-xs">JPG PNG MP4 MOV PDF supported</span>
            </p>
            <input id="file-in" type="file" className="hidden"
              accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.avi,.pdf"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
          </div>
        </TabsContent>

        <TabsContent value="youtube">
          <div className="flex gap-2 mt-2">
            <input type="url" value={ytUrl} onChange={(e) => setYtUrl(e.target.value)}
              placeholder="YouTube, TikTok, Instagram, Twitter/X, Vimeo..."
              className="flex-1 px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary" />
            <Button disabled={!ytUrl || loading} onClick={() => { const f = new FormData(); f.append("youtube_url", ytUrl); submit(f); }}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyze"}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="text">
          <textarea value={txt} onChange={(e) => setTxt(e.target.value)}
            placeholder="Paste ad copy, script, book chapter, or any text..."
            rows={5}
            className="w-full px-3 py-2 text-sm border rounded-lg bg-background resize-none focus:outline-none focus:ring-2 focus:ring-primary mt-2" />
          <Button disabled={!txt.trim() || loading} className="w-full mt-2"
            onClick={() => { const f = new FormData(); f.append("text_content", txt); submit(f); }}>
            {loading ? <><Loader2 className="w-4 h-4 animate-spin mr-2" />Analyzing...</> : "Analyze Brain Response"}
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
}
