import type { Recommendation } from "@/types/analysis";
import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";

const ICON = {
  high:   <AlertCircle   className="w-4 h-4 text-rose-500    shrink-0 mt-0.5" />,
  medium: <AlertTriangle className="w-4 h-4 text-amber-500   shrink-0 mt-0.5" />,
  ok:     <CheckCircle2  className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />,
};

const BG = {
  high:   "bg-rose-50    border-rose-100    dark:bg-rose-950/20    dark:border-rose-900",
  medium: "bg-amber-50   border-amber-100   dark:bg-amber-950/20   dark:border-amber-900",
  ok:     "bg-emerald-50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900",
};

export function RecommendationPanel({ recommendations, showOk = false }: { recommendations: Recommendation[]; showOk?: boolean }) {
  const visible = showOk ? recommendations : recommendations.filter((r) => r.priority !== "ok");
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Optimization</h3>
      {visible.map((r) => (
        <div key={r.region_key} className={`flex gap-3 p-3 rounded-lg border text-sm ${BG[r.priority]}`}>
          {ICON[r.priority]}
          <div><span className="font-medium">{r.region_name}: </span>{r.message}</div>
        </div>
      ))}
      {visible.length === 0 && (
        <p className="text-sm text-muted-foreground italic">All regions scoring well.</p>
      )}
    </div>
  );
}
