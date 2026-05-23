"use client";

import { useState, useRef } from "react";
import { fetchStage2, Stage2Result } from "@/lib/api";

interface Props {
  onResult: (result: Stage2Result, confidence: number) => void;
}

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
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  };

  const submit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetchStage2(file, drawingType);
      setResult(res);
      onResult(res, res.confidence);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const confidenceColor = result
    ? result.confidence >= 0.7 ? "text-red-500" : result.confidence >= 0.4 ? "text-yellow-500" : "text-green-500"
    : "";

  return (
    <div className="space-y-6">
      <section className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-1">Instructions</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          Draw one of the patterns below on white paper with a dark pen, then upload a photo.
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 dark:text-gray-300">
          <div className="flex items-start gap-2"><span>🌀</span><span><strong>Spiral</strong> — Archimedean spiral (best for PD detection)</span></div>
          <div className="flex items-start gap-2"><span>〰️</span><span><strong>Wave</strong> — Continuous wave pattern</span></div>
          <div className="flex items-start gap-2"><span>💡</span><span>Use good lighting, camera directly above paper</span></div>
          <div className="flex items-start gap-2"><span>✍️</span><span>Draw with your dominant hand first</span></div>
        </div>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex gap-3 mb-5">
          {(["Spiral", "Wave"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setDrawingType(t)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${
                drawingType === t
                  ? "bg-purple-600 text-white border-purple-600"
                  : "bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400"
              }`}
            >
              {t === "Spiral" ? "🌀" : "〰️"} {t}
            </button>
          ))}
        </div>

        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          onClick={() => inputRef.current?.click()}
          className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-all flex flex-col items-center justify-center py-10 ${
            dragging ? "border-purple-500 bg-purple-50 dark:bg-purple-900/10" : "border-gray-200 dark:border-gray-600 hover:border-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/10"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }}
          />
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="preview" className="max-h-48 rounded-lg object-contain" />
          ) : (
            <>
              <p className="text-3xl mb-2">📷</p>
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Drop image here or click to upload</p>
              <p className="text-xs text-gray-400 mt-1">PNG, JPG, WEBP</p>
            </>
          )}
        </div>
      </section>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <button
        onClick={submit}
        disabled={!file || loading}
        className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-semibold rounded-xl transition-colors text-sm"
      >
        {loading ? "Analyzing..." : "🔬 Analyze Drawing"}
      </button>

      {result && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100">Drawing Analysis</h3>
              <span className={`text-2xl font-bold ${confidenceColor}`}>{(result.confidence * 100).toFixed(1)}%</span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {result.confidence >= 0.7
                ? "🔴 Drawing patterns suggest high probability of motor impairment consistent with PD."
                : result.confidence >= 0.4
                ? "🟡 Drawing patterns show some irregularities that may warrant further evaluation."
                : "🟢 Drawing patterns appear within normal range."}
            </p>
          </div>

          {result.heatmap_base64 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-3">Grad-CAM Attention Heatmap</h3>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`data:image/png;base64,${result.heatmap_base64}`}
                alt="Attention heatmap"
                className="w-full rounded-lg"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
