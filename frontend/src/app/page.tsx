"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ContentUploader } from "@/components/ContentUploader";

export default function Home() {
  const router = useRouter();
  const [err, setErr] = useState<string | null>(null);

  function handleResult(result: unknown) {
    sessionStorage.setItem("np_result", JSON.stringify(result));
    router.push("/analysis");
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16">
      <div className="text-center mb-10 max-w-xl">
        <h1 className="text-4xl font-bold tracking-tight mb-3">NeuroPulse</h1>
        <p className="text-muted-foreground text-lg">
          Analyze how your marketing content activates the brain.<br />
          Image, video, YouTube, PDF, or plain text.
        </p>
      </div>
      <ContentUploader onResult={handleResult} onError={setErr} />
      {err && <p className="mt-4 text-sm text-rose-500 text-center max-w-sm">{err}</p>}
      <p className="mt-8 text-xs text-muted-foreground">Runs fully local — your content never leaves your machine.</p>
    </main>
  );
}
