"use client";

import { useState } from "react";
import Stage1Form from "@/components/Stage1Form";
import Stage2Upload from "@/components/Stage2Upload";
import CombinedResult from "@/components/CombinedResult";
import { Stage1Result, Stage2Result } from "@/lib/api";

type Tab = "stage1" | "stage2" | "combined" | "about";

export default function Home() {
  const [tab, setTab] = useState<Tab>("stage1");
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [cnnConfidence, setCnnConfidence] = useState<number | null>(null);

  const handleStage1Result = (_result: Stage1Result, score: number) => setRiskScore(score);
  const handleStage2Result = (_result: Stage2Result, confidence: number) => setCnnConfidence(confidence);

  const tabs: { id: Tab; label: string; badge?: boolean }[] = [
    { id: "stage1",   label: "📋 Stage 1",  badge: riskScore !== null },
    { id: "stage2",   label: "✏️ Stage 2",  badge: cnnConfidence !== null },
    { id: "combined", label: "📊 Combined" },
    { id: "about",    label: "ℹ️ About" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🧠</span>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Parkinson&apos;s Disease Prediction System</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">Two-stage clinical screening — MobileNetV2 + Risk Scoring</p>
            </div>
          </div>

          {/* Progress indicators */}
          <div className="flex gap-4 mt-4">
            <div className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${riskScore !== null ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-500 dark:bg-gray-700"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${riskScore !== null ? "bg-green-500" : "bg-gray-400"}`} />
              Stage 1 {riskScore !== null ? `✓ (${riskScore}/22)` : "pending"}
            </div>
            <div className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${cnnConfidence !== null ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-gray-100 text-gray-500 dark:bg-gray-700"}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${cnnConfidence !== null ? "bg-green-500" : "bg-gray-400"}`} />
              Stage 2 {cnnConfidence !== null ? `✓ (${(cnnConfidence * 100).toFixed(0)}%)` : "pending"}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map(({ id, label, badge }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`relative flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                  tab === id
                    ? "border-purple-600 text-purple-600 dark:text-purple-400"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                }`}
              >
                {label}
                {badge && (
                  <span className="absolute top-2 right-1 w-2 h-2 bg-green-500 rounded-full" />
                )}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {tab === "stage1" && (
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Answer the clinical questionnaire below. Check all symptoms that apply to determine the risk score.
            </p>
            <Stage1Form onResult={handleStage1Result} />
          </div>
        )}

        {tab === "stage2" && (
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Upload a photo of a hand-drawn spiral or wave pattern for CNN-based motor analysis.
            </p>
            <Stage2Upload onResult={handleStage2Result} />
          </div>
        )}

        {tab === "combined" && (
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Fuses your clinical risk score (35%) with the CNN drawing analysis (65%) into a final recommendation.
            </p>
            <CombinedResult riskScore={riskScore} cnnConfidence={cnnConfidence} />
          </div>
        )}

        {tab === "about" && <AboutTab />}
      </main>
    </div>
  );
}

function AboutTab() {
  return (
    <div className="space-y-6">
      <section className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-bold mb-4">Two-Stage Architecture</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700">
                <th className="text-left px-4 py-2 font-semibold">Stage</th>
                <th className="text-left px-4 py-2 font-semibold">Input</th>
                <th className="text-left px-4 py-2 font-semibold">Method</th>
                <th className="text-left px-4 py-2 font-semibold">Output</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              <tr><td className="px-4 py-2 font-medium">Stage 1</td><td className="px-4 py-2">Clinical questionnaire</td><td className="px-4 py-2">Point-based risk scoring</td><td className="px-4 py-2">Score 0–22</td></tr>
              <tr><td className="px-4 py-2 font-medium">Stage 2</td><td className="px-4 py-2">Hand-drawing image</td><td className="px-4 py-2">MobileNetV2 CNN</td><td className="px-4 py-2">PD probability 0–1</td></tr>
              <tr><td className="px-4 py-2 font-medium">Combined</td><td className="px-4 py-2">Both scores</td><td className="px-4 py-2">Weighted fusion (35/65)</td><td className="px-4 py-2">Final recommendation</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-bold mb-4">Risk Scoring System</h2>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          Derived from <strong>1,340 confirmed Parkinson&apos;s disease patient records</strong> from a hospital in Udon Thani, Thailand (2567–2568 BE).
        </p>
        <div className="grid grid-cols-3 gap-3 text-sm">
          {[
            { emoji: "🟢", level: "Low",    range: "0–2",  weight: "×0.3", desc: "Few or no clinical risk factors" },
            { emoji: "🟡", level: "Medium", range: "3–5",  weight: "×1.0", desc: "Some clinical risk factors present" },
            { emoji: "🔴", level: "High",   range: "6+",   weight: "×1.5", desc: "Multiple clinical risk factors" },
          ].map(({ emoji, level, range, weight, desc }) => (
            <div key={level} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="font-semibold">{emoji} {level}</p>
              <p className="text-gray-500 dark:text-gray-400 text-xs">Score {range} · Weight {weight}</p>
              <p className="text-gray-600 dark:text-gray-300 text-xs mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-bold mb-2">Research Team</h2>
        <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
          <li>Supervisor: Dr. Sasiporn Usanavasin</li>
          <li>Sai Wai Yan Phyo</li>
          <li>Kantapon Makpisut</li>
        </ul>
      </section>

      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4 text-sm text-amber-800 dark:text-amber-300">
        ⚠️ This tool is for <strong>preliminary screening purposes only</strong> and does not constitute a medical diagnosis.
        Always consult a qualified healthcare professional.
      </div>
    </div>
  );
}
