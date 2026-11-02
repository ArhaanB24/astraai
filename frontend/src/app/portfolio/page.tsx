"use client";

import { useState, useEffect } from "react";
import { fetchPortfolioSummary } from "@/lib/api";
import { PortfolioSummary } from "@/types";
import { formatINR } from "@/lib/utils";
import { PortfolioStats } from "@/components/PortfolioStats";
import { AddTransactionModal } from "@/components/AddTransactionModal";
import { PieChart, TrendingUp } from "lucide-react";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function PortfolioPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loadingData, setLoadingData] = useState(true);

  const loadData = async () => {
    try {
      const data = await fetchPortfolioSummary();
      setSummary(data);
    } catch (e) {
      console.warn("Failed to load portfolio", e);
    } finally {
      setLoadingData(false);
    }
  };

  useAutoRefresh(loadData, {
    intervalMs: 4000,
    enabled: isAuthenticated,
    eventScopes: ["portfolio", "all"],
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
    return <div className="p-6 text-emerald-400 font-semibold text-xs">Loading Portfolio Data...</div>;
  }

  const hasInvestments = Boolean(summary && summary.fund_breakdown && summary.fund_breakdown.length > 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between bg-card p-6 rounded-2xl border border-border">
        <div>
          <h1 className="text-xl font-black text-white flex items-center gap-2">
            <PieChart className="w-5 h-5 text-emerald-400" /> Portfolio Tracker
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Transaction-level portfolio tracking with dynamic XIRR and Latest Available AMFI NAVs (18 Aug 2026).
          </p>
        </div>
        <AddTransactionModal onTransactionAdded={loadData} />
      </div>

      {summary && <PortfolioStats summary={summary} />}

      {/* Fund Breakdown Table */}
      <div className="p-5 rounded-2xl bg-card border border-border">
        <h3 className="text-sm font-bold text-white mb-4">Mutual Fund Breakdown</h3>
        {hasInvestments && summary ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-surface text-slate-400 uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="py-3 px-4">Fund</th>
                  <th className="py-3 px-4">Units</th>
                  <th className="py-3 px-4">Latest NAV</th>
                  <th className="py-3 px-4">Invested</th>
                  <th className="py-3 px-4">Current</th>
                  <th className="py-3 px-4">Profit / Loss</th>
                  <th className="py-3 px-4">Return (%)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {summary.fund_breakdown.map((fund, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      {fund.scheme_name}
                    </td>
                    <td className="py-3 px-4 font-mono">{fund.total_units.toFixed(4)}</td>
                    <td className="py-3 px-4 font-mono text-emerald-400">₹{fund.latest_nav.toFixed(4)}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{formatINR(fund.invested_amount)}</td>
                    <td className="py-3 px-4 font-mono font-bold text-white">{formatINR(fund.current_value)}</td>
                    <td
                      className={`py-3 px-4 font-mono font-bold ${
                        fund.profit_loss >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {formatINR(fund.profit_loss)}
                    </td>
                    <td
                      className={`py-3 px-4 font-mono font-bold ${
                        fund.profit_loss_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {fund.profit_loss_pct >= 0 ? "+" : ""}
                      {fund.profit_loss_pct.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center bg-surface/50 rounded-xl border border-dashed border-border text-slate-400 space-y-3">
            <PieChart className="w-8 h-8 mx-auto text-slate-500" />
            <p className="text-xs">No mutual fund transactions recorded yet for this account.</p>
            <AddTransactionModal onTransactionAdded={loadData} />
          </div>
        )}
      </div>
    </div>
  );
}
