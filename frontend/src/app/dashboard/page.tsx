"use client";

import { useState, useEffect } from "react";
import { fetchPortfolioSummary, fetchPortfolioOverlap } from "@/lib/api";
import { PortfolioSummary, OverlapAnalysis } from "@/types";
import { formatINR } from "@/lib/utils";
import { PortfolioStats } from "@/components/PortfolioStats";
import { PortfolioCharts } from "@/components/PortfolioCharts";
import { AddTransactionModal } from "@/components/AddTransactionModal";
import { AIChatDrawer } from "@/components/AIChatDrawer";
import { Bot, Sparkles, AlertTriangle, ArrowRight, TrendingUp, ShieldCheck, PieChart } from "lucide-react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading } = useRequireAuth();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [overlap, setOverlap] = useState<OverlapAnalysis | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [loadingData, setLoadingData] = useState(true);

  const loadData = async () => {
    try {
      const sum = await fetchPortfolioSummary();
      setSummary(sum);
      try {
        const ov = await fetchPortfolioOverlap();
        setOverlap(ov);
      } catch {
        setOverlap(null);
      }
    } catch (err) {
      console.warn("Failed to load portfolio data", err);
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
        Authenticating ArthaAI Session...
      </div>
    );
  }

  if (loadingData && !summary) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-emerald-400 font-semibold text-xs">
        Loading ArthaAI Portfolio Engine...
      </div>
    );
  }

  const topStock = overlap?.overlapping_stocks?.[0];
  const firstName = user?.full_name ? user.full_name.split(" ")[0] : "Investor";
  const hasInvestments = Boolean(summary && summary.fund_breakdown && summary.fund_breakdown.length > 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card p-6 rounded-2xl border border-border">
        <div>
          <h1 className="text-xl font-black text-white tracking-tight">
            Good evening, {firstName}
          </h1>
          <p className="text-xs text-slate-400 mt-1">Here's your mutual fund portfolio at a glance.</p>
        </div>

        <div className="flex items-center gap-3">
          <AddTransactionModal onTransactionAdded={loadData} />
          <button
            onClick={() => setIsChatOpen(true)}
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs px-4 py-2.5 rounded-xl shadow-lg transition-all"
          >
            <Bot className="w-4 h-4" /> Ask ArthaAI
          </button>
        </div>
      </div>

      {summary && <PortfolioStats summary={summary} />}

      {/* Prominent ArthaAI Analysis Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-950/40 via-card to-slate-900 border border-emerald-800/40 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">ArthaAI Intelligence Analysis</h3>
              <p className="text-[11px] text-slate-400">Deterministic portfolio synthesis & factsheet citation audit</p>
            </div>
          </div>
          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded-lg border border-emerald-800/50 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Audit Verified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-3.5 rounded-xl bg-surface/80 border border-border space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">XIRR & Performance</span>
            <p className="text-xs text-slate-200 leading-relaxed">
              {summary ? (
                <>
                  Overall portfolio XIRR is{" "}
                  <span className="font-bold text-emerald-400">
                    {summary.xirr !== null ? `${summary.xirr.toFixed(2)}%` : "N/A"}
                  </span>
                  . Net return is{" "}
                  <span className="font-bold text-slate-100">{formatINR(summary.total_profit_loss || 0)}</span> (
                  {(summary.profit_loss_percentage || 0).toFixed(2)}%).
                </>
              ) : (
                "Add your first mutual fund transaction to generate performance metrics."
              )}
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-surface/80 border border-border space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Concentration Alert</span>
            <p className="text-xs text-slate-200 leading-relaxed">
              {topStock ? (
                <>
                  Stock <span className="font-bold text-amber-300">{topStock.company_name}</span> is held by multiple
                  schemes in your portfolio.
                </>
              ) : (
                "Sector exposure and stock diversification are evaluated deterministically across AMFI disclosures."
              )}
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-surface/80 border border-border space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Factsheet Insight</span>
            <p className="text-xs text-slate-200 leading-relaxed">
              ArthaAI matches all portfolio valuations with official AMFI NAV disclosures and multi-agent RAG.
            </p>
          </div>
        </div>
      </div>

      {/* Portfolio Charts */}
      {summary && hasInvestments && <PortfolioCharts summary={summary} overlap={overlap || undefined} />}

      {/* Clickable Overlap Concentration Alert Card */}
      {topStock && (
        <Link
          href="/portfolio/overlap"
          className="p-5 rounded-2xl bg-amber-950/20 border border-amber-800/40 flex items-start gap-4 hover:border-amber-500/50 transition-all group block cursor-pointer"
        >
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1 text-xs">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-sm text-amber-300 group-hover:underline">Portfolio Concentration Alert</h4>
              <span className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                View Overlap Matrix <ArrowRight className="w-3 h-3" />
              </span>
            </div>
            <p className="text-slate-300 mt-1 leading-relaxed">
              <span className="font-bold text-amber-200">{topStock.company_name}</span> appears across multiple funds in
              your portfolio (
              {topStock.held_by_funds.map((f) => f.scheme_name.split("-")[0].trim()).join(", ")}). Click to view full
              overlap analysis.
            </p>
          </div>
        </Link>
      )}

      {/* Fund Performance Table or Empty State */}
      <div className="p-5 rounded-2xl bg-card border border-border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white">Fund Performance & Allocation</h3>
          <Link
            href="/portfolio"
            className="text-xs font-semibold text-emerald-400 hover:underline flex items-center gap-1"
          >
            View All Transactions <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {hasInvestments && summary ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-surface text-slate-400 uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="py-3 px-4">Fund</th>
                  <th className="py-3 px-4">Invested</th>
                  <th className="py-3 px-4">Current Value</th>
                  <th className="py-3 px-4">P/L</th>
                  <th className="py-3 px-4">Allocation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {summary.fund_breakdown.map((fund, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      {fund.scheme_name}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">{formatINR(fund.invested_amount)}</td>
                    <td className="py-3 px-4 font-mono font-bold text-white">{formatINR(fund.current_value)}</td>
                    <td
                      className={`py-3 px-4 font-mono font-bold ${
                        fund.profit_loss >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {formatINR(fund.profit_loss)} ({fund.profit_loss_pct}%)
                    </td>
                    <td className="py-3 px-4 font-bold text-blue-400">{fund.allocation_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center bg-surface/50 rounded-xl border border-dashed border-border text-slate-400 space-y-3">
            <PieChart className="w-8 h-8 mx-auto text-slate-500" />
            <p className="text-xs">No mutual fund investments logged yet for this account.</p>
            <AddTransactionModal onTransactionAdded={loadData} />
          </div>
        )}
      </div>

      {/* AI CTA Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-card to-slate-900 border border-emerald-800/40 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Ask ArthaAI about your portfolio</h3>
          </div>
          <p className="text-xs text-slate-400">
            Get citation-backed answers grounded in official factsheet disclosures and deterministic math engines.
          </p>

          <div className="flex flex-wrap gap-2 pt-1">
            {["Why is my portfolio underperforming?", "Which funds overlap?", "What changed in my portfolio?"].map(
              (q, qIdx) => (
                <span
                  key={qIdx}
                  onClick={() => setIsChatOpen(true)}
                  className="text-[11px] text-slate-300 bg-surface border border-border px-3 py-1 rounded-lg cursor-pointer hover:border-emerald-500/50 transition-all"
                >
                  "{q}"
                </span>
              )
            )}
          </div>
        </div>

        <button
          onClick={() => setIsChatOpen(true)}
          className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs px-5 py-3 rounded-xl shadow-lg transition-all shrink-0 self-start md:self-auto"
        >
          Ask ArthaAI
        </button>
      </div>

      {/* AI Assistant Drawer */}
      <AIChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
}
