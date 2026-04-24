"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ContentUploader } from "@/components/ContentUploader";
import { PersonaSelector } from "@/components/PersonaSelector";
import { BrainRadarChart } from "@/components/BrainRadarChart";
import { RegionCard } from "@/components/RegionCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { SplitSquareHorizontal, Zap } from "lucide-react";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

function CompareView({ persona }: { persona: string }) {
  const [a, setA] = useState<AnalysisResult | null>(null);
  const [b, setB] = useState<AnalysisResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const keys = a ? (Object.keys(a.scores) as (keyof BrainScores)[]) : [];

  return (
    <div className="w-full max-w-5xl mx-auto">
      {!(a && b) && (
        <div className="grid md:grid-cols-2 gap-8">
          <ContentUploader
            label="Content A"
            onResult={(r) => setA(r as AnalysisResult)}
            onError={setErr}
            persona={persona}
          />
          <ContentUploader
            label="Content B"
            onResult={(r) => setB(r as AnalysisResult)}
            onError={setErr}
            persona={persona}
          />
        </div>
      )}
      {err && <p className="text-sm text-rose-500 mt-4">{err}</p>}

      {a && b && (
        <div className="space-y-8">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-3">Brain overlap — A vs B</p>
              <BrainRadarChart scores={a.scores} compareScores={b.scores} />
            </div>
            <div className="space-y-2">
              {keys.map((k) => (
                <div key={k} className="grid grid-cols-2 gap-2">
                  <RegionCard regionKey={k} score={a.scores[k]} />
                  <RegionCard regionKey={k} score={b.scores[k]} />
                </div>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-500 mb-3">A — Recommendations</p>
              <RecommendationPanel recommendations={a.recommendations} />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-500 mb-3">B — Recommendations</p>
              <RecommendationPanel recommendations={b.recommendations} />
            </div>
          </div>

          <Button variant="outline" onClick={() => { setA(null); setB(null); }}>
            New Comparison
          </Button>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [err, setErr] = useState<string | null>(null);
  const [persona, setPersona] = useState("default");

  function handleResult(result: unknown) {
    sessionStorage.setItem("np_result", JSON.stringify(result));
    router.push("/analysis");
  }

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-16">
      <div className="text-center mb-10 max-w-xl">
        <h1 className="text-4xl font-bold tracking-tight mb-3">NeuroPulse</h1>
        <p className="text-muted-foreground text-lg">
          Analyze how your marketing content activates the brain.<br />
          Image, video, YouTube, PDF, or plain text.
        </p>
      </div>

      <PersonaSelector value={persona} onChange={setPersona} />

      <Tabs defaultValue="analyze" className="w-full max-w-5xl">
        <TabsList className="mb-8 mx-auto flex w-fit">
          <TabsTrigger value="analyze" className="gap-2">
            <Zap className="w-4 h-4" />
            Analyze
          </TabsTrigger>
          <TabsTrigger value="compare" className="gap-2">
            <SplitSquareHorizontal className="w-4 h-4" />
            A/B Compare
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analyze" className="flex flex-col items-center">
          <ContentUploader onResult={handleResult} onError={setErr} persona={persona} />
          {err && <p className="mt-4 text-sm text-rose-500 text-center max-w-sm">{err}</p>}
          <p className="mt-8 text-xs text-muted-foreground">Runs fully local — your content never leaves your machine.</p>
        </TabsContent>

        <TabsContent value="compare">
          <CompareView persona={persona} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
