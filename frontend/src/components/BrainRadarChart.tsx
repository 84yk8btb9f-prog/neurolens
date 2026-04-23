"use client";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";
import type { BrainScores } from "@/types/analysis";

const LABELS: Record<keyof BrainScores, string> = {
  visual_cortex: "Visual",
  face_social: "Social",
  amygdala: "Emotion",
  hippocampus: "Memory",
  language_areas: "Language",
  reward_circuit: "Reward",
  prefrontal: "Decision",
  motor_action: "Action",
};

interface Props {
  scores: BrainScores;
  compareScores?: BrainScores;
  color?: string;
  compareColor?: string;
}

export function BrainRadarChart({ scores, compareScores, color = "#6366f1", compareColor = "#f59e0b" }: Props) {
  const data = (Object.keys(LABELS) as (keyof BrainScores)[]).map((k) => ({
    region: LABELS[k], A: scores[k], B: compareScores?.[k],
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="region" tick={{ fontSize: 12, fill: "#6b7280" }} />
        <Tooltip formatter={(v: unknown, name: unknown) => [`${v}/100`, name === "A" ? "Content" : "Compare"]} />
        <Radar name="A" dataKey="A" stroke={color} fill={color} fillOpacity={0.25} strokeWidth={2} />
        {compareScores && (
          <Radar name="B" dataKey="B" stroke={compareColor} fill={compareColor} fillOpacity={0.15} strokeWidth={2} />
        )}
      </RadarChart>
    </ResponsiveContainer>
  );
}
