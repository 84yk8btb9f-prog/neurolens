// frontend/src/types/analysis.ts
export interface BrainScores {
  visual_cortex: number;
  face_social: number;
  amygdala: number;
  hippocampus: number;
  language_areas: number;
  reward_circuit: number;
  prefrontal: number;
  motor_action: number;
}

export interface Recommendation {
  region_key: keyof BrainScores;
  region_name: string;
  score: number;
  priority: "high" | "medium" | "ok";
  message: string;
  details: string;
  steps: string[];
}

export interface AnalysisResult {
  type: "image" | "video" | "youtube" | "pdf" | "text";
  scores: BrainScores;
  recommendations: Recommendation[];
  meta: Record<string, unknown>;
}

export interface CompareResult {
  a: AnalysisResult;
  b: AnalysisResult;
}

export interface ProjectSummary {
  id: number;
  name: string;
  type: string;
  created_at: string;
}

export interface Project extends ProjectSummary {
  result: AnalysisResult;
}
