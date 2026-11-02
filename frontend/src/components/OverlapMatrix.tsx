"use client";

import { OverlapAnalysis } from "@/types";
import { AlertTriangle, Layers, Building, TrendingUp, TrendingDown, Trash2 } from "lucide-react";
import { formatINR } from "@/lib/utils";

interface OverlapMatrixProps {
  overlap?: OverlapAnalysis | null;
  directStocks?: any[];
  onDeleteStock?: (id: string) => void;
}

export function OverlapMatrix({ overlap, directStocks = [], onDeleteStock }: OverlapMatrixProps) {
  const overlappingStocks = overlap?.overlapping_stocks || [];
  const topSector = overlap?.sector_concentration?.[0];
  const topCommonStock = overlappingStocks[0];
  const hasFunds = overlappingStocks.length > 0;
  const hasStocks = directStocks && directStocks.length > 0;

  if (!hasFunds && !hasStocks) {
    return (
      <div className="p-8 rounded-2xl bg-card border border-border text-center text-slate-400 text-xs space-y-2">
        <p className="font-semibold text-slate-300">No mutual funds or direct stocks found in your portfolio.</p>
        <p className="text-slate-500">
          Add mutual fund transactions or use &ldquo;+ Add Direct Stock&rdquo; above to track stock exposure and detect portfolio overlap.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Overlap & Concentration Warning Card */}
      {(topCommonStock || topSector) && hasFunds && (
        <div className="p-5 rounded-2xl bg-amber-950/20 border border-amber-800/40 flex items-start gap-4">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1 text-xs">
            <h4 className="font-bold text-sm text-amber-300">Portfolio Concentration Warning</h4>
            <p className="text-slate-300 mt-1 leading-relaxed">
              {topCommonStock ? (
                <>
                  <span className="font-bold text-amber-200">{topCommonStock.company_name}</span> appears across multiple funds in your portfolio ({topCommonStock.held_by_funds.map(f => f.scheme_name.split('-')[0].trim()).join(', ')}).
                </>
              ) : (
                `Highest sector concentration is in ${topSector?.sector} at ${topSector?.portfolio_weight_pct}%.`
              )}
            </p>
          </div>
        </div>
      )}

      {/* Direct Stocks Table */}
      {hasStocks && (
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Direct Stock Holdings (Saved in DB)</h3>
            </div>
            <span className="text-[11px] text-slate-400">{directStocks.length} Stocks</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-surface text-slate-400 uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Sector</th>
                  <th className="py-3 px-4">Quantity</th>
                  <th className="py-3 px-4">Buy Price</th>
                  <th className="py-3 px-4">Current Value</th>
                  <th className="py-3 px-4">P&amp;L</th>
                  {onDeleteStock && <th className="py-3 px-4 text-right">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {directStocks.map((stock) => {
                  const isProfit = (stock.profit_loss || 0) >= 0;
                  return (
                    <tr key={stock.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-semibold text-white">
                        <div className="flex items-center gap-2">
                          <Building className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <div>
                            <p>{stock.company_name}</p>
                            <span className="text-[10px] text-slate-400">{stock.symbol}</span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{stock.sector}</td>
                      <td className="py-3 px-4 font-medium text-white">{stock.quantity}</td>
                      <td className="py-3 px-4 text-slate-300">{formatINR(stock.buy_price)}</td>
                      <td className="py-3 px-4 font-bold text-white">{formatINR(stock.current_value)}</td>
                      <td className={`py-3 px-4 font-bold ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
                        <div className="flex items-center gap-1">
                          {isProfit ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {formatINR(stock.profit_loss)} ({stock.profit_loss_pct}%)
                        </div>
                      </td>
                      {onDeleteStock && (
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => onDeleteStock(stock.id)}
                            className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                            title="Delete Stock"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Common Stocks Across Mutual Funds */}
      {hasFunds && (
        <div className="p-5 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">Common Stocks Across Mutual Fund Schemes</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-surface text-slate-400 uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Sector</th>
                  <th className="py-3 px-4">Effective Weight</th>
                  <th className="py-3 px-4">Held By Schemes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {overlappingStocks.map((stock, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                      <Building className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      {stock.company_name}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{stock.sector}</td>
                    <td className="py-3 px-4 font-bold text-emerald-400">
                      {stock.effective_portfolio_weight_pct}%
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {stock.held_by_funds.map((f, fIdx) => (
                          <span key={fIdx} className="bg-surface border border-border px-2 py-0.5 rounded text-[10px] text-slate-300">
                            {f.scheme_name.split("-")[0].trim()} ({f.fund_allocation_pct}%)
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
