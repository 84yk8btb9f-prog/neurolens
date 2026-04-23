// frontend/src/lib/api.ts
import type { AnalysisResult, CompareResult } from "@/types/analysis";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post(path: string, body: FormData): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", body });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const analyzeFile = (file: File): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("file", file);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const analyzeYoutube = (url: string): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("youtube_url", url);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const analyzeText = (text: string): Promise<AnalysisResult> => {
  const f = new FormData(); f.append("text_content", text);
  return post("/analyze", f) as Promise<AnalysisResult>;
};

export const comparePair = (a: FormData, b: FormData): Promise<CompareResult> => {
  const f = new FormData();
  a.forEach((v, k) => f.append(k + "_a", v));
  b.forEach((v, k) => f.append(k + "_b", v));
  return post("/compare", f) as Promise<CompareResult>;
};
