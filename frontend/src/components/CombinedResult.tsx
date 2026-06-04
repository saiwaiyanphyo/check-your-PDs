"use client";

import { useState } from "react";
import { fetchCombined, CombinedResult } from "@/lib/api";
import { useLocale } from "@/lib/i18n";

interface Props { riskScore: number | null; cnnConfidence: number | null }

export default function CombinedResultPanel({ riskScore, cnnConfidence }: Props) {
  const { t } = useLocale();
  const [result, setResult] = useState<CombinedResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (riskScore === null || cnnConfidence === null) return;
    setLoading(true); setError("");
    try { setResult(await fetchCombined(riskScore, cnnConfidence)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Request failed"); }
    finally { setLoading(false); }
  };

  const missing = riskScore === null || cnnConfidence === null;
  const pct = result ? Math.round(result.combined_score * 100) : 0;

  const style = result
    ? result.combined_score >= 0.7
      ? { bar: "bg-rose-500",    badge: "bg-rose-100 text-rose-700",       ring: "ring-rose-200" }
      : result.combined_score >= 0.45
      ? { bar: "bg-amber-400",   badge: "bg-amber-100 text-amber-700",     ring: "ring-amber-200" }
      : { bar: "bg-emerald-500", badge: "bg-emerald-100 text-emerald-700", ring: "ring-emerald-200" }
    : null;

  return (
    <div className="space-y-5">

      {/* Inputs summary */}
      <div className="grid grid-cols-2 gap-4">
        <InputCard label={t("combined.stage1_card")} value={riskScore !== null ? `${riskScore} / 22` : null} unit="" notCompleted={t("combined.not_completed")} />
        <InputCard label={t("combined.stage2_card")} value={cnnConfidence !== null ? `${Math.round(cnnConfidence * 100)}` : null} unit="%" notCompleted={t("combined.not_completed")} />
      </div>

      {missing && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-700">
          {t("combined.incomplete_warning")}
        </div>
      )}

      {error && <p className="text-sm text-rose-500 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">{error}</p>}

      <button onClick={submit} disabled={missing || loading}
        className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm">
        {loading ? t("combined.generating") : t("combined.submit")}
      </button>

      {result && style && (
        <div className="space-y-4">

          {/* Score card */}
          <div className={`bg-white rounded-2xl border border-slate-200 p-4 sm:p-6 ring-2 ${style.ring}`}>
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-1">{t("combined.score_label")}</p>
                <p className="text-5xl font-bold text-slate-800">{pct}<span className="text-2xl text-slate-400 font-normal">%</span></p>
              </div>
              <span className={`px-3 py-1.5 rounded-full text-sm font-bold flex-shrink-0 ${style.badge}`}>{result.recommendation}</span>
            </div>

            <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-5">
              <div className={`h-full rounded-full transition-all duration-700 ${style.bar}`} style={{ width: `${pct}%` }} />
            </div>

            <p className="text-sm text-slate-700 leading-relaxed">{result.advice}</p>
          </div>

          {/* Breakdown table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="px-4 sm:px-6 py-4 border-b border-slate-100">
              <p className="text-sm font-semibold text-slate-700">{t("combined.breakdown_title")}</p>
            </div>
            {/* Desktop table */}
            <table className="hidden sm:table w-full text-sm">
              <thead className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wide">
                <tr>
                  <th className="text-left px-6 py-3">{t("combined.col_component")}</th>
                  <th className="text-left px-6 py-3">{t("combined.col_value")}</th>
                  <th className="text-right px-6 py-3">{t("combined.col_weight")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="px-6 py-3 text-slate-600">{t("combined.clinical_row")}</td>
                  <td className="px-6 py-3 font-medium text-slate-800">
                    {riskScore} / 22
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                      result.risk_level === "High" ? "bg-rose-100 text-rose-700" :
                      result.risk_level === "Medium" ? "bg-amber-100 text-amber-700" :
                      "bg-emerald-100 text-emerald-700"
                    }`}>{result.risk_level}</span>
                  </td>
                  <td className="px-6 py-3 text-right text-slate-500">35% × {result.risk_weight}</td>
                </tr>
                <tr>
                  <td className="px-6 py-3 text-slate-600">{t("combined.drawing_row")}</td>
                  <td className="px-6 py-3 font-medium text-slate-800">{Math.round((cnnConfidence ?? 0) * 100)}%</td>
                  <td className="px-6 py-3 text-right text-slate-500">65%</td>
                </tr>
                <tr className="bg-indigo-50">
                  <td className="px-6 py-3 font-bold text-slate-800">{t("combined.combined_row")}</td>
                  <td className="px-6 py-3 font-bold text-indigo-700 text-base">{pct}%</td>
                  <td className="px-6 py-3" />
                </tr>
              </tbody>
            </table>
            {/* Mobile stacked cards */}
            <div className="sm:hidden divide-y divide-slate-100">
              <div className="px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400 mb-0.5">{t("combined.clinical_row")}</p>
                  <p className="font-medium text-slate-800">
                    {riskScore} / 22
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                      result.risk_level === "High" ? "bg-rose-100 text-rose-700" :
                      result.risk_level === "Medium" ? "bg-amber-100 text-amber-700" :
                      "bg-emerald-100 text-emerald-700"
                    }`}>{result.risk_level}</span>
                  </p>
                </div>
                <p className="text-xs text-slate-500">35% × {result.risk_weight}</p>
              </div>
              <div className="px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400 mb-0.5">{t("combined.drawing_row")}</p>
                  <p className="font-medium text-slate-800">{Math.round((cnnConfidence ?? 0) * 100)}%</p>
                </div>
                <p className="text-xs text-slate-500">65%</p>
              </div>
              <div className="px-4 py-3 bg-indigo-50 flex items-center justify-between">
                <p className="font-bold text-slate-800">{t("combined.combined_row")}</p>
                <p className="font-bold text-indigo-700 text-base">{pct}%</p>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 sm:p-5 text-sm">
            <p className="font-semibold text-amber-800 mb-1">{t("combined.disclaimer_title")}</p>
            <p className="text-amber-700 leading-relaxed">{t("combined.disclaimer_body")}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function InputCard({ label, value, unit, notCompleted }: { label: string; value: string | null; unit: string; notCompleted: string }) {
  return (
    <div className={`rounded-2xl border p-5 ${value !== null ? "bg-white border-slate-200" : "bg-slate-50 border-slate-200 border-dashed"}`}>
      <p className="text-xs text-slate-400 mb-2">{label}</p>
      {value !== null
        ? <p className="text-2xl font-bold text-slate-800">{value}<span className="text-base font-normal text-slate-400">{unit}</span></p>
        : <p className="text-sm text-slate-400 italic">{notCompleted}</p>
      }
    </div>
  );
}
