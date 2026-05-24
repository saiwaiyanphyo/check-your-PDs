"use client";

import { useState } from "react";
import { fetchStage1, Stage1Input, Stage1Result } from "@/lib/api";

const AGES = ["Under 40", "40-49", "50-59", "60-69", "70-79", "80+"];

const SECTIONS = [
  {
    title: "Cardinal Motor Symptoms",
    subtitle: "Primary indicators of Parkinson's disease",
    color: "indigo",
    items: [
      { key: "tremor",       label: "Tremor",        desc: "Involuntary shaking, especially at rest" },
      { key: "bradykinesia", label: "Bradykinesia",   desc: "Slowness or difficulty initiating movement" },
      { key: "rigidity",     label: "Rigidity",       desc: "Muscle stiffness or resistance to movement" },
    ],
  },
  {
    title: "Supporting Motor Symptoms",
    subtitle: "Secondary movement-related signs",
    color: "violet",
    items: [
      { key: "falls",           label: "Falls / Balance problems", desc: "Frequent stumbling or falling" },
      { key: "gait_difficulty", label: "Gait difficulty",          desc: "Shuffling walk, freezing, or difficulty walking" },
      { key: "weakness",        label: "Weakness",                  desc: "General muscle weakness" },
      { key: "asymmetric",      label: "Asymmetric symptoms",       desc: "One side of body more affected" },
    ],
  },
  {
    title: "Non-Motor Symptoms",
    subtitle: "Non-movement related signs",
    color: "sky",
    items: [
      { key: "cognitive_decline", label: "Cognitive decline",    desc: "Memory problems or difficulty concentrating" },
      { key: "sleep_disorder",    label: "Sleep disorder",       desc: "Insomnia, vivid dreams, or RBD" },
      { key: "constipation",      label: "Constipation",         desc: "Chronic, not explained by other causes" },
      { key: "depression",        label: "Depression / Anxiety", desc: "Persistent low mood or worry" },
    ],
  },
  {
    title: "Functional Impact",
    subtitle: "How symptoms affect daily life",
    color: "teal",
    items: [
      { key: "bedridden",     label: "Bedridden",        desc: "Unable to get out of bed without help" },
      { key: "walk_with_aid", label: "Uses walking aid", desc: "Requires cane, walker, or wheelchair" },
    ],
  },
] as const;

const defaultForm: Stage1Input = {
  age: "60-69", sex: "Male",
  tremor: false, bradykinesia: false, rigidity: false,
  falls: false, gait_difficulty: false, weakness: false, asymmetric: false,
  cognitive_decline: false, sleep_disorder: false, constipation: false, depression: false,
  bedridden: false, walk_with_aid: false,
  has_cva: false, has_all_metabolic: false,
};

interface Props { onResult: (result: Stage1Result, score: number) => void }

export default function Stage1Form({ onResult }: Props) {
  const [form, setForm] = useState<Stage1Input>(defaultForm);
  const [result, setResult] = useState<Stage1Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (key: keyof Stage1Input, value: boolean | string) =>
    setForm(f => ({ ...f, [key]: value }));

  const submit = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetchStage1(form);
      setResult(res);
      onResult(res, res.score);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally { setLoading(false); }
  };

  const pct = result ? Math.round((result.score / 22) * 100) : 0;
  const barColor = result
    ? result.level === "High" ? "bg-rose-500" : result.level === "Medium" ? "bg-amber-400" : "bg-emerald-500"
    : "bg-indigo-500";

  return (
    <div className="space-y-5">

      {/* Demographics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
        <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-5">Demographics & Medical History</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">Age range</label>
            <div className="flex flex-wrap gap-2">
              {AGES.map(a => (
                <button key={a} onClick={() => set("age", a)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    form.age === a ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                  }`}>
                  {a}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">Biological sex</label>
            <div className="flex gap-2">
              {["Male", "Female"].map(s => (
                <button key={s} onClick={() => set("sex", s)}
                  className={`px-5 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    form.sex === s ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { key: "has_cva",           label: "History of stroke (CVA)" },
            { key: "has_all_metabolic", label: "Has all three: Hypertension + Diabetes + Dyslipidemia" },
          ].map(({ key, label }) => (
            <CheckItem key={key} checked={form[key as keyof Stage1Input] as boolean}
              onChange={v => set(key as keyof Stage1Input, v)} label={label} />
          ))}
        </div>
      </div>

      {/* Symptom sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {SECTIONS.map(({ title, subtitle, items }) => (
          <div key={title} className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
            <h3 className="text-sm font-semibold text-slate-700 mb-0.5">{title}</h3>
            <p className="text-xs text-slate-400 mb-4">{subtitle}</p>
            <div className="space-y-3">
              {items.map(({ key, label, desc }) => (
                <CheckItem key={key} checked={form[key as keyof Stage1Input] as boolean}
                  onChange={v => set(key as keyof Stage1Input, v)} label={label} desc={desc} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {error && <p className="text-sm text-rose-500 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">{error}</p>}

      <button onClick={submit} disabled={loading}
        className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm">
        {loading ? "Calculating…" : "Calculate Risk Score"}
      </button>

      {result && (
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-1">Risk Score</p>
              <p className="text-4xl font-bold text-slate-800">{result.score}<span className="text-xl text-slate-400 font-normal"> / 22</span></p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              result.level === "High"   ? "bg-rose-100 text-rose-700" :
              result.level === "Medium" ? "bg-amber-100 text-amber-700" :
                                          "bg-emerald-100 text-emerald-700"
            }`}>{result.level} Risk</span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-5">
            <div className={`h-full rounded-full transition-all duration-700 ${barColor}`} style={{ width: `${pct}%` }} />
          </div>

          {result.breakdown.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Score Breakdown</p>
              <div className="flex flex-wrap gap-2">
                {result.breakdown.map((item, i) => (
                  <span key={i} className="text-xs bg-slate-50 border border-slate-200 text-slate-600 px-3 py-1 rounded-full">{item}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CheckItem({ checked, onChange, label, desc }: {
  checked: boolean; onChange: (v: boolean) => void; label: string; desc?: string;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer group">
      <div onClick={() => onChange(!checked)}
        className={`mt-0.5 w-5 h-5 rounded-md flex-shrink-0 border-2 flex items-center justify-center transition-all ${
          checked ? "bg-indigo-600 border-indigo-600" : "bg-white border-slate-300 group-hover:border-indigo-400"
        }`}>
        {checked && <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
      </div>
      <div>
        <p className={`text-sm font-medium leading-tight transition-colors ${checked ? "text-indigo-700" : "text-slate-700 group-hover:text-indigo-600"}`}>{label}</p>
        {desc && <p className="text-xs text-slate-400 mt-0.5">{desc}</p>}
      </div>
    </label>
  );
}
