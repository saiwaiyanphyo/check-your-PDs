"use client";

import { useState } from "react";
import { Check, Clipboard, Info, Lock, Shield, Target, Trash2, type LucideIcon } from "lucide-react";
import Stage1Form from "@/components/Stage1Form";
import Stage2Upload from "@/components/Stage2Upload";
import CombinedResult from "@/components/CombinedResult";
import { Stage1Result, Stage2Result } from "@/lib/api";
import { useLocale } from "@/lib/i18n";

type Tab = "stage1" | "stage2" | "combined" | "about";

export default function Home() {
  const [tab, setTab] = useState<Tab>("stage1");
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [cnnConfidence, setCnnConfidence] = useState<number | null>(null);
  const { locale, t, switchLocale } = useLocale();

  const handleStage1Result = (_r: Stage1Result, score: number) => setRiskScore(score);
  const handleStage2Result = (_r: Stage2Result, confidence: number) => setCnnConfidence(confidence);

  const steps = [
    { id: "stage1" as Tab,   num: 1, label: t("stepper.stage1_long"), short: t("stepper.stage1_short") },
    { id: "stage2" as Tab,   num: 2, label: t("stepper.stage2_long"), short: t("stepper.stage2_short") },
    { id: "combined" as Tab, num: 3, label: t("stepper.stage3_long"), short: t("stepper.stage3_short") },
  ];

  const stagesDone = [riskScore !== null, cnnConfidence !== null];

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Top nav */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <button
            onClick={() => setTab("stage1")}
            className="flex items-center gap-3 flex-shrink-0 group"
          >
            <div className="w-9 h-9 rounded-xl bg-indigo-600 group-hover:bg-indigo-700 transition-colors flex items-center justify-center text-white text-lg font-bold">P</div>
            <div>
              <p className="text-sm font-semibold text-slate-800 leading-none">{t("nav.brand")}</p>
              <p className="text-xs text-slate-400 mt-0.5 hidden sm:block">{t("nav.tagline")}</p>
            </div>
          </button>

          <div className="flex items-center gap-2">
            {/* Language toggle */}
            <div className="flex items-center rounded-lg border border-slate-200 overflow-hidden text-xs font-semibold">
              <button
                onClick={() => switchLocale("en")}
                className={`px-2.5 py-1.5 transition-colors ${locale === "en" ? "bg-indigo-600 text-white" : "text-slate-500 hover:bg-slate-50"}`}
              >
                EN
              </button>
              <button
                onClick={() => switchLocale("my")}
                className={`px-2.5 py-1.5 transition-colors ${locale === "my" ? "bg-indigo-600 text-white" : "text-slate-500 hover:bg-slate-50"}`}
              >
                မြန်မာ
              </button>
            </div>

            <button
              onClick={() => setTab("about")}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === "about"
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
              }`}
            >
              <Info className="w-4 h-4" />
              <span className="hidden sm:inline">{t("nav.about")}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Progress stepper */}
      {tab !== "about" && (
        <div className="bg-white border-b border-slate-100">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex items-center gap-2 sm:gap-3">
              {steps.map((s, i) => {
                const done = stagesDone[i] ?? false;
                const active = tab === s.id;
                return (
                  <div key={s.id} className="flex items-center gap-2 sm:gap-3">
                    <button onClick={() => setTab(s.id)} className="flex items-center gap-1.5 sm:gap-2 group">
                      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all flex-shrink-0 ${
                        done ? "bg-emerald-500 text-white" :
                        active ? "bg-indigo-600 text-white" :
                        "bg-slate-100 text-slate-400"
                      }`}>
                        {done ? <Check className="w-3.5 h-3.5" /> : s.num}
                      </span>
                      <span className={`text-xs sm:text-sm font-medium transition-colors ${
                        active ? "text-indigo-700" : done ? "text-emerald-600" : "text-slate-400"
                      }`}>
                        <span className="hidden sm:inline">{s.label}</span>
                        <span className="sm:hidden">{s.short}</span>
                      </span>
                    </button>
                    {i < steps.length - 1 && (
                      <div className={`h-px w-6 sm:w-10 flex-shrink-0 ${stagesDone[i] ? "bg-emerald-300" : "bg-slate-200"}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {tab === "stage1" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-800">{t("stage1.title")}</h2>
              <p className="text-sm text-slate-500 mt-1">{t("stage1.subtitle")}</p>
            </div>
            <Stage1Form onResult={handleStage1Result} onNext={() => setTab("stage2")} />
          </>
        )}

        {tab === "stage2" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-800">{t("stage2.title")}</h2>
              <p className="text-sm text-slate-500 mt-1">{t("stage2.subtitle")}</p>
            </div>
            <Stage2Upload onResult={handleStage2Result} onNext={() => setTab("combined")} />
          </>
        )}

        {tab === "combined" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-800">{t("combined.title")}</h2>
              <p className="text-sm text-slate-500 mt-1">{t("combined.subtitle")}</p>
            </div>
            <CombinedResult riskScore={riskScore} cnnConfidence={cnnConfidence} />
          </>
        )}

        {tab === "about" && <AboutTab onBack={() => setTab("stage1")} />}
      </main>
    </div>
  );
}

function AboutTab({ onBack }: { onBack: () => void }) {
  const { t } = useLocale();

  const pdpaCards: { Icon: LucideIcon; titleKey: string; bodyKey: string }[] = [
    { Icon: Clipboard, titleKey: "about.collected_title", bodyKey: "about.collected_body" },
    { Icon: Target,    titleKey: "about.purpose_title",   bodyKey: "about.purpose_body"   },
    { Icon: Trash2,    titleKey: "about.retention_title", bodyKey: "about.retention_body" },
    { Icon: Lock,      titleKey: "about.sharing_title",   bodyKey: "about.sharing_body"   },
  ];

  const rights = [
    "about.right_informed", "about.right_access", "about.right_rectification",
    "about.right_erasure",  "about.right_restrict", "about.right_portability", "about.right_object",
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="mb-2">
        <h2 className="text-xl font-bold text-slate-800">{t("about.title")}</h2>
        <p className="text-sm text-slate-500 mt-1">{t("about.subtitle")}</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-700">{t("about.arch_title")}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-6 py-3">{t("about.col_stage")}</th>
                <th className="text-left px-6 py-3">{t("about.col_input")}</th>
                <th className="text-left px-6 py-3">{t("about.col_method")}</th>
                <th className="text-left px-6 py-3">{t("about.col_output")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {[
                { stage: t("stepper.stage1_long"), input: t("about.s1_input"), method: t("about.s1_method"), output: t("about.s1_output") },
                { stage: t("stepper.stage2_long"), input: t("about.s2_input"), method: t("about.s2_method"), output: t("about.s2_output") },
                { stage: t("stepper.stage3_long"), input: t("about.sc_input"), method: t("about.sc_method"), output: t("about.sc_output") },
              ].map(({ stage, input, method, output }) => (
                <tr key={stage} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-3 font-medium text-slate-800">{stage}</td>
                  <td className="px-6 py-3 text-slate-600">{input}</td>
                  <td className="px-6 py-3 text-slate-600">{method}</td>
                  <td className="px-6 py-3 text-slate-600">{output}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-700 mb-4">{t("about.risk_title")}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          {[
            { dot: "bg-emerald-400", labelKey: "about.low_label",    rangeKey: "about.low_range",    weightKey: "about.low_weight",    descKey: "about.low_desc" },
            { dot: "bg-amber-400",   labelKey: "about.medium_label", rangeKey: "about.medium_range", weightKey: "about.medium_weight", descKey: "about.medium_desc" },
            { dot: "bg-rose-400",    labelKey: "about.high_label",   rangeKey: "about.high_range",   weightKey: "about.high_weight",   descKey: "about.high_desc" },
          ].map(({ dot, labelKey, rangeKey, weightKey, descKey }) => (
            <div key={labelKey} className="bg-slate-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-2.5 h-2.5 rounded-full ${dot}`} />
                <span className="font-semibold text-slate-800">{t(labelKey)}</span>
              </div>
              <p className="text-slate-500 text-xs">{t(rangeKey)} · Weight {t(weightKey)}</p>
              <p className="text-slate-600 text-xs mt-1">{t(descKey)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-700 mb-3">{t("about.team_title")}</h3>
        <div className="space-y-2 text-sm text-slate-600">
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Supervisor: Dr. Sasiporn Usanavasin</div>
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Sai Wai Yan Phyo</div>
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Kantapon Makpisut</div>
        </div>
        <p className="text-xs text-slate-400 mt-4">{t("about.data_note")}</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
          <Shield className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <h3 className="font-semibold text-slate-700">{t("about.pdpa_title")}</h3>
        </div>
        <div className="p-5 sm:p-6 space-y-5 text-sm text-slate-600">
          <p className="leading-relaxed">{t("about.pdpa_body")}</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {pdpaCards.map(({ Icon, titleKey, bodyKey }) => (
              <div key={titleKey} className="bg-slate-50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <Icon className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <p className="font-semibold text-slate-700 text-xs uppercase tracking-wide">{t(titleKey)}</p>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">{t(bodyKey)}</p>
              </div>
            ))}
          </div>

          <div>
            <p className="font-semibold text-slate-700 mb-2">{t("about.rights_title")}</p>
            <div className="flex flex-wrap gap-2">
              {rights.map(key => (
                <span key={key} className="text-xs bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1 rounded-full">
                  {t(key)}
                </span>
              ))}
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">{t("about.consent_note")}</p>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-sm text-amber-800">
        <p className="font-semibold mb-1">{t("about.disclaimer_title")}</p>
        <p className="text-amber-700 leading-relaxed">{t("about.disclaimer_body")}</p>
      </div>

      <button
        onClick={onBack}
        className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm"
      >
        {t("about.back")}
      </button>
    </div>
  );
}
