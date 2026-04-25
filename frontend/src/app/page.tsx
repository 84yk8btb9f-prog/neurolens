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
import { SplitSquareHorizontal, Zap, Sparkles, Loader2 } from "lucide-react";
import { analyzeText } from "@/lib/api";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

const SAMPLE_AD = `Our software offers comprehensive analytics, dashboards, and customizable reporting tools. Built for modern teams who care about data. Schedule a demo to learn more about our enterprise-grade features.`;

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
  const [trying, setTrying] = useState(false);

  function handleResult(result: unknown) {
    sessionStorage.setItem("np_result", JSON.stringify(result));
    router.push("/analysis");
  }

  async function trySample() {
    setErr(null);
    setTrying(true);
    try {
      const result = await analyzeText(SAMPLE_AD);
      handleResult(result);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Sample analysis failed");
    } finally {
      setTrying(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center px-4 py-16">
      <div className="text-center mb-10 max-w-2xl">
        <h1 className="text-5xl font-bold tracking-tight mb-4">NeuroPulse</h1>
        <p className="text-muted-foreground text-lg leading-relaxed">
          Drop in any ad — video, image, or copy.
          See how the brain reacts before you spend a dollar promoting it.
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
          <button
            onClick={trySample}
            disabled={trying}
            className="mt-6 inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-60"
          >
            {trying ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            {trying ? "Analyzing sample…" : "Or try with a sample ad copy"}
          </button>
          <p className="mt-8 text-xs text-muted-foreground">
            Free and open source — self-host for full privacy.
          </p>
        </TabsContent>

        <TabsContent value="compare">
          <CompareView persona={persona} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
