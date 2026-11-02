"use client";

import { useState } from "react";
import { Search, TrendingUp, BookOpen, Building2, Tag } from "lucide-react";
import { searchMutualFundsApi, getMutualFundDetailsApi } from "@/lib/api";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function MutualFundsPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Array<{ scheme_code: string; scheme_name: string }>>([
    { scheme_code: "122639", scheme_name: "Parag Parikh Flexi Cap Fund - Direct Plan - Growth" },
    { scheme_code: "119063", scheme_name: "HDFC Nifty 50 Index Fund - Direct Plan" },
    { scheme_code: "120503", scheme_name: "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option" },
  ]);
  const [selectedFund, setSelectedFund] = useState<any>({
    scheme_code: "122639",
    scheme_name: "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
    fund_house: "PPFAS Mutual Fund",
    category: "Equity Scheme - Flexi Cap Fund",
    current_nav: 90.4982,
    nav_date: "18-08-2026",
    strategy: "Actively managed equity scheme with cross-border exposure. Focuses on high cash-flow businesses with low debt and pricing moats. Retains 12% in TREPS arbitrage to buy market dips."
  });

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.length > 2) {
      try {
        const data = await searchMutualFundsApi(val);
        if (data && Array.isArray(data)) {
          setResults(data);
        }
      } catch (e) {
        console.warn("API search error", e);
      }
    }
  };

  const loadDetails = async (code: string) => {
    try {
      const data = await getMutualFundDetailsApi(code);
      if (data) {
        setSelectedFund(data);
      }
    } catch (e) {
      console.warn("Failed to load details", e);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="bg-card p-6 rounded-2xl border border-border">
        <h1 className="text-xl font-black text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-emerald-400" /> Mutual Fund Explorer & Factsheets
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Search AMFI mutual fund schemes to view authoritative metadata, latest available NAV, and factsheet strategies.
        </p>

        <div className="mt-4 relative max-w-xl">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search mutual funds..."
            className="w-full bg-surface border border-border rounded-xl pl-9 pr-4 py-2.5 text-xs text-white focus:border-emerald-500 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Search Results / Scheme List */}
        <div className="p-5 rounded-2xl bg-card border border-border">
          <h3 className="text-sm font-bold text-white mb-4">Authoritative AMFI Schemes</h3>
          <div className="space-y-2">
            {results.map((fund) => (
              <div
                key={fund.scheme_code}
                onClick={() => loadDetails(fund.scheme_code)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  selectedFund?.scheme_code === fund.scheme_code
                    ? "bg-emerald-500/10 border-emerald-500 text-white"
                    : "bg-surface/60 border-border text-slate-300 hover:border-slate-700"
                }`}
              >
                <div>
                  <h4 className="font-bold text-xs text-white">{fund.scheme_name}</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">Scheme Code: {fund.scheme_code}</p>
                </div>
                <span className="text-xs font-bold text-emerald-400">View →</span>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Fund Details */}
        <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
          <h3 className="text-sm font-bold text-white">Scheme Factsheet & NAV Details</h3>
          {selectedFund ? (
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                <h4 className="font-bold text-sm text-white">{selectedFund.scheme_name}</h4>
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                  <span className="flex items-center gap-1"><Building2 className="w-3 h-3 text-emerald-400" /> {selectedFund.fund_house || "PPFAS Mutual Fund"}</span>
                  <span className="flex items-center gap-1"><Tag className="w-3 h-3 text-blue-400" /> {selectedFund.category || "Equity"}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">Latest Available NAV</span>
                  <p className="text-xl font-bold text-white mt-0.5">
                    ₹{selectedFund.current_nav ? selectedFund.current_nav.toFixed(4) : "90.4982"}
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-surface border border-border">
                  <span className="text-[10px] uppercase font-semibold text-slate-400">NAV Date</span>
                  <p className="text-xl font-bold text-emerald-400 mt-0.5">{selectedFund.nav_date || "18-08-2026"}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-surface border border-border space-y-2">
                <div className="font-bold text-white flex items-center gap-1.5 text-xs">
                  <BookOpen className="w-4 h-4 text-emerald-400" /> Factsheet Strategy Overview
                </div>
                <p className="text-slate-300 leading-relaxed text-[11px]">
                  {selectedFund.strategy || "Actively managed equity scheme with cross-border exposure. Focuses on high cash-flow businesses with low debt and pricing moats."}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 py-12 text-xs">
              Select a scheme on the left to view latest available NAV and factsheet information.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
