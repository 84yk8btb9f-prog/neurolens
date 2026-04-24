"use client";
import { useState } from "react";
import type { Recommendation } from "@/types/analysis";
import { AlertCircle, AlertTriangle, CheckCircle2, ChevronDown } from "lucide-react";

const ICON = {
  high:   <AlertCircle   className="w-4 h-4 text-rose-500    shrink-0" />,
  medium: <AlertTriangle className="w-4 h-4 text-amber-500   shrink-0" />,
  ok:     <CheckCircle2  className="w-4 h-4 text-emerald-500 shrink-0" />,
};

const COLORS = {
  high: {
    card:   "border-rose-200    dark:border-rose-900",
    header: "bg-rose-50    dark:bg-rose-950/30",
    badge:  "bg-rose-100   text-rose-700   dark:bg-rose-900/40 dark:text-rose-300",
    body:   "bg-white      dark:bg-rose-950/10",
    step:   "text-rose-600 dark:text-rose-400",
    num:    "bg-rose-100   text-rose-700   dark:bg-rose-900/50 dark:text-rose-300",
  },
  medium: {
    card:   "border-amber-200   dark:border-amber-900",
    header: "bg-amber-50   dark:bg-amber-950/30",
    badge:  "bg-amber-100  text-amber-700  dark:bg-amber-900/40 dark:text-amber-300",
    body:   "bg-white      dark:bg-amber-950/10",
    step:   "text-amber-700 dark:text-amber-400",
    num:    "bg-amber-100  text-amber-700  dark:bg-amber-900/50 dark:text-amber-300",
  },
  ok: {
    card:   "border-emerald-200 dark:border-emerald-900",
    header: "bg-emerald-50 dark:bg-emerald-950/30",
    badge:  "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
    body:   "bg-white      dark:bg-emerald-950/10",
    step:   "text-emerald-700 dark:text-emerald-400",
    num:    "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300",
  },
};

function RecommendationCard({ r }: { r: Recommendation }) {
  const [open, setOpen] = useState(r.priority === "high");
  const c = COLORS[r.priority];

  return (
    <div className={`rounded-xl border overflow-hidden ${c.card}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:brightness-95 ${c.header}`}
      >
        {ICON[r.priority]}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-foreground">{r.region_name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${c.badge}`}>
              Score {r.score}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{r.message}</p>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className={`px-5 py-4 border-t ${c.card} ${c.body} space-y-4`}>
          <p className="text-sm text-muted-foreground leading-relaxed">{r.details}</p>
          {r.steps.length > 0 && (
            <div className="space-y-2.5">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Fix it</p>
              <ol className="space-y-2">
                {r.steps.map((step, i) => (
                  <li key={i} className="flex gap-3 items-start">
                    <span className={`text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${c.num}`}>
                      {i + 1}
                    </span>
                    <span className="text-sm text-foreground/90 leading-snug">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function RecommendationPanel({ recommendations, showOk = false }: { recommendations: Recommendation[]; showOk?: boolean }) {
  const visible = showOk ? recommendations : recommendations.filter((r) => r.priority !== "ok");
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Optimization</h3>
      {visible.map((r) => (
        <RecommendationCard key={r.region_key} r={r} />
      ))}
      {visible.length === 0 && (
        <p className="text-sm text-muted-foreground italic">All regions scoring well.</p>
      )}
    </div>
  );
}
