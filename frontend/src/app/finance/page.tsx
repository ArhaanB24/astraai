"use client";

import { useState, useEffect } from "react";
import { fetchFinanceHealth } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  Wallet,
  ShieldCheck,
  TrendingUp,
  PiggyBank,
  CreditCard,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  UserCheck,
} from "lucide-react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function PersonalFinanceOverviewPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [health, setHealth] = useState<any>(null);
  const [loadingData, setLoadingData] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchFinanceHealth();
      setHealth(data);
    } catch (e) {
      console.warn("Failed to fetch finance health", e);
    } finally {
      setLoadingData(false);
    }
  };

  useAutoRefresh(loadData, {
    intervalMs: 4000,
    enabled: isAuthenticated,
    eventScopes: ["finance", "portfolio", "all"],
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

  if (loadingData && !health) {
    return <div className="p-6 text-emerald-400 font-semibold text-xs">Loading Personal Finance Engine...</div>;
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Welcome Banner */}
      <div className="p-6 rounded-2xl bg-card border border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Personal Finance AI Module
          </span>
          <h1 className="text-xl font-black text-white mt-1">Financial Health & Net Worth Overview</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time deterministic aggregation of income sources, essential expenses, liabilities, and liquid reserves.
          </p>
        </div>

        {health && (
          <div className="flex items-center gap-3 bg-surface px-4 py-3 rounded-xl border border-border shrink-0">
            <Activity className="w-5 h-5 text-emerald-400" />
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Financial Health Score</span>
              <span className="text-lg font-black text-white">
                {health.health_score} / 100 ({health.health_status})
              </span>
            </div>
          </div>
        )}
      </div>

      {health ? (
        <>
          {/* Key KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-card border border-border">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>Monthly Surplus</span>
                <ArrowUpRight className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-black text-emerald-400 mt-2">{formatINR(health.monthly_surplus)}</p>
              <span className="text-[11px] text-slate-400 mt-1 block">Inflow: {formatINR(health.monthly_income)}</span>
            </div>

            <div className="p-5 rounded-2xl bg-card border border-border">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>Savings Rate %</span>
                <PiggyBank className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-black text-blue-400 mt-2">{health.savings_rate_pct}%</p>
              <span className="text-[11px] text-slate-400 mt-1 block">Includes monthly investments</span>
            </div>

            <div className="p-5 rounded-2xl bg-card border border-border">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>Debt-To-Income (DTI)</span>
                <CreditCard className="w-4 h-4 text-amber-400" />
              </div>
              <p className="text-2xl font-black text-amber-400 mt-2">{health.debt_to_income_pct}%</p>
              <span className="text-[11px] text-slate-400 mt-1 block">EMIs: {formatINR(health.monthly_emis)}/mo</span>
            </div>

            <div className="p-5 rounded-2xl bg-card border border-border">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
                <span>Net Worth</span>
                <ShieldCheck className="w-4 h-4 text-purple-400" />
              </div>
              <p className="text-2xl font-black text-white mt-2">{formatINR(health.net_worth)}</p>
              <span className="text-[11px] text-slate-400 mt-1 block">Assets - Liabilities</span>
            </div>
          </div>

          {/* Breakdown Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Assets vs Liabilities */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
              <h3 className="text-sm font-bold text-white border-b border-border/80 pb-2">
                Balance Sheet Assets vs Liabilities
              </h3>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Total Assets</span>
                  <p className="text-lg font-bold text-emerald-400 mt-1">{formatINR(health.total_assets)}</p>
                </div>
                <div className="p-4 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Total Liabilities</span>
                  <p className="text-lg font-bold text-rose-400 mt-1">{formatINR(health.total_liabilities)}</p>
                </div>
              </div>
            </div>

            {/* Emergency Fund Coverage */}
            <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
              <h3 className="text-sm font-bold text-white border-b border-border/80 pb-2">
                Emergency Reserve Adequacy
              </h3>
              <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Liquid Emergency Buffer</span>
                  <p className="text-xl font-bold text-white mt-0.5">{formatINR(health.emergency_fund_balance)}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Coverage Buffer</span>
                  <p className="text-xl font-bold text-emerald-400 mt-0.5">
                    {health.emergency_coverage_months} Months
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="p-8 text-center bg-card rounded-2xl border border-border text-slate-400 space-y-3">
          <UserCheck className="w-8 h-8 mx-auto text-emerald-400" />
          <h3 className="text-sm font-bold text-white">No Financial Profile Configured Yet</h3>
          <p className="text-xs max-w-md mx-auto">
            Complete the interactive financial onboarding questionnaire to synthesize your personalized health score, net worth, and savings rate.
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
