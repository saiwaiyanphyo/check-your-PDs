"use client";

import { useState } from "react";
import { fetchCombined, CombinedResult } from "@/lib/api";

interface Props {
  riskScore: number | null;
  cnnConfidence: number | null;
}

export default function CombinedResultPanel({ riskScore, cnnConfidence }: Props) {
  const [result, setResult] = useState<CombinedResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (riskScore === null || cnnConfidence === null) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetchCombined(riskScore, cnnConfidence);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const missing = riskScore === null || cnnConfidence === null;

  const scoreColor = result
    ? result.combined_score >= 0.7 ? "text-red-500" : result.combined_score >= 0.45 ? "text-yellow-500" : "text-green-500"
    : "";

  const badgeClass = result
    ? result.combined_score >= 0.7
      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
      : result.combined_score >= 0.45
      ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
      : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
    : "";

  return (
    <div className="space-y-6">
      <section className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-3">Inputs from Previous Stages</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className={`rounded-lg p-4 ${riskScore !== null ? "bg-purple-50 dark:bg-purple-900/20" : "bg-gray-50 dark:bg-gray-700"}`}>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Stage 1 — Clinical Score</p>
            {riskScore !== null
              ? <p className="text-2xl font-bold text-purple-600 mt-1">{riskScore} / 22</p>
              : <p className="text-sm text-gray-400 mt-1">Not completed yet</p>}
          </div>
          <div className={`rounded-lg p-4 ${cnnConfidence !== null ? "bg-purple-50 dark:bg-purple-900/20" : "bg-gray-50 dark:bg-gray-700"}`}>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Stage 2 — CNN Confidence</p>
            {cnnConfidence !== null
              ? <p className="text-2xl font-bold text-purple-600 mt-1">{(cnnConfidence * 100).toFixed(1)}%</p>
              : <p className="text-sm text-gray-400 mt-1">Not completed yet</p>}
          </div>
        </div>

        {missing && (
          <p className="text-sm text-amber-600 dark:text-amber-400 mt-3 flex items-center gap-1">
            ⚠️ Please complete both Stage 1 and Stage 2 before generating the final result.
          </p>
        )}
      </section>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <button
        onClick={submit}
        disabled={missing || loading}
        className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-semibold rounded-xl transition-colors text-sm"
      >
        {loading ? "Generating..." : "Generate Final Assessment"}
      </button>

      {result && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-xl text-gray-800 dark:text-gray-100">Final Assessment</h3>
              <span className={`text-3xl font-bold ${scoreColor}`}>{(result.combined_score * 100).toFixed(1)}%</span>
            </div>

            <span className={`inline-block px-4 py-1.5 rounded-full text-sm font-bold mb-4 ${badgeClass}`}>
              {result.recommendation}
            </span>

            <p className="text-sm text-gray-600 dark:text-gray-300 mb-5">{result.advice}</p>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-100 dark:bg-gray-600">
                    <th className="text-left px-4 py-2 text-gray-600 dark:text-gray-200 font-semibold">Component</th>
                    <th className="text-left px-4 py-2 text-gray-600 dark:text-gray-200 font-semibold">Value</th>
                    <th className="text-left px-4 py-2 text-gray-600 dark:text-gray-200 font-semibold">Weight</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-gray-200 dark:border-gray-600">
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-300">Clinical Risk Score</td>
                    <td className="px-4 py-2 font-medium">{riskScore} / 22 ({result.risk_level})</td>
                    <td className="px-4 py-2 text-gray-500">35% (×{result.risk_weight})</td>
                  </tr>
                  <tr className="border-t border-gray-200 dark:border-gray-600">
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-300">Drawing CNN Confidence</td>
                    <td className="px-4 py-2 font-medium">{((cnnConfidence ?? 0) * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2 text-gray-500">65%</td>
                  </tr>
                  <tr className="border-t border-gray-200 dark:border-gray-600 bg-purple-50 dark:bg-purple-900/20">
                    <td className="px-4 py-2 font-bold text-gray-800 dark:text-gray-100">Combined Score</td>
                    <td className={`px-4 py-2 font-bold text-lg ${scoreColor}`}>{(result.combined_score * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2" />
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4 text-sm text-amber-800 dark:text-amber-300">
            ⚠️ <strong>Disclaimer:</strong> This tool is for preliminary screening only and does not constitute a medical diagnosis.
            Always consult a qualified healthcare professional for evaluation and diagnosis of Parkinson&apos;s disease.
          </div>
        </div>
      )}
    </div>
  );
}
