// frontend/src/lib/api.ts
import type { AnalysisResult, CompareResult, ProjectSummary, Project } from "@/types/analysis";

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

async function json_get(path: string): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

async function json_post(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const listProjects = (): Promise<ProjectSummary[]> =>
  json_get("/projects") as Promise<ProjectSummary[]>;

export const saveProject = (name: string, result: AnalysisResult): Promise<{ id: number }> =>
  json_post("/projects", { name, result }) as Promise<{ id: number }>;

export const getProject = (id: number): Promise<Project> =>
  json_get(`/projects/${id}`) as Promise<Project>;

export const deleteProject = (id: number): Promise<void> =>
  fetch(`${BASE}/projects/${id}`, { method: "DELETE" }).then(() => undefined);
