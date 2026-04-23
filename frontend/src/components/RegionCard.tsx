import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { BrainScores } from "@/types/analysis";

const META: Record<keyof BrainScores, { name: string; sub: string }> = {
  visual_cortex: { name: "Visual Cortex", sub: "Visual appeal" },
  face_social:   { name: "Face & Social", sub: "Human connection" },
  amygdala:      { name: "Emotional Core", sub: "Emotional impact" },
  hippocampus:   { name: "Memory", sub: "Memorability" },
  language_areas:{ name: "Language Areas", sub: "Message clarity" },
  reward_circuit:{ name: "Reward Circuit", sub: "Desire & intent" },
  prefrontal:    { name: "Decision Center", sub: "Trust & proof" },
  motor_action:  { name: "Action Drive", sub: "CTA activation" },
};

function bar(score: number) {
  if (score >= 65) return "bg-emerald-500";
  if (score >= 35) return "bg-amber-500";
  return "bg-rose-500";
}

export function RegionCard({ regionKey, score }: { regionKey: keyof BrainScores; score: number }) {
  const m = META[regionKey];
  const label = score >= 65 ? "Strong" : score >= 35 ? "Moderate" : "Weak";
  const variant: "default" | "secondary" | "destructive" = score >= 65 ? "default" : score >= 35 ? "secondary" : "destructive";
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-sm font-semibold">{m.name}</p>
            <p className="text-xs text-muted-foreground">{m.sub}</p>
          </div>
          <Badge variant={variant}>{label}</Badge>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all ${bar(score)}`} style={{ width: `${score}%` }} />
          </div>
          <span className="text-sm font-mono font-bold w-8 text-right">{score}</span>
        </div>
      </CardContent>
    </Card>
  );
}
