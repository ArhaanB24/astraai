"use client";

import { useState, useEffect, useRef } from "react";
import { Plus, X, Search, Check, Building2, Tag, TrendingUp, Sparkles, Loader2 } from "lucide-react";
import { addTransactionApi, searchMutualFundsApi, fetchMutualFundsCatalogApi } from "@/lib/api";
import { notifyDataMutation } from "@/lib/dataSync";

interface FundItem {
  scheme_code: string;
  scheme_name: string;
  fund_house?: string;
  category?: string;
  plan_type?: string;
  nav?: number;
}

export function AddTransactionModal({ onTransactionAdded }: { onTransactionAdded: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<FundItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<FundItem | null>(null);
  
  const [txType, setTxType] = useState("SIP");
  const [amount, setAmount] = useState("5000");
  const [nav, setNav] = useState("50.0");
  const [units, setUnits] = useState("100");
  const [txDate, setTxDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Search funds with debouncing and instant 1-char handling
  useEffect(() => {
    if (!query || query.trim().length === 0) {
      setResults([]);
      setIsDropdownOpen(false);
      return;
    }

    if (selectedScheme && selectedScheme.scheme_name === query) {
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await searchMutualFundsApi(query.trim());
        if (Array.isArray(data)) {
          setResults(data);
          setIsDropdownOpen(data.length > 0);
        } else {
          setResults([]);
        }
      } catch (e) {
        console.warn("Mutual fund search failed:", e);
      } finally {
        setIsSearching(false);
      }
    }, 150);

    return () => clearTimeout(timer);
  }, [query, selectedScheme]);

  const handleSelectFund = (fund: FundItem) => {
    setSelectedScheme(fund);
    setQuery(fund.scheme_name);
    setIsDropdownOpen(false);
    
    // Auto-populate latest NAV if available
    if (fund.nav && fund.nav > 0) {
      const fundNav = fund.nav.toString();
      setNav(fundNav);
      if (parseFloat(amount) > 0) {
        setUnits((parseFloat(amount) / fund.nav).toFixed(4));
      }
    }
  };

  const handleClearSelection = () => {
    setSelectedScheme(null);
    setQuery("");
    setResults([]);
    setIsDropdownOpen(false);
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  const handleAmountChange = (val: string) => {
    setAmount(val);
    const parsedAmount = parseFloat(val);
    const parsedNav = parseFloat(nav);
    if (parsedAmount > 0 && parsedNav > 0) {
      setUnits((parsedAmount / parsedNav).toFixed(4));
    }
  };

  const handleNavChange = (val: string) => {
    setNav(val);
    const parsedAmount = parseFloat(amount);
    const parsedNav = parseFloat(val);
    if (parsedAmount > 0 && parsedNav > 0) {
      setUnits((parsedAmount / parsedNav).toFixed(4));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedScheme) {
      setErrorMsg("Please select a valid mutual fund from the search dropdown.");
      return;
    }
    setErrorMsg(null);
    setLoading(true);

    try {
      const payload = {
        scheme_code: selectedScheme.scheme_code,
        scheme_name: selectedScheme.scheme_name,
        transaction_type: txType,
        transaction_date: txDate,
        units: parseFloat(units) || 0,
        nav: parseFloat(nav) || 0,
        amount: parseFloat(amount) || 0,
      };

      await addTransactionApi(payload);
      notifyDataMutation("portfolio");
      setLoading(false);
      setIsOpen(false);
      onTransactionAdded();
    } catch (err: any) {
      setLoading(false);
      setErrorMsg(err.message || "Failed to record transaction");
    }
  };

  return (
    <>
      <button
        onClick={() => {
          setIsOpen(true);
          setErrorMsg(null);
        }}
        className="flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-semibold text-sm px-4 py-2.5 rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.98]"
      >
        <Plus className="w-4 h-4" /> Add Transaction
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#0f172a] border border-slate-800 w-full max-w-lg rounded-2xl p-6 relative text-white shadow-2xl">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <h2 className="text-xl font-bold text-slate-100">Add Mutual Fund Transaction</h2>
            </div>
            <p className="text-xs text-slate-400 mb-5">Record a SIP instalment, lump-sum purchase, or redemption into your portfolio.</p>

            {errorMsg && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-center gap-2">
                <span>⚠️ {errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Mutual Fund Autocomplete Search */}
              <div className="relative" ref={dropdownRef}>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Search Mutual Fund Scheme <span className="text-emerald-400">*</span></span>
                  {selectedScheme && (
                    <span className="text-[11px] text-emerald-400 font-normal flex items-center gap-1">
                      <Check className="w-3 h-3" /> Selected
                    </span>
                  )}
                </label>

                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      if (selectedScheme && selectedScheme.scheme_name !== e.target.value) {
                        setSelectedScheme(null);
                      }
                    }}
                    onFocus={() => {
                      if (results.length > 0 && !selectedScheme) {
                        setIsDropdownOpen(true);
                      }
                    }}
                    placeholder="Type fund name or AMC (e.g. Parag Parikh, HDFC, Axis)..."
                    className="w-full bg-slate-900/90 border border-slate-700 focus:border-emerald-500 rounded-xl pl-10 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-emerald-500/20"
                    required
                    autoComplete="off"
                  />
                  {isSearching ? (
                    <Loader2 className="w-4 h-4 absolute right-3.5 top-3 text-emerald-400 animate-spin" />
                  ) : query.length > 0 ? (
                    <button
                      type="button"
                      onClick={handleClearSelection}
                      className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  ) : null}
                </div>

                {/* Instant Autocomplete Dropdown */}
                {isDropdownOpen && results.length > 0 && !selectedScheme && (
                  <div className="absolute top-full left-0 right-0 z-50 mt-1.5 bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl max-h-60 overflow-y-auto divide-y divide-slate-800">
                    {results.map((r) => (
                      <div
                        key={r.scheme_code}
                        onClick={() => handleSelectFund(r)}
                        className="p-3 hover:bg-emerald-500/10 hover:border-l-2 hover:border-l-emerald-500 cursor-pointer transition-all flex flex-col gap-1 text-left"
                      >
                        <div className="text-xs font-semibold text-slate-100 line-clamp-1">
                          {r.scheme_name}
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {r.fund_house && (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">
                              <Building2 className="w-2.5 h-2.5 text-emerald-400" />
                              {r.fund_house}
                            </span>
                          )}
                          {r.category && (
                            <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-md border border-emerald-500/20">
                              <Tag className="w-2.5 h-2.5" />
                              {r.category}
                            </span>
                          )}
                          {r.nav && (
                            <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 ml-auto font-mono">
                              NAV: ₹{r.nav.toFixed(2)}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Transaction Type Selector */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Transaction Type</label>
                <div className="grid grid-cols-4 gap-2">
                  {["SIP", "BUY", "SELL", "DIVIDEND"].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTxType(t)}
                      className={`py-2 rounded-xl text-xs font-semibold transition-all border ${
                        txType === t
                          ? "bg-emerald-500 text-white border-emerald-400 shadow-md shadow-emerald-500/20"
                          : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Amount & NAV */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Amount (₹)</label>
                  <input
                    type="number"
                    min="1"
                    step="any"
                    value={amount}
                    onChange={(e) => handleAmountChange(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-xl px-3 py-2 text-sm text-slate-100 outline-none transition-all font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">NAV (₹)</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    value={nav}
                    onChange={(e) => handleNavChange(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-xl px-3 py-2 text-sm text-slate-100 outline-none transition-all font-mono"
                    required
                  />
                </div>
              </div>

              {/* Units & Date */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Calculated Units</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={units}
                    onChange={(e) => setUnits(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-xl px-3 py-2 text-sm text-slate-100 outline-none transition-all font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Transaction Date</label>
                  <input
                    type="date"
                    value={txDate}
                    onChange={(e) => setTxDate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-xl px-3 py-2 text-sm text-slate-100 outline-none transition-all"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !selectedScheme}
                className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.99] flex items-center justify-center gap-2 mt-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Saving Transaction...
                  </>
                ) : (
                  "Save Transaction to Portfolio"
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
