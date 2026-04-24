"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BrainRadarChart } from "@/components/BrainRadarChart";
import { RegionCard } from "@/components/RegionCard";
import { RecommendationPanel } from "@/components/RecommendationPanel";
import { SaveProjectButton } from "@/components/SaveProjectButton";
import { Button } from "@/components/ui/button";
import { ArrowLeft, BarChart2, FolderOpen } from "lucide-react";
import type { AnalysisResult, BrainScores } from "@/types/analysis";

export default function AnalysisPage() {
  const router = useRouter();
  const [result, setResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("np_result");
    if (!raw) { router.push("/"); return; }
    setResult(JSON.parse(raw));
  }, [router]);

  if (!result) return null;

  const keys = Object.keys(result.scores) as (keyof BrainScores)[];
  const avg = Math.round(Object.values(result.scores).reduce((a, b) => a + b, 0) / keys.length);

  return (
    <main className="min-h-screen px-4 py-10 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-8 flex-wrap">
        <Button variant="ghost" size="sm" onClick={() => router.push("/")}>
          <ArrowLeft className="w-4 h-4 mr-1" /> New
        </Button>
        <Button variant="outline" size="sm" onClick={() => router.push("/compare")}>
          <BarChart2 className="w-4 h-4 mr-1" /> Compare
        </Button>
        <Button variant="outline" size="sm" onClick={() => router.push("/projects")}>
          <FolderOpen className="w-4 h-4 mr-1" /> Projects
        </Button>
        <div className="ml-auto">
          <SaveProjectButton result={result} />
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div>
          <h2 className="text-2xl font-bold mb-1">Brain Activation</h2>
          <p className="text-muted-foreground text-sm mb-4">
            Overall: <span className="font-semibold text-foreground">{avg}/100</span>
            <span className="ml-2 capitalize text-xs">({result.type})</span>
          </p>
          <BrainRadarChart scores={result.scores} />
        </div>
        <div className="space-y-2">
          <h3 className="font-semibold mb-3">Region Breakdown</h3>
          {keys.map((k) => <RegionCard key={k} regionKey={k} score={result.scores[k]} />)}
        </div>
      </div>

      <RecommendationPanel recommendations={result.recommendations} />
    </main>
  );
}
