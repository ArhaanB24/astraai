"use client";

import { useState } from "react";
import { simulateScenarioApi } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { Sliders, Sparkles, AlertCircle } from "lucide-react";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function WhatIfScenariosPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [scenarioType, setScenarioType] = useState("SALARY_CHANGE");
  const [paramValue, setParamValue] = useState(15);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    let params: any = {};
    if (scenarioType === "SALARY_CHANGE") params = { change_percentage: paramValue };
    else if (scenarioType === "EXPENSE_INCREASE") params = { increase_percentage: paramValue };
    else if (scenarioType === "INCREASE_SIP") params = { additional_monthly_sip: paramValue * 1000 };
    else if (scenarioType === "INCOME_LOSS") params = { duration_months: paramValue };

    try {
      const data = await simulateScenarioApi({ scenario_type: scenarioType, scenario_params: params });
      if (data) {
        setResult(data);
      } else {
        setResult(null);
        setError("Unable to run simulation. Please check the backend connection.");
      }
    } catch (err: any) {
      console.error("[Scenario Error]", err);
      setResult(null);
      setError("Unable to run simulation. Please check the backend connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="p-6 rounded-2xl bg-card border border-border flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Non-Destructive Simulator Engine
          </span>
          <h1 className="text-xl font-black text-white mt-1">What-If Scenario Simulator</h1>
          <p className="text-xs text-slate-400 mt-1">
            Simulates financial decisions in an isolated memory buffer without mutating your baseline profile.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Card */}
        <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
          <h3 className="text-sm font-bold text-white border-b border-border/80 pb-2">Select Scenario</h3>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Scenario Type</label>
            <select
              value={scenarioType}
              onChange={(e) => setScenarioType(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
            >
              <option value="SALARY_CHANGE">Salary Change (%)</option>
              <option value="EXPENSE_INCREASE">Expense Increase (%)</option>
              <option value="INCREASE_SIP">Increase Monthly SIP (₹k)</option>
              <option value="INCOME_LOSS">Temporary Income Loss (Months)</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase">Parameter Value</label>
            <input
              type="number"
              value={paramValue}
              onChange={(e) => setParamValue(Number(e.target.value))}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
            />
          </div>

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs py-3 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2"
          >
            {loading ? "Running Simulation..." : "Run Non-Destructive Simulation"}
          </button>

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-center gap-2 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Impact Panel */}
        <div className="lg:col-span-2">
          {result ? (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <div className="flex items-center justify-between border-b border-border/80 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-emerald-400" /> Simulation Impact Summary
                </h3>
                <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                  Non-Destructive Simulation
                </span>
              </div>

              <div className="p-4 rounded-xl bg-surface border border-border text-xs text-slate-200 leading-relaxed font-medium">
                {result.impact_summary}
              </div>

              {/* Side by Side Comparison Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface border border-border space-y-1.5">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Baseline Monthly Surplus</span>
                  <p className="text-xl font-bold text-slate-300">{formatINR(result.baseline_health.monthly_surplus)}</p>
                  <span className="text-[10px] text-slate-400 block">Baseline Income: {formatINR(result.baseline_health.monthly_income)}</span>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border space-y-1.5">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Scenario Monthly Surplus</span>
                  <p className="text-xl font-bold text-emerald-400">{formatINR(result.scenario_health.monthly_surplus)}</p>
                  <span className="text-[10px] text-slate-400 block">Scenario Income: {formatINR(result.scenario_health.monthly_income)}</span>
                </div>
              </div>

              {/* Delta Impact Indicators */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Surplus Change</span>
                  <p className={`text-xl font-black mt-1 ${result.deltas.surplus_change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {result.deltas.surplus_change >= 0 ? "+" : ""}{formatINR(result.deltas.surplus_change)} / mo
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Health Score Change</span>
                  <p className={`text-xl font-black mt-1 ${result.deltas.health_score_change >= 0 ? "text-emerald-400" : "text-amber-400"}`}>
                    {result.deltas.health_score_change >= 0 ? "+" : ""}{result.deltas.health_score_change} pts
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 rounded-2xl bg-card border border-border border-dashed flex flex-col items-center justify-center text-center">
              <Sliders className="w-8 h-8 text-slate-500 mb-2" />
              <h4 className="text-sm font-bold text-slate-300">No Simulation Run Yet</h4>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Select a scenario parameter on the left and click &quot;Run Non-Destructive Simulation&quot; to see real-time financial cash flow impacts.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
