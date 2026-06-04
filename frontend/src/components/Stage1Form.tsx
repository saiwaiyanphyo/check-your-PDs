"use client";

import { useState, useRef } from "react";
import { fetchStage1, Stage1Input, Stage1Result } from "@/lib/api";
import { useLocale } from "@/lib/i18n";

const AGES = ["Under 40", "40-49", "50-59", "60-69", "70-79", "80+"];

const defaultForm: Stage1Input = {
  age: "60-69", sex: "Male",
  tremor: false, bradykinesia: false, rigidity: false,
  falls: false, gait_difficulty: false, weakness: false, asymmetric: false,
  cognitive_decline: false, sleep_disorder: false, constipation: false, depression: false,
  bedridden: false, walk_with_aid: false,
  has_cva: false, has_all_metabolic: false,
};

interface Props { onResult: (result: Stage1Result, score: number) => void; onNext: () => void }

export default function Stage1Form({ onResult, onNext }: Props) {
  const { t } = useLocale();
  const [form, setForm] = useState<Stage1Input>(defaultForm);
  const [result, setResult] = useState<Stage1Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const resultRef = useRef<HTMLDivElement>(null);

  const sections = [
    {
      title: t("stage1.cardinal_title"),
      subtitle: t("stage1.cardinal_subtitle"),
      items: [
        { key: "tremor",       label: t("stage1.tremor_label"),       desc: t("stage1.tremor_desc") },
        { key: "bradykinesia", label: t("stage1.bradykinesia_label"), desc: t("stage1.bradykinesia_desc") },
        { key: "rigidity",     label: t("stage1.rigidity_label"),     desc: t("stage1.rigidity_desc") },
      ],
    },
    {
      title: t("stage1.supporting_title"),
      subtitle: t("stage1.supporting_subtitle"),
      items: [
        { key: "falls",           label: t("stage1.falls_label"),      desc: t("stage1.falls_desc") },
        { key: "gait_difficulty", label: t("stage1.gait_label"),       desc: t("stage1.gait_desc") },
        { key: "weakness",        label: t("stage1.weakness_label"),   desc: t("stage1.weakness_desc") },
        { key: "asymmetric",      label: t("stage1.asymmetric_label"), desc: t("stage1.asymmetric_desc") },
      ],
    },
    {
      title: t("stage1.nonmotor_title"),
      subtitle: t("stage1.nonmotor_subtitle"),
      items: [
        { key: "cognitive_decline", label: t("stage1.cognitive_label"),    desc: t("stage1.cognitive_desc") },
        { key: "sleep_disorder",    label: t("stage1.sleep_label"),        desc: t("stage1.sleep_desc") },
        { key: "constipation",      label: t("stage1.constipation_label"), desc: t("stage1.constipation_desc") },
        { key: "depression",        label: t("stage1.depression_label"),   desc: t("stage1.depression_desc") },
      ],
    },
    {
      title: t("stage1.functional_title"),
      subtitle: t("stage1.functional_subtitle"),
      items: [
        { key: "bedridden",     label: t("stage1.bedridden_label"), desc: t("stage1.bedridden_desc") },
        { key: "walk_with_aid", label: t("stage1.walkaid_label"),   desc: t("stage1.walkaid_desc") },
      ],
    },
  ];

  const set = (key: keyof Stage1Input, value: boolean | string) =>
    setForm(f => ({ ...f, [key]: value }));

  const submit = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetchStage1(form);
      setResult(res);
      onResult(res, res.score);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally { setLoading(false); }
  };

  const pct = result ? Math.round((result.score / 22) * 100) : 0;
  const barColor = result
    ? result.level === "High" ? "bg-rose-500" : result.level === "Medium" ? "bg-amber-400" : "bg-emerald-500"
    : "bg-indigo-500";

  const riskLabel = result
    ? result.level === "High"   ? t("stage1.high_risk")
    : result.level === "Medium" ? t("stage1.medium_risk")
    :                             t("stage1.low_risk")
    : "";

  return (
    <div className="space-y-5">

      {/* Demographics */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
        <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-5">{t("stage1.demo_title")}</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">{t("stage1.age_label")}</label>
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
            <label className="block text-xs font-medium text-slate-500 mb-2">{t("stage1.sex_label")}</label>
            <div className="flex gap-2">
              {(["Male", "Female"] as const).map(s => (
                <button key={s} onClick={() => set("sex", s)}
                  className={`px-5 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    form.sex === s ? "bg-indigo-600 text-white border-indigo-600" : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                  }`}>
                  {s === "Male" ? t("stage1.male") : t("stage1.female")}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          <CheckItem checked={form.has_cva} onChange={v => set("has_cva", v)} label={t("stage1.cva")} />
          <CheckItem checked={form.has_all_metabolic} onChange={v => set("has_all_metabolic", v)} label={t("stage1.metabolic")} />
        </div>
      </div>

      {/* Symptom sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {sections.map(({ title, subtitle, items }) => (
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
        {loading ? t("stage1.calculating") : t("stage1.submit")}
      </button>

      {result && (
        <div ref={resultRef} className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6 space-y-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-1">{t("stage1.score_label")}</p>
              <p className="text-4xl font-bold text-slate-800">{result.score}<span className="text-xl text-slate-400 font-normal"> / 22</span></p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              result.level === "High"   ? "bg-rose-100 text-rose-700" :
              result.level === "Medium" ? "bg-amber-100 text-amber-700" :
                                          "bg-emerald-100 text-emerald-700"
            }`}>{riskLabel}</span>
          </div>

          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div className={`h-full rounded-full transition-all duration-700 ${barColor}`} style={{ width: `${pct}%` }} />
          </div>

          {result.breakdown.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">{t("stage1.breakdown_label")}</p>
              <div className="flex flex-wrap gap-2">
                {result.breakdown.map((item, i) => (
                  <span key={i} className="text-xs bg-slate-50 border border-slate-200 text-slate-600 px-3 py-1 rounded-full">{item}</span>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={onNext}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm"
          >
            {t("stage1.next")}
          </button>
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
