"use client";

import { useState, useRef } from "react";
import { Camera, Lightbulb, PenLine, RefreshCw, WavesHorizontal, type LucideIcon } from "lucide-react";
import { fetchStage2, Stage2Result, AnomalyRegion } from "@/lib/api";

function regionStyle(intensity: number) {
  if (intensity >= 0.75) return { bg: "bg-rose-50 border-rose-200",   badge: "bg-rose-500",   text: "text-rose-800"   };
  if (intensity >= 0.50) return { bg: "bg-amber-50 border-amber-200", badge: "bg-amber-500",  text: "text-amber-800"  };
  return                        { bg: "bg-blue-50 border-blue-200",   badge: "bg-blue-500",   text: "text-blue-800"   };
}

interface Props { onResult: (result: Stage2Result, confidence: number) => void }

export default function Stage2Upload({ onResult }: Props) {
  const [drawingType, setDrawingType] = useState<"Spiral" | "Wave">("Spiral");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Stage2Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    setFile(f); setPreview(URL.createObjectURL(f)); setResult(null);
  };

  const submit = async () => {
    if (!file) return;
    setLoading(true); setError("");
    try {
      const res = await fetchStage2(file, drawingType);
      setResult(res); onResult(res, res.confidence);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally { setLoading(false); }
  };

  const pct = result ? Math.round(result.confidence * 100) : 0;
  const riskLabel = result
    ? result.confidence >= 0.7 ? { text: "High Risk",     bg: "bg-rose-100",    text2: "text-rose-700",    bar: "bg-rose-500" }
    : result.confidence >= 0.4 ? { text: "Moderate Risk", bg: "bg-amber-100",   text2: "text-amber-700",   bar: "bg-amber-400" }
    :                             { text: "Low Risk",      bg: "bg-emerald-100", text2: "text-emerald-700", bar: "bg-emerald-500" }
    : null;

  return (
    <div className="space-y-5">

      {/* Instructions */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">How to prepare your drawing</h3>
        <div className="grid grid-cols-2 gap-3">
          {(
            [
              { Icon: RefreshCw,       title: "Spiral",   desc: "Archimedean spiral — best for PD detection" },
              { Icon: WavesHorizontal, title: "Wave",     desc: "Continuous wave pattern left-to-right" },
              { Icon: Lightbulb,       title: "Lighting", desc: "Good lighting, camera directly above paper" },
              { Icon: PenLine,         title: "Pen",      desc: "Dark pen on plain white paper" },
            ] as { Icon: LucideIcon; title: string; desc: string }[]
          ).map(({ Icon, title, desc }) => (
            <div key={title} className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
              <Icon className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-slate-700">{title}</p>
                <p className="text-xs text-slate-400">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Drawing type + upload */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
        <div className="flex gap-3 mb-5">
          {(["Spiral", "Wave"] as const).map(t => (
            <button key={t} onClick={() => setDrawingType(t)}
              className={`flex-1 py-2.5 rounded-xl text-sm font-semibold border-2 transition-all ${
                drawingType === t
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
              }`}>
              <span className="flex items-center justify-center gap-1.5">
                {t === "Spiral" ? <RefreshCw className="w-4 h-4" /> : <WavesHorizontal className="w-4 h-4" />}
                {t}
              </span>
            </button>
          ))}
        </div>

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
          onClick={() => inputRef.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed transition-all flex flex-col items-center justify-center py-10 gap-3 ${
            dragging ? "border-indigo-400 bg-indigo-50" : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50"
          }`}>
          <input ref={inputRef} type="file" accept="image/*" className="hidden"
            onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />

          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="preview" className="max-h-52 rounded-lg object-contain shadow-sm" />
          ) : (
            <>
              <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
                <Camera className="w-6 h-6 text-slate-400" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-slate-600">Drop your image here</p>
                <p className="text-xs text-slate-400 mt-0.5">or click to browse · PNG, JPG, WEBP</p>
              </div>
            </>
          )}
        </div>

        {file && (
          <p className="text-xs text-slate-400 text-center mt-2">{file.name}</p>
        )}
      </div>

      {error && <p className="text-sm text-rose-500 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">{error}</p>}

      <button onClick={submit} disabled={!file || loading}
        className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm">
        {loading ? "Analyzing…" : "Analyze Drawing"}
      </button>

      {/* Results */}
      {result && riskLabel && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
            <div className="flex items-start justify-between mb-4 gap-3">
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-1">PD Probability</p>
                <p className="text-4xl font-bold text-slate-800">{pct}<span className="text-xl text-slate-400 font-normal">%</span></p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold flex-shrink-0 ${riskLabel.bg} ${riskLabel.text2}`}>
                {riskLabel.text}
              </span>
            </div>

            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-5">
              <div className={`h-full rounded-full transition-all duration-700 ${riskLabel.bar}`} style={{ width: `${pct}%` }} />
            </div>

            <p className="text-sm text-slate-600">
              {result.confidence >= 0.7
                ? "Drawing patterns suggest high probability of motor impairment consistent with Parkinson's disease."
                : result.confidence >= 0.4
                ? "Drawing shows some irregularities. Further evaluation may be warranted."
                : "Drawing patterns appear within normal range for this analysis."}
            </p>
          </div>

          {result.heatmap_base64 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5">
              <p className="text-sm font-semibold text-slate-700 mb-3">Stroke Irregularity Map</p>
              <p className="text-xs text-slate-400 mb-4">
                Red = shaky / high-tremor strokes · Blue = smooth consistent strokes. Numbered circles mark the most irregular regions.
              </p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`data:image/png;base64,${result.heatmap_base64}`} alt="heatmap" className="w-full rounded-xl" />
            </div>
          )}

          {result.anomaly_regions && result.anomaly_regions.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5">
              <p className="text-sm font-semibold text-slate-700 mb-1">Detected Irregular Regions</p>
              <p className="text-xs text-slate-400 mb-4">
                Regions where stroke direction changes most rapidly — a key indicator of motor irregularity.
              </p>
              <div className="space-y-2">
                {result.anomaly_regions.map((region: AnomalyRegion) => {
                  const s = regionStyle(region.intensity);
                  return (
                    <div key={region.id} className={`flex items-start gap-3 p-3 rounded-xl border ${s.bg}`}>
                      <span className={`w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5 ${s.badge}`}>
                        {region.id}
                      </span>
                      <div className="min-w-0">
                        <p className={`text-sm font-semibold ${s.text}`}>{region.label}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Attention intensity: {Math.round(region.intensity * 100)}%
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
