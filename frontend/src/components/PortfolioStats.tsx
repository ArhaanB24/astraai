"use client";

import { PortfolioSummary } from "@/types";
import { formatINR } from "@/lib/utils";
import { Wallet, TrendingUp, TrendingDown, Award } from "lucide-react";

export function PortfolioStats({ summary }: { summary: PortfolioSummary }) {
  const isPositive = summary.total_profit_loss >= 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Total Invested */}
      <div className="p-5 rounded-2xl bg-card border border-border flex items-start justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Invested</span>
          <h3 className="text-2xl font-bold text-white mt-1">{formatINR(summary.total_invested)}</h3>
          <p className="text-[11px] text-slate-500 mt-1">Across {summary.fund_breakdown.length} mutual fund schemes</p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
          <Wallet className="w-5 h-5" />
        </div>
      </div>

      {/* 2. Current Value */}
      <div className="p-5 rounded-2xl bg-card border border-border flex items-start justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Current Portfolio Value</span>
          <h3 className="text-2xl font-bold text-white mt-1">{formatINR(summary.current_value)}</h3>
          <p className="text-[11px] text-slate-500 mt-1">Valued at Latest Available NAV (18 Aug 2026)</p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
          <TrendingUp className="w-5 h-5" />
        </div>
      </div>

      {/* 3. Profit / Loss */}
      <div className="p-5 rounded-2xl bg-card border border-border flex items-start justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Profit / Loss</span>
          <h3 className={`text-2xl font-bold mt-1 ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
            {formatINR(summary.total_profit_loss)}
          </h3>
          <span className={`inline-block text-[11px] font-bold px-2 py-0.5 rounded mt-1 ${isPositive ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
            {isPositive ? "+" : ""}{summary.profit_loss_percentage.toFixed(2)}% Absolute Return
          </span>
        </div>
        <div className={`w-10 h-10 rounded-xl border flex items-center justify-center shrink-0 ${isPositive ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-rose-500/10 border-rose-500/20 text-rose-400"}`}>
          {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        </div>
      </div>

      {/* 4. Portfolio XIRR */}
      <div className="p-5 rounded-2xl bg-card border border-border flex items-start justify-between">
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Portfolio XIRR</span>
          <h3 className={`text-2xl font-bold mt-1 ${summary.xirr !== null && summary.xirr >= 0 ? "text-emerald-400" : "text-slate-200"}`}>
            {summary.xirr !== null ? `${summary.xirr.toFixed(2)}%` : "N/A"}
          </h3>
          <p className="text-[11px] text-slate-500 mt-1">Exact Money-Weighted Return</p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 text-emerald-400 flex items-center justify-center shrink-0">
          <Award className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
