"use client";

import { useState, useEffect } from "react";
import { calculateCarAffordabilityApi } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { Car, Calculator, ShieldCheck, AlertTriangle, CheckCircle2, Bot, Sparkles, BookOpen } from "lucide-react";

import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function CarAffordabilityPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [carPrice, setCarPrice] = useState(1500000);
  const [downPayment, setDownPayment] = useState(300000);
  const [interestRate, setInterestRate] = useState(8.5);
  const [tenureYears, setTenureYears] = useState(5);

  const [res, setRes] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const isInvalidDownPayment = downPayment >= carPrice && carPrice > 0;

  const handleCalculate = async () => {
    if (!isAuthenticated) return;
    if (isInvalidDownPayment || carPrice <= 0) return;
    try {
      const data = await calculateCarAffordabilityApi({
        car_price: carPrice,
        down_payment: downPayment,
        interest_rate_pct: interestRate,
        tenure_years: tenureYears
      });
      setRes(data);
    } catch (e) {
      console.warn("Affordability calculation notice:", e);
    } finally {
      setLoading(false);
    }
  };

  useAutoRefresh(handleCalculate, {
    intervalMs: 8000,
    enabled: isAuthenticated && !isInvalidDownPayment,
    eventScopes: ["finance", "all"],
    refreshOnFocus: true,
    fetchOnMount: true,
  });

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Banner */}
      <div className="bg-card p-6 rounded-2xl border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Official Faculty Demo Tool
          </span>
          <h1 className="text-xl font-black text-white flex items-center gap-2 mt-1">
            <Car className="w-5 h-5 text-emerald-400" /> Car Purchase Affordability Calculator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Evaluates loan EMI, post-purchase cash flow, emergency fund impact, and active financial goal compatibility.
          </p>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading || isInvalidDownPayment}
          className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg transition-all flex items-center gap-2 shrink-0"
        >
          <Calculator className="w-4 h-4" /> {loading ? "Evaluating..." : "Re-Calculate Affordability"}
        </button>
      </div>

      {isInvalidDownPayment && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-center gap-3 text-rose-300 text-xs">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
          <span>
            <strong>Invalid Input:</strong> Down payment ({formatINR(downPayment)}) cannot be greater than or equal to the total on-road vehicle price ({formatINR(carPrice)}).
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Parameters Form */}
        <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
          <h3 className="text-sm font-bold text-white border-b border-border/80 pb-2">Purchase Parameters</h3>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Car On-Road Price (₹)</label>
            <input
              type="number"
              value={carPrice}
              onChange={(e) => setCarPrice(Number(e.target.value))}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 focus:border-emerald-500 outline-none"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Down Payment (₹)</label>
            <input
              type="number"
              value={downPayment}
              onChange={(e) => setDownPayment(Number(e.target.value))}
              className={`w-full bg-surface border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none ${
                isInvalidDownPayment ? "border-rose-500 focus:border-rose-500" : "border-border focus:border-emerald-500"
              }`}
            />
            {isInvalidDownPayment && (
              <p className="text-[10px] text-rose-400 mt-1">Must be less than total price</p>
            )}
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Loan Interest Rate (% p.a.)</label>
            <input
              type="number"
              step="0.1"
              value={interestRate}
              onChange={(e) => setInterestRate(Number(e.target.value))}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 focus:border-emerald-500 outline-none"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Loan Tenure (Years)</label>
            <select
              value={tenureYears}
              onChange={(e) => setTenureYears(Number(e.target.value))}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 focus:border-emerald-500 outline-none"
            >
              <option value={3}>3 Years (36 Months)</option>
              <option value={4}>4 Years (48 Months)</option>
              <option value={5}>5 Years (60 Months)</option>
              <option value={7}>7 Years (84 Months)</option>
            </select>
          </div>

          {res?.financial_health && (
            <div className="p-3.5 rounded-xl bg-surface/60 border border-border text-[11px] space-y-1.5 text-slate-300">
              <span className="font-bold text-white text-xs block border-b border-border/60 pb-1">Shared Profile Baseline</span>
              <div className="flex justify-between">
                <span>Monthly Income:</span>
                <span className="font-bold text-white">{formatINR(res.financial_health.monthly_income)}</span>
              </div>
              <div className="flex justify-between">
                <span>Monthly Expenses:</span>
                <span className="font-bold text-slate-300">{formatINR(res.financial_health.monthly_expenses)}</span>
              </div>
              <div className="flex justify-between">
                <span>Existing EMIs:</span>
                <span className="font-bold text-amber-400">{formatINR(res.financial_health.monthly_emis)}</span>
              </div>
              <div className="flex justify-between">
                <span>Emergency Buffer:</span>
                <span className="font-bold text-emerald-400">{formatINR(res.financial_health.emergency_fund_balance)} ({res.financial_health.emergency_coverage_months} mos)</span>
              </div>
            </div>
          )}
        </div>

        {/* Deterministic Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {res && (
            <>
              {/* Rating Banner */}
              <div className={`p-5 rounded-2xl border flex items-center justify-between ${
                res.affordability_assessment === "HIGHLY_AFFORDABLE" ? "bg-emerald-950/30 border-emerald-800/50 text-emerald-300" :
                res.affordability_assessment === "MODERATELY_AFFORDABLE" ? "bg-blue-950/30 border-blue-800/50 text-blue-300" :
                res.affordability_assessment === "STRETCHED" ? "bg-amber-950/30 border-amber-800/50 text-amber-300" :
                "bg-rose-950/30 border-rose-800/50 text-rose-300"
              }`}>
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Deterministic Assessment Rating</span>
                  <h2 className="text-xl font-black mt-0.5">{res.affordability_assessment}</h2>
                  <p className="text-xs opacity-90 mt-1">
                    Calculated using your exact monthly cash surplus, DTI %, and emergency coverage buffer.
                  </p>
                </div>
                <div className="w-12 h-12 rounded-2xl bg-surface/40 border border-white/10 flex items-center justify-center font-extrabold text-xl shrink-0">
                  {res.affordability_assessment === "HIGHLY_AFFORDABLE" ? "✓" : "!"}
                </div>
              </div>

              {/* Key Metric Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-xl bg-card border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Loan Amount</span>
                  <p className="text-lg font-bold text-white mt-1">{formatINR(res.loan_amount)}</p>
                </div>
                <div className="p-4 rounded-xl bg-card border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">New Monthly EMI</span>
                  <p className="text-lg font-bold text-amber-400 mt-1">{formatINR(res.new_monthly_emi)}</p>
                </div>
                <div className="p-4 rounded-xl bg-card border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Post Surplus</span>
                  <p className="text-lg font-bold text-emerald-400 mt-1">{formatINR(res.post_purchase_monthly_surplus)}</p>
                </div>
                <div className="p-4 rounded-xl bg-card border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">New DTI %</span>
                  <p className="text-lg font-bold text-blue-400 mt-1">{res.new_debt_to_income_pct}%</p>
                </div>
              </div>

              {/* Detailed Impact Analysis Table */}
              <div className="p-5 rounded-2xl bg-card border border-border space-y-3">
                <h4 className="text-sm font-bold text-white">Cash Flow & Liquidity Impact Breakdown</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 rounded-xl bg-surface border border-border space-y-1">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Total Loan Interest Payable</span>
                    <p className="text-base font-bold text-white">{formatINR(res.total_loan_interest)}</p>
                    <p className="text-[10px] text-slate-400">Over {res.loan_tenure_years} years ({res.loan_tenure_months} EMIs)</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-surface border border-border space-y-1">
                    <span className="text-[10px] uppercase text-slate-400 font-semibold">Emergency Buffer Post-Purchase</span>
                    <p className="text-base font-bold text-emerald-400">{res.post_purchase_emergency_coverage_months} months</p>
                    <p className="text-[10px] text-slate-400">Remaining Buffer: {formatINR(res.emergency_fund_balance_after_down_payment)}</p>
                  </div>
                </div>
              </div>

              {/* AI Advisory & Grounded Heuristic Explanation */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/30 via-card to-slate-900 border border-emerald-800/40 space-y-3">
                <div className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-sm font-bold text-white">Personal Finance AI Grounded Advisory</h3>
                </div>

                <div className="text-xs text-slate-300 space-y-2 leading-relaxed">
                  <p>
                    Your proposed car purchase of <span className="font-bold text-white">{formatINR(res.purchase_price)}</span> with a down payment of <span className="font-bold text-white">{formatINR(res.down_payment)}</span> yields a new EMI of <span className="font-bold text-amber-400">{formatINR(res.new_monthly_emi)}</span>.
                  </p>

                  <div className="p-3 rounded-xl bg-surface/80 border border-border text-[11px] space-y-1">
                    <div className="font-bold text-emerald-400 flex items-center gap-1">
                      <BookOpen className="w-3.5 h-3.5" /> Cited 20/4/10 Rule of Thumb Heuristic:
                    </div>
                    <p className="text-slate-400">
                      *(Rule of thumb guideline: 20% down payment, 4-year tenure max, transportation costs &lt; 10% income. Note: This is an advisory heuristic guideline rather than an absolute rule.)*
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
