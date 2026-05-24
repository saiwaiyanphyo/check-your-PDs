"use client";

import { useState } from "react";
import { Check, Clipboard, Lock, Shield, Target, Trash2, type LucideIcon } from "lucide-react";
import Stage1Form from "@/components/Stage1Form";
import Stage2Upload from "@/components/Stage2Upload";
import CombinedResult from "@/components/CombinedResult";
import { Stage1Result, Stage2Result } from "@/lib/api";

type Tab = "stage1" | "stage2" | "combined" | "about";

export default function Home() {
  const [tab, setTab] = useState<Tab>("stage1");
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [cnnConfidence, setCnnConfidence] = useState<number | null>(null);

  const handleStage1Result = (_r: Stage1Result, score: number) => setRiskScore(score);
  const handleStage2Result = (_r: Stage2Result, confidence: number) => setCnnConfidence(confidence);

  const steps = [
    { id: "stage1" as Tab,   num: 1, label: "Clinical Questionnaire", short: "Stage 1" },
    { id: "stage2" as Tab,   num: 2, label: "Drawing Analysis",        short: "Stage 2" },
    { id: "combined" as Tab, num: 3, label: "Final Assessment",        short: "Combined" },
  ];

  const navTabs: { id: Tab; label: string }[] = [
    { id: "stage1",   label: "Stage 1" },
    { id: "stage2",   label: "Stage 2" },
    { id: "combined", label: "Combined" },
    { id: "about",    label: "About" },
  ];

  const stagesDone = [riskScore !== null, cnnConfidence !== null];

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Top nav */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white text-lg font-bold">P</div>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold text-slate-800 leading-none">PD Screening</p>
              <p className="text-xs text-slate-400 mt-0.5">Parkinson&apos;s Disease Prediction System</p>
            </div>
          </div>

          <nav className="flex items-center gap-1 overflow-x-auto flex-shrink min-w-0">
            {navTabs.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  tab === id
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Progress stepper — only for the 3 main tabs */}
      {tab !== "about" && (
        <div className="bg-white border-b border-slate-100">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex items-center gap-3">
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
                      <span className={`text-xs sm:text-sm font-medium hidden xs:block transition-colors ${
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
              <h2 className="text-xl font-bold text-slate-800">Clinical Questionnaire</h2>
              <p className="text-sm text-slate-500 mt-1">Check all symptoms that apply. This generates a risk score out of 22 points.</p>
            </div>
            <Stage1Form onResult={handleStage1Result} />
          </>
        )}

        {tab === "stage2" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-800">Drawing Analysis</h2>
              <p className="text-sm text-slate-500 mt-1">Upload a hand-drawn spiral or wave pattern for CNN-based motor analysis.</p>
            </div>
            <Stage2Upload onResult={handleStage2Result} />
          </>
        )}

        {tab === "combined" && (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-800">Final Assessment</h2>
              <p className="text-sm text-slate-500 mt-1">Combines clinical score (35%) and drawing analysis (65%) into a final recommendation.</p>
            </div>
            <CombinedResult riskScore={riskScore} cnnConfidence={cnnConfidence} />
          </>
        )}

        {tab === "about" && <AboutTab />}
      </main>
    </div>
  );
}

function AboutTab() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div className="mb-2">
        <h2 className="text-xl font-bold text-slate-800">About This Tool</h2>
        <p className="text-sm text-slate-500 mt-1">Research project — Parkinson&apos;s Disease prediction using MobileNetV2 + clinical scoring.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-700">Two-Stage Architecture</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left px-6 py-3">Stage</th>
                <th className="text-left px-6 py-3">Input</th>
                <th className="text-left px-6 py-3">Method</th>
                <th className="text-left px-6 py-3">Output</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-3 font-medium text-slate-800">Stage 1</td>
                <td className="px-6 py-3 text-slate-600">Clinical questionnaire</td>
                <td className="px-6 py-3 text-slate-600">Point-based scoring</td>
                <td className="px-6 py-3 text-slate-600">Score 0–22</td>
              </tr>
              <tr className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-3 font-medium text-slate-800">Stage 2</td>
                <td className="px-6 py-3 text-slate-600">Hand-drawing image</td>
                <td className="px-6 py-3 text-slate-600">MobileNetV2 CNN</td>
                <td className="px-6 py-3 text-slate-600">PD probability 0–1</td>
              </tr>
              <tr className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-3 font-medium text-slate-800">Combined</td>
                <td className="px-6 py-3 text-slate-600">Both scores</td>
                <td className="px-6 py-3 text-slate-600">Weighted fusion 35/65</td>
                <td className="px-6 py-3 text-slate-600">Final recommendation</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-700 mb-4">Risk Level Reference</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          {[
            { dot: "bg-emerald-400", label: "Low",    range: "0–2 pts",  weight: "×0.3", desc: "Few or no risk factors" },
            { dot: "bg-amber-400",   label: "Medium", range: "3–5 pts",  weight: "×1.0", desc: "Some risk factors present" },
            { dot: "bg-rose-400",    label: "High",   range: "6+ pts",   weight: "×1.5", desc: "Multiple risk factors" },
          ].map(({ dot, label, range, weight, desc }) => (
            <div key={label} className="bg-slate-50 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-2.5 h-2.5 rounded-full ${dot}`} />
                <span className="font-semibold text-slate-800">{label}</span>
              </div>
              <p className="text-slate-500 text-xs">{range} · Weight {weight}</p>
              <p className="text-slate-600 text-xs mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-700 mb-3">Research Team</h3>
        <div className="space-y-2 text-sm text-slate-600">
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Supervisor: Dr. Sasiporn Usanavasin</div>
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Sai Wai Yan Phyo</div>
          <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />Kantapon Makpisut</div>
        </div>
        <p className="text-xs text-slate-400 mt-4">Data: 1,340 PD patient records — Udon Thani, Thailand (2567–2568 BE)</p>
      </div>

      {/* PDPA Thailand Notice */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
          <Shield className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <h3 className="font-semibold text-slate-700">Personal Data Protection Notice (PDPA)</h3>
        </div>
        <div className="p-5 sm:p-6 space-y-5 text-sm text-slate-600">
          <p className="leading-relaxed">
            This tool operates in accordance with the{" "}
            <span className="font-medium text-slate-800">
              Personal Data Protection Act B.E. 2562 (2019)
            </span>{" "}
            of Thailand (พระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล พ.ศ. ๒๕๖๒).
            Health-related information — including symptom responses and hand-drawing images — constitutes{" "}
            <span className="font-medium text-slate-800">sensitive personal data</span> under Section 26 of the PDPA and is handled accordingly.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {(
              [
                {
                  Icon: Clipboard,
                  title: "Data Collected",
                  body: "Symptom questionnaire responses and hand-drawing images submitted voluntarily for screening purposes.",
                },
                {
                  Icon: Target,
                  title: "Purpose of Processing",
                  body: "Preliminary Parkinson's disease risk screening and academic research. Data is not used for any commercial purpose.",
                },
                {
                  Icon: Trash2,
                  title: "Data Retention",
                  body: "Submitted images and responses are processed in memory only and are not stored, logged, or retained on any server after the response is returned.",
                },
                {
                  Icon: Lock,
                  title: "Data Sharing",
                  body: "No personal data is shared with third parties. Aggregate anonymised results may be used for research publication.",
                },
              ] as { Icon: LucideIcon; title: string; body: string }[]
            ).map(({ Icon, title, body }) => (
              <div key={title} className="bg-slate-50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-1.5">
                  <Icon className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                  <p className="font-semibold text-slate-700 text-xs uppercase tracking-wide">{title}</p>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          <div>
            <p className="font-semibold text-slate-700 mb-2">Your Rights Under PDPA</p>
            <div className="flex flex-wrap gap-2">
              {[
                "Right to be informed",
                "Right of access",
                "Right to rectification",
                "Right to erasure",
                "Right to restrict processing",
                "Right to data portability",
                "Right to object",
              ].map(right => (
                <span key={right} className="text-xs bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1 rounded-full">
                  {right}
                </span>
              ))}
            </div>
          </div>

          {/* <div className="bg-slate-50 rounded-xl p-4 text-xs text-slate-500 leading-relaxed">
            <span className="font-medium text-slate-700">Data Controller: </span>
            Dr. Sasiporn Usanavasin (Supervisor), Research Team — Udon Thani, Thailand.
            For any data protection enquiries or to exercise your rights, please contact the research team through your institution.
          </div> */}

          <p className="text-xs text-slate-400 leading-relaxed">
            By using this tool you acknowledge that you have read this notice and voluntarily provide any data entered.
            Use of this tool implies consent to process the submitted data solely for the stated screening purpose.
          </p>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-sm text-amber-800">
        <p className="font-semibold mb-1">Medical Disclaimer</p>
        <p className="text-amber-700 leading-relaxed">This tool is for preliminary screening only and does not constitute a medical diagnosis. Always consult a qualified healthcare professional for evaluation of Parkinson&apos;s disease.</p>
      </div>
    </div>
  );
}
