"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { BrainRadarChart } from "@/components/BrainRadarChart";
import { RegionCard } from "@/components/RegionCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { ContentUploader } from "@/components/ContentUploader";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

export default function ComparePage() {
  const router = useRouter();
  const [a, setA] = useState<AnalysisResult | null>(null);
  const [b, setB] = useState<AnalysisResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const keys = a ? (Object.keys(a.scores) as (keyof BrainScores)[]) : [];

  return (
    <main className="min-h-screen px-4 py-10 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <h1 className="text-2xl font-bold">A/B Brain Comparison</h1>
      </div>

      {!(a && b) && (
        <div className="grid md:grid-cols-2 gap-8">
          <ContentUploader label="Content A" onResult={(r) => setA(r as AnalysisResult)} onError={setErr} />
          <ContentUploader label="Content B" onResult={(r) => setB(r as AnalysisResult)} onError={setErr} />
        </div>
      )}
      {err && <p className="text-sm text-rose-500 mt-4">{err}</p>}

      {a && b && (
        <>
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div>
              <h3 className="font-semibold mb-2 text-indigo-500">Content A vs B</h3>
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
              <p className="text-sm font-semibold text-indigo-500 mb-2">A — Recommendations</p>
              <RecommendationPanel recommendations={a.recommendations} />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-500 mb-2">B — Recommendations</p>
              <RecommendationPanel recommendations={b.recommendations} />
            </div>
          </div>
          <Button variant="outline" className="mt-8" onClick={() => { setA(null); setB(null); }}>
            New Comparison
          </Button>
        </>
      )}
    </main>
  );
}
