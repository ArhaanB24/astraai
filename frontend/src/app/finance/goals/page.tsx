"use client";

import { useState, useEffect } from "react";
import { fetchFinanceSummary } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { Target, Calendar, TrendingUp, CheckCircle2, UserCheck } from "lucide-react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function FinancialGoalsPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [summary, setSummary] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchFinanceSummary();
      setSummary(data);
    } catch (e) {
      console.warn("Goals summary error", e);
    } finally {
      setLoadingData(false);
    }
  };

  useAutoRefresh(loadData, {
    intervalMs: 4000,
    enabled: isAuthenticated,
    eventScopes: ["goals", "finance", "all"],
    refreshOnFocus: true,
    fetchOnMount: true,
  });

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  if (loadingData && !summary) {
    return <div className="p-6 text-emerald-400 font-semibold text-xs">Loading Goals Tracker...</div>;
  }

  const goals = summary?.goals || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="p-6 rounded-2xl bg-card border border-border flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Goal Tracker & PMT Compounding Engine
          </span>
          <h1 className="text-xl font-black text-white mt-1">Financial Goals & Required Monthly Contribution</h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic FV compounding math calculating exact monthly SIP needed to reach every milestone.
          </p>
        </div>
      </div>

      {goals.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {goals.map((goal: any) => (
            <div key={goal.id} className="p-5 rounded-2xl bg-card border border-border space-y-3">
              <div className="flex items-center justify-between border-b border-border/80 pb-2">
                <div>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                    {goal.priority} Priority
                  </span>
                  <h3 className="text-base font-bold text-white mt-0.5">{goal.name}</h3>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Target Year</span>
                  <p className="text-sm font-bold text-white">{goal.target_year}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase">Target Amount</span>
                  <p className="text-base font-bold text-white mt-0.5">{formatINR(goal.target_amount)}</p>
                </div>
                <div className="p-3 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase">Current Accumulation</span>
                  <p className="text-base font-bold text-emerald-400 mt-0.5">{formatINR(goal.current_amount)}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase font-semibold text-emerald-400">Required Monthly SIP</span>
                  <p className="text-lg font-black text-white mt-0.5">
                    {formatINR(goal.required_monthly_contribution)} / mo
                  </p>
                </div>
                <span className="text-[11px] text-slate-400 font-semibold">@ {goal.expected_return_pct}% p.a.</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center bg-card rounded-2xl border border-border text-slate-400 space-y-3">
          <Target className="w-8 h-8 mx-auto text-emerald-400" />
          <h3 className="text-sm font-bold text-white">No Financial Goals Defined Yet</h3>
          <p className="text-xs max-w-md mx-auto">
            Complete the onboarding questionnaire to initialize your target financial milestones and required SIP calculations.
          </p>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 font-bold text-slate-950 text-xs px-4 py-2 rounded-xl transition-all"
          >
            Start Onboarding
          </Link>
        </div>
      )}
    </div>
  );
}
