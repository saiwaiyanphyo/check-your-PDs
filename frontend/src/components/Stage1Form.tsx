"use client";

import { useState } from "react";
import { fetchStage1, Stage1Input, Stage1Result } from "@/lib/api";

const AGES = ["Under 40", "40-49", "50-59", "60-69", "70-79", "80+"];

const CHECKBOXES = {
  "Cardinal Motor Symptoms": [
    { key: "tremor",       label: "Tremor",       desc: "Involuntary shaking, especially at rest" },
    { key: "bradykinesia", label: "Bradykinesia",  desc: "Slowness or difficulty initiating movement" },
    { key: "rigidity",     label: "Rigidity",      desc: "Muscle stiffness or resistance to movement" },
  ],
  "Supporting Motor Symptoms": [
    { key: "falls",           label: "Falls / Balance problems",  desc: "Frequent stumbling or falling" },
    { key: "gait_difficulty", label: "Gait difficulty",          desc: "Shuffling walk, freezing, or difficulty walking" },
    { key: "weakness",        label: "Weakness",                  desc: "General muscle weakness" },
    { key: "asymmetric",      label: "Asymmetric symptoms",       desc: "One side of body more affected" },
  ],
  "Non-Motor Symptoms": [
    { key: "cognitive_decline", label: "Cognitive decline", desc: "Memory problems or difficulty concentrating" },
    { key: "sleep_disorder",    label: "Sleep disorder",    desc: "Insomnia, vivid dreams, or RBD" },
    { key: "constipation",      label: "Constipation",      desc: "Chronic, not explained by other causes" },
    { key: "depression",        label: "Depression / Anxiety", desc: "Persistent low mood or worry" },
  ],
  "Functional Impact": [
    { key: "bedridden",     label: "Bedridden",          desc: "Unable to get out of bed without help" },
    { key: "walk_with_aid", label: "Uses walking aid",   desc: "Requires cane, walker, or wheelchair" },
  ],
} as const;

const defaultForm: Stage1Input = {
  age: "60-69", sex: "Male",
  tremor: false, bradykinesia: false, rigidity: false,
  falls: false, gait_difficulty: false, weakness: false, asymmetric: false,
  cognitive_decline: false, sleep_disorder: false, constipation: false, depression: false,
  bedridden: false, walk_with_aid: false,
  has_cva: false, has_all_metabolic: false,
};

interface Props {
  onResult: (result: Stage1Result, score: number) => void;
}

export default function Stage1Form({ onResult }: Props) {
  const [form, setForm] = useState<Stage1Input>(defaultForm);
  const [result, setResult] = useState<Stage1Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (key: keyof Stage1Input, value: boolean | string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchStage1(form);
      setResult(res);
      onResult(res, res.score);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const levelColor = result
    ? result.level === "High" ? "text-red-500" : result.level === "Medium" ? "text-yellow-500" : "text-green-500"
    : "";

  return (
    <div className="space-y-6">
      {/* Demographics */}
      <section className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-4">Demographics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Age range</label>
            <div className="flex flex-wrap gap-2">
              {AGES.map((a) => (
                <button
                  key={a}
                  onClick={() => set("age", a)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    form.age === a
                      ? "bg-purple-600 text-white border-purple-600"
                      : "bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400"
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Sex</label>
            <div className="flex gap-2">
              {["Male", "Female"].map((s) => (
                <button
                  key={s}
                  onClick={() => set("sex", s)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    form.sex === s
                      ? "bg-purple-600 text-white border-purple-600"
                      : "bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-purple-400"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Medical history */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { key: "has_cva",          label: "History of stroke (CVA)" },
            { key: "has_all_metabolic", label: "Hypertension + Diabetes + Dyslipidemia (all three)" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={form[key as keyof Stage1Input] as boolean}
                onChange={(e) => set(key as keyof Stage1Input, e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-purple-600 accent-purple-600"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-purple-600">{label}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Symptom sections */}
      {Object.entries(CHECKBOXES).map(([section, items]) => (
        <section key={section} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-4">{section}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items.map(({ key, label, desc }) => (
              <label key={key} className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={form[key as keyof Stage1Input] as boolean}
                  onChange={(e) => set(key as keyof Stage1Input, e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-purple-600 accent-purple-600"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-purple-600">{label}</span>
                  <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
                </div>
              </label>
            ))}
          </div>
        </section>
      ))}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <button
        onClick={submit}
        disabled={loading}
        className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white font-semibold rounded-xl transition-colors text-sm"
      >
        {loading ? "Calculating..." : "Calculate Risk Score"}
      </button>

      {result && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg text-gray-800 dark:text-gray-100">Stage 1 Result</h3>
            <span className={`text-2xl font-bold ${levelColor}`}>{result.score} / {result.max_score}</span>
          </div>
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold mb-4 ${
            result.level === "High" ? "bg-red-100 text-red-700" :
            result.level === "Medium" ? "bg-yellow-100 text-yellow-700" :
            "bg-green-100 text-green-700"
          }`}>
            {result.emoji} {result.level} Risk
          </div>
          {result.breakdown.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Score Breakdown</p>
              <ul className="space-y-1">
                {result.breakdown.map((item, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-300 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
