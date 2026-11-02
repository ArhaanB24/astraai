"use client";

import { useEffect, useState } from "react";
import { getTaxSummary, calculateTax, TaxCalculatePayload } from "@/lib/api";
import {
  Calculator,
  ShieldCheck,
  TrendingDown,
  Info,
  CheckCircle,
  HelpCircle,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Landmark,
  Scale
} from "lucide-react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function TaxDashboardPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [financialYear, setFinancialYear] = useState<string>("2025-26");

  // Form State
  const [salary, setSalary] = useState<number>(0);
  const [otherIncome, setOtherIncome] = useState<number>(0);
  const [deductions80c, setDeductions80c] = useState<number>(0);
  const [deductions80d, setDeductions80d] = useState<number>(0);
  const [age, setAge] = useState<number>(28);

  // Result State
  const [comparison, setComparison] = useState<any>(null);

  async function loadTaxSummary() {
    try {
      const data = await getTaxSummary(financialYear);
      if (data && data.comparison) {
        setComparison(data.comparison);
        if (data.profile_inputs) {
          setSalary(data.profile_inputs.annual_salary ?? 0);
          setOtherIncome(data.profile_inputs.annual_other_income ?? 0);
          setDeductions80c(data.profile_inputs.claimed_80c ?? 0);
          setDeductions80d(data.profile_inputs.claimed_80d ?? 0);
          setAge(data.profile_inputs.age ?? 28);
        }
      }
    } catch (e) {
      console.warn("Failed to load tax summary", e);
    } finally {
      setLoading(false);
    }
  }

  useAutoRefresh(
    () => {
      if (!calculating) {
        loadTaxSummary();
      }
    },
    {
      intervalMs: 5000,
      enabled: isAuthenticated,
      eventScopes: ["tax", "finance", "all"],
      refreshOnFocus: true,
      fetchOnMount: true,
    }
  );

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  async function handleRecalculate() {
    setCalculating(true);
    const payload: TaxCalculatePayload = {
      gross_salary: Number(salary),
      other_income: Number(otherIncome),
      deductions_80c: Number(deductions80c),
      deductions_80d: Number(deductions80d),
      financial_year: financialYear,
      regime: "AUTO",
      is_salaried: true,
      age: Number(age)
    };

    const res = await calculateTax(payload);
    if (res) {
      setComparison(res);
    }
    setCalculating(false);
  }

  const activeRes = comparison?.recommended_regime === "OLD" ? comparison?.old_regime : comparison?.new_regime;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Phase 3 Tax Module
            </span>
            <span className="text-xs text-slate-500 font-medium">Income Tax Act, 1961</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <Calculator className="w-7 h-7 text-purple-400" /> Income Tax Overview & Regime Optimization
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic statutory tax computations, Section 80C/80D optimizations, and Old vs. New Regime comparisons.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* FY Selector */}
          <div className="flex items-center bg-slate-900 border border-border rounded-xl p-1 text-xs">
            <button
              onClick={() => setFinancialYear("2025-26")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                financialYear === "2025-26"
                  ? "bg-purple-500 text-slate-950 shadow-md shadow-purple-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              FY 2025-26 (AY 2026-27)
            </button>
            <button
              onClick={() => setFinancialYear("2024-25")}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                financialYear === "2024-25"
                  ? "bg-purple-500 text-slate-950 shadow-md shadow-purple-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              FY 2024-25 (AY 2025-26)
            </button>
          </div>

          <Link
            href="/tax/chat"
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-lg shadow-purple-500/20"
          >
            <Sparkles className="w-3.5 h-3.5" /> Ask Tax AI Chat
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="py-24 text-center text-slate-400 flex flex-col items-center gap-3">
          <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
          <p className="text-xs font-medium">Computing deterministic tax models...</p>
        </div>
      ) : (
        <>
          {/* Top Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Gross Income</span>
              <p className="text-lg font-extrabold text-white mt-1">₹{comparison?.gross_total_income?.toLocaleString("en-IN") || "0"}</p>
              <span className="text-[10px] text-slate-500">Annual Salary + Other</span>
            </div>

            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Deductions</span>
              <p className="text-lg font-extrabold text-purple-400 mt-1">₹{activeRes?.total_deductions?.toLocaleString("en-IN") || "0"}</p>
              <span className="text-[10px] text-slate-500">Std + 80C + 80D</span>
            </div>

            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Taxable Income</span>
              <p className="text-lg font-extrabold text-white mt-1">₹{activeRes?.taxable_income?.toLocaleString("en-IN") || "0"}</p>
              <span className="text-[10px] text-slate-500">Net of Deductions</span>
            </div>

            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Tax Liability</span>
              <p className="text-lg font-extrabold text-emerald-400 mt-1">₹{activeRes?.total_tax_liability?.toLocaleString("en-IN") || "0"}</p>
              <span className="text-[10px] text-slate-500">Incl. 4% Cess</span>
            </div>

            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Effective Tax Rate</span>
              <p className="text-lg font-extrabold text-blue-400 mt-1">{activeRes?.effective_tax_rate_pct || "0.0"}%</p>
              <span className="text-[10px] text-slate-500">Tax / Gross Income</span>
            </div>

            <div className="bg-card border border-border/80 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Monthly TDS Equivalent</span>
              <p className="text-lg font-extrabold text-amber-400 mt-1">₹{activeRes?.monthly_tax_equivalent?.toLocaleString("en-IN") || "0"}</p>
              <span className="text-[10px] text-slate-500">Approx. Monthly Withholding</span>
            </div>
          </div>

          {/* Regime Comparison Banner */}
          <div className="bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/30 rounded-2xl p-6 relative overflow-hidden">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5" /> Recommended: {comparison?.recommended_regime} TAX REGIME
                  </span>
                  <span className="text-xs text-slate-400 font-semibold">Authoritative Deterministic Analysis</span>
                </div>
                <h2 className="text-xl font-bold text-white tracking-tight">
                  {comparison?.summary}
                </h2>
                <p className="text-xs text-slate-400 max-w-2xl">
                  Based on your declared income of ₹{comparison?.gross_total_income?.toLocaleString("en-IN")} and eligible Section 80C/80D investments, opting for the {comparison?.recommended_regime} Regime maximizes your net in-hand savings.
                </p>
              </div>

              <div className="bg-slate-950/80 border border-purple-500/40 rounded-2xl p-4 shrink-0 text-right min-w-[200px]">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Annual Tax Savings</span>
                <p className="text-2xl font-black text-emerald-400 mt-1">₹{comparison?.tax_savings?.toLocaleString("en-IN") || "0"}</p>
                <span className="text-[10px] text-slate-500">Difference between regimes</span>
              </div>
            </div>
          </div>

          {/* Side-by-Side Old vs New Regime Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* New Tax Regime Card */}
            <div className={`bg-card border rounded-2xl p-6 transition-all ${
              comparison?.recommended_regime === "NEW" ? "border-purple-500 shadow-lg shadow-purple-500/5 ring-1 ring-purple-500/40" : "border-border/80"
            }`}>
              <div className="flex items-center justify-between pb-4 border-b border-border/60">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-base text-white">New Tax Regime</h3>
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-bold">Sec 115BAC</span>
                    {comparison?.recommended_regime === "NEW" && (
                      <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-bold">
                        Cheaper
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Lower slab rates with ₹75,000 flat standard deduction</p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">Total Tax:</span>
                  <p className="text-lg font-black text-white">₹{comparison?.new_regime?.total_tax_liability?.toLocaleString("en-IN")}</p>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Standard Deduction:</span>
                  <span className="font-bold text-white">₹{comparison?.new_regime?.standard_deduction?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Chapter VI-A (80C / 80D):</span>
                  <span className="font-bold text-slate-500">Not Allowed (₹0)</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Net Taxable Income:</span>
                  <span className="font-bold text-white">₹{comparison?.new_regime?.taxable_income?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Base Slab Tax:</span>
                  <span className="font-bold text-white">₹{comparison?.new_regime?.tax_before_rebate?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Section 87A Rebate / Relief:</span>
                  <span className="font-bold text-emerald-400">-₹{(comparison?.new_regime?.section_87a_rebate + comparison?.new_regime?.marginal_relief)?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">4% Health & Education Cess:</span>
                  <span className="font-bold text-white">₹{comparison?.new_regime?.health_and_education_cess?.toLocaleString("en-IN")}</span>
                </div>
              </div>
            </div>

            {/* Old Tax Regime Card */}
            <div className={`bg-card border rounded-2xl p-6 transition-all ${
              comparison?.recommended_regime === "OLD" ? "border-purple-500 shadow-lg shadow-purple-500/5 ring-1 ring-purple-500/40" : "border-border/80"
            }`}>
              <div className="flex items-center justify-between pb-4 border-b border-border/60">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-base text-white">Old Tax Regime</h3>
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-bold">Optional</span>
                    {comparison?.recommended_regime === "OLD" && (
                      <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-bold">
                        Cheaper
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">Higher slab rates with Section 80C & 80D deductions</p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">Total Tax:</span>
                  <p className="text-lg font-black text-white">₹{comparison?.old_regime?.total_tax_liability?.toLocaleString("en-IN")}</p>
                </div>
              </div>

              <div className="mt-4 space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Standard Deduction:</span>
                  <span className="font-bold text-white">₹{comparison?.old_regime?.standard_deduction?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Section 80C (ELSS, PPF, EPF):</span>
                  <span className="font-bold text-emerald-400">₹{comparison?.old_regime?.eligible_80c_deduction?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Section 80D (Health Insurance):</span>
                  <span className="font-bold text-emerald-400">₹{comparison?.old_regime?.eligible_80d_deduction?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Net Taxable Income:</span>
                  <span className="font-bold text-white">₹{comparison?.old_regime?.taxable_income?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">Base Slab Tax:</span>
                  <span className="font-bold text-white">₹{comparison?.old_regime?.tax_before_rebate?.toLocaleString("en-IN")}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-border/40 text-slate-300">
                  <span className="text-slate-400">4% Health & Education Cess:</span>
                  <span className="font-bold text-white">₹{comparison?.old_regime?.health_and_education_cess?.toLocaleString("en-IN")}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Tax Calculator Card */}
          <div className="bg-card border border-border/80 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4 border-b border-border/60 pb-3">
              <div>
                <h3 className="font-bold text-base text-white flex items-center gap-2">
                  <Scale className="w-5 h-5 text-purple-400" /> Interactive Tax Recalculation Engine
                </h3>
                <p className="text-xs text-slate-400">Adjust income and deduction parameters to test custom scenarios in real-time.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Annual Gross Salary (₹)</label>
                <input
                  type="number"
                  value={salary}
                  onChange={(e) => setSalary(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2 text-xs text-white font-medium focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Other Annual Income (₹)</label>
                <input
                  type="number"
                  value={otherIncome}
                  onChange={(e) => setOtherIncome(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2 text-xs text-white font-medium focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Section 80C Claimed (Max ₹1.5L)</label>
                <input
                  type="number"
                  value={deductions80c}
                  onChange={(e) => setDeductions80c(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2 text-xs text-white font-medium focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Section 80D Health Insurance (₹)</label>
                <input
                  type="number"
                  value={deductions80d}
                  onChange={(e) => setDeductions80d(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3.5 py-2 text-xs text-white font-medium focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={handleRecalculate}
                disabled={calculating}
                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs px-6 py-2.5 rounded-xl transition-all shadow-md shadow-purple-500/20 disabled:opacity-50"
              >
                {calculating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                Recalculate Deterministic Tax
              </button>
            </div>
          </div>

          {/* Statutory Informational Disclaimer */}
          <div className="bg-slate-900/60 border border-border/80 rounded-2xl p-4 text-xs text-slate-400 flex items-start gap-3">
            <Info className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-slate-200 text-xs">Statutory Educational Disclaimer</h4>
              <p className="mt-0.5 text-[11px] leading-relaxed text-slate-400">
                All computations generated by ArthaAI are automated estimates based on user-provided inputs and applicable provisions of the <strong>Income Tax Act, 1961</strong> and <strong>Finance Acts</strong>. ArthaAI is an artificial intelligence financial analytics tool and does not provide formal chartered accountancy or legal tax filing advisory. Consult a certified Chartered Accountant (CA) for customized filing advice.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
