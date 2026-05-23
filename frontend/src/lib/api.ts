const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchStage1(data: Stage1Input) {
  const res = await fetch(`${API_BASE}/stage1`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<Stage1Result>;
}

export async function fetchStage2(file: File, drawingType: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("drawing_type", drawingType);
  const res = await fetch(`${API_BASE}/stage2`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<Stage2Result>;
}

export async function fetchCombined(riskScore: number, cnnConfidence: number) {
  const res = await fetch(`${API_BASE}/combined`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ risk_score: riskScore, cnn_confidence: cnnConfidence }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<CombinedResult>;
}

// ── Types ──────────────────────────────────────────────────

export interface Stage1Input {
  age: string;
  sex: string;
  tremor: boolean;
  bradykinesia: boolean;
  rigidity: boolean;
  falls: boolean;
  gait_difficulty: boolean;
  weakness: boolean;
  asymmetric: boolean;
  cognitive_decline: boolean;
  sleep_disorder: boolean;
  constipation: boolean;
  depression: boolean;
  bedridden: boolean;
  walk_with_aid: boolean;
  has_cva: boolean;
  has_all_metabolic: boolean;
}

export interface Stage1Result {
  score: number;
  max_score: number;
  level: "Low" | "Medium" | "High";
  weight: number;
  emoji: string;
  breakdown: string[];
}

export interface Stage2Result {
  confidence: number;
  drawing_type: string;
  heatmap_base64: string | null;
}

export interface CombinedResult {
  combined_score: number;
  recommendation: string;
  advice: string;
  risk_level: string;
  risk_weight: number;
  risk_emoji: string;
}
