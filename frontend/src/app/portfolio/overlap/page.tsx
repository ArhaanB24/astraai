"use client";

import { useState } from "react";
import { fetchPortfolioOverlap, fetchStockHoldingsApi, addStockHoldingApi, deleteStockHoldingApi } from "@/lib/api";
import { OverlapAnalysis } from "@/types";
import { OverlapMatrix } from "@/components/OverlapMatrix";
import { Layers, PieChart as PieIcon, Plus, Building, X } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartConfig } from "@/components/ui/chart";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { useAutoRefresh } from "@/lib/dataSync";

const sectorChartConfig: ChartConfig = {
  portfolio_weight_pct: {
    label: "Portfolio Weight",
    color: "#10b981",
  },
};

export default function OverlapPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [overlap, setOverlap] = useState<OverlapAnalysis | null>(null);
  const [directStocks, setDirectStocks] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Add Stock Modal State
  const [showAddStockModal, setShowAddStockModal] = useState(false);
  const [symbol, setSymbol] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [sector, setSector] = useState("Energy");
  const [quantity, setQuantity] = useState(10);
  const [buyPrice, setBuyPrice] = useState(400);
  const [savingStock, setSavingStock] = useState(false);

  const loadData = async () => {
    try {
      const [overlapData, stocksData] = await Promise.all([
        fetchPortfolioOverlap(),
        fetchStockHoldingsApi()
      ]);
      setOverlap(overlapData);
      setDirectStocks(stocksData || []);
    } catch (e) {
      console.warn("Overlap error", e);
    } finally {
      setLoadingData(false);
    }
  };

  useAutoRefresh(loadData, {
    intervalMs: 5000,
    enabled: isAuthenticated && !showAddStockModal,
    eventScopes: ["portfolio", "all"],
    refreshOnFocus: true,
    fetchOnMount: true,
  });

  const handleAddStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !companyName || buyPrice <= 0 || quantity <= 0) return;
    setSavingStock(true);
    try {
      await addStockHoldingApi({
        symbol: symbol.toUpperCase().trim(),
        company_name: companyName.trim(),
        sector: sector.trim() || "General",
        quantity: quantity,
        buy_price: buyPrice,
        current_price: buyPrice
      });
      setShowAddStockModal(false);
      setSymbol("");
      setCompanyName("");
      setQuantity(10);
      setBuyPrice(400);
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to add stock holding");
    } finally {
      setSavingStock(false);
    }
  };

  const handleDeleteStock = async (stockId: string) => {
    if (!confirm("Are you sure you want to remove this stock from your portfolio?")) return;
    try {
      await deleteStockHoldingApi(stockId);
      await loadData();
    } catch (err: any) {
      alert("Failed to delete stock holding");
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  if (loadingData && !overlap && directStocks.length === 0) {
    return <div className="p-6 text-emerald-400 font-semibold text-xs">Loading Portfolio Overlap Analysis...</div>;
  }

  const sectorData = overlap?.sector_concentration || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="bg-card p-6 rounded-2xl border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
            Portfolio Analytics
          </span>
          <h1 className="text-xl font-black text-white flex items-center gap-2 mt-1">
            <Layers className="w-5 h-5 text-emerald-400" /> Portfolio Overlap &amp; Stock Concentration
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Identifies common stock holdings across your mutual fund schemes and allows tracking direct stock portfolios.
          </p>
        </div>

        <button
          onClick={() => setShowAddStockModal(true)}
          className="bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 shrink-0"
        >
          <Plus className="w-4 h-4" /> Add Direct Stock
        </button>
      </div>

      {/* Overlap Matrix & Stock List */}
      <OverlapMatrix
        overlap={overlap}
        directStocks={directStocks}
        onDeleteStock={handleDeleteStock}
      />

      {/* Sector Exposure Chart (Shadcn Card + Chart) */}
      {sectorData.length > 0 && (
        <Card className="border-border shadow-lg shadow-black/20 space-y-6">
          <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-0">
            <div>
              <div className="flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-emerald-400" />
                <CardTitle className="text-base font-bold text-white tracking-tight">Sector Exposure (%)</CardTitle>
              </div>
              <CardDescription className="text-xs text-slate-400 mt-1">
                Deterministic aggregation of underlying stock holdings and weighted sector concentrations
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <Badge variant="emerald" className="text-[10px] py-1 px-2.5">
                Top Sector: {sectorData[0]?.sector} ({sectorData[0]?.portfolio_weight_pct}%)
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="h-64 w-full">
              <ChartContainer config={sectorChartConfig} className="h-full w-full aspect-auto">
                <BarChart data={sectorData} margin={{ top: 10, right: 10, left: -15, bottom: 25 }}>
                  <defs>
                    <linearGradient id="sectorBarGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="100%" stopColor="#0d9488" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis
                    dataKey="sector"
                    stroke="#64748b"
                    tick={{ fontSize: 11, fill: "#cbd5e1" }}
                    interval={0}
                    tickLine={false}
                    axisLine={{ stroke: "#334155" }}
                  />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11, fill: "#94a3b8" }}
                    tickFormatter={(val) => `${val}%`}
                    tickLine={false}
                    axisLine={{ stroke: "#334155" }}
                  />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        indicator="dot"
                        formatter={(val: any) => (
                          <div className="flex items-center justify-between gap-3 w-full">
                            <span className="text-slate-400">Portfolio Weight:</span>
                            <span className="font-mono font-bold text-emerald-400">{val}%</span>
                          </div>
                        )}
                      />
                    }
                  />
                  <Bar dataKey="portfolio_weight_pct" fill="url(#sectorBarGrad)" radius={[6, 6, 0, 0]} maxBarSize={48} />
                </BarChart>
              </ChartContainer>
            </div>

            {/* Sector Allocation Breakdown Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 pt-4 border-t border-border/60">
              {sectorData.map((s, idx) => (
                <div key={idx} className="bg-surface/80 p-2.5 rounded-xl border border-border/80 text-center space-y-1">
                  <span className="text-[10px] font-semibold text-slate-400 truncate block">{s.sector}</span>
                  <span className="text-xs font-black text-emerald-400 font-mono">{s.portfolio_weight_pct}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Direct Stock Modal */}
      {showAddStockModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Building className="w-4 h-4 text-emerald-400" /> Add Stock Holding to Portfolio
              </h2>
              <button onClick={() => setShowAddStockModal(false)} className="text-slate-400 hover:text-white p-1">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddStock} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Stock Symbol</label>
                  <input
                    type="text"
                    placeholder="e.g. TATAPOWER"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    required
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Sector</label>
                  <input
                    type="text"
                    placeholder="e.g. Energy, IT, Bank"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Company Name</label>
                <input
                  type="text"
                  placeholder="e.g. Tata Power Co. Ltd."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Quantity (Shares)</label>
                  <input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    required
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 uppercase">Buy Price (₹/share)</label>
                  <input
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={buyPrice}
                    onChange={(e) => setBuyPrice(Number(e.target.value))}
                    required
                    className="w-full bg-surface border border-border rounded-xl px-3 py-2 text-xs text-white mt-1 outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="p-3 rounded-xl bg-surface border border-border text-[11px] text-slate-400">
                Total Invested Value: <strong className="text-white">₹{(quantity * buyPrice).toLocaleString("en-IN")}</strong>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border mt-4">
                <button
                  type="button"
                  onClick={() => setShowAddStockModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-slate-400 hover:text-white font-semibold text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingStock}
                  className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20"
                >
                  {savingStock ? "Saving to DB..." : "Save to Portfolio"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
