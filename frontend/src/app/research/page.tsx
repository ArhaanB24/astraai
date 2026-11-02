"use client";

import { useState, useRef } from "react";
import {
  Newspaper,
  Search,
  ExternalLink,
  AlertCircle,
  Globe,
  Loader2,
  ShieldCheck,
  Radio,
} from "lucide-react";
import { sendSearchResearch, SearchResearchResult } from "@/lib/api";
import { FormattedMarkdown } from "@/components/FormattedMarkdown";
import { useRequireAuth } from "@/lib/useRequireAuth";

const QUICK_SEARCHES = [
  "Latest mutual fund news India",
  "Indian stock market news today",
  "Income tax updates India 2025",
  "RBI monetary policy update",
  "Personal finance tips India",
  "SEBI regulatory news",
];

function extractDomain(url: string): string {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return "Source";
  }
}

export default function ResearchPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResearchResult | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const handleSearch = async (queryText?: string) => {
    const q = (queryText ?? query).trim();
    if (!q || loading) return;
    if (!queryText) setQuery(q);

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await sendSearchResearch(q);
      setResult(res);
      setTimeout(
        () => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        100
      );
    } catch (e: any) {
      setError(e?.message ?? "Failed to fetch research results. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="bg-card p-4 rounded-2xl border border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
            <Newspaper className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white">News &amp; Research</h1>
              <span className="text-[10px] font-bold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                Live Internet Search
              </span>
            </div>
            <p className="text-[10px] text-amber-400 flex items-center gap-1 mt-0.5">
              <ShieldCheck className="w-3 h-3" />
              Google News RSS + DuckDuckGo &middot; Real-time financial intelligence
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded-xl">
          <Radio className="w-3 h-3 animate-pulse" />
          Live
        </div>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        className="flex items-center gap-2"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Indian financial news, market updates, tax changes..."
            className="w-full bg-card border border-border rounded-xl pl-10 pr-4 py-3 text-xs text-white focus:border-amber-500 outline-none transition-colors placeholder:text-slate-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 px-5 py-3 rounded-xl text-xs font-bold transition-all shrink-0"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {/* Quick-search chips */}
      <div className="flex flex-wrap gap-2">
        {QUICK_SEARCHES.map((q) => (
          <button
            key={q}
            onClick={() => {
              setQuery(q);
              handleSearch(q);
            }}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-card border border-border text-slate-400 hover:text-amber-300 hover:border-amber-500/40 text-[11px] font-medium transition-all disabled:opacity-50 whitespace-nowrap"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Searching live sources...</p>
            <p className="text-xs text-slate-400 mt-1">Fetching from Google News RSS and DuckDuckGo</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="flex items-start gap-3 p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-rose-300">Search Failed</p>
            <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div ref={resultsRef} className="space-y-4">
          {/* AI Research Summary */}
          {result.answer && (
            <div className="bg-card border border-border rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <div className="w-6 h-6 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                  <Newspaper className="w-3.5 h-3.5 text-amber-400" />
                </div>
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                  Research Summary
                </span>
                <span className="ml-auto text-[10px] text-slate-500 truncate max-w-[200px]">
                  {result.query}
                </span>
              </div>
              <div className="text-xs text-slate-200 leading-relaxed border-t border-border pt-3">
                <FormattedMarkdown content={result.answer} />
              </div>
            </div>
          )}

          {/* Evidence Sources */}
          {result.evidence_sources && result.evidence_sources.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 px-1">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Live Sources — {result.evidence_sources.length} articles retrieved
                </span>
              </div>

              <div className="grid gap-2.5">
                {result.evidence_sources.map((src, idx) => {
                  const domain = extractDomain(src.url);
                  const hasUrl = Boolean(src.url && src.url.startsWith("http"));

                  if (hasUrl) {
                    return (
                      <a
                        key={idx}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group block bg-card border border-border rounded-xl p-4 hover:border-amber-500/40 hover:bg-amber-500/5 transition-all cursor-pointer"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-white group-hover:text-amber-300 transition-colors leading-snug line-clamp-2">
                              {src.title}
                            </p>
                            {src.snippet && (
                              <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                                {src.snippet}
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-2">
                              <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-400/80 bg-amber-950/40 border border-amber-800/30 px-2 py-0.5 rounded-full">
                                <Globe className="w-2.5 h-2.5" />
                                {domain}
                              </span>
                              <span className="text-[10px] text-slate-500">{src.source}</span>
                            </div>
                          </div>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400 transition-colors shrink-0 mt-0.5" />
                        </div>
                      </a>
                    );
                  }

                  return (
                    <div
                      key={idx}
                      className="bg-card border border-border rounded-xl p-4"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-white leading-snug line-clamp-2">
                          {src.title}
                        </p>
                        {src.snippet && (
                          <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                            {src.snippet}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-400/80 bg-amber-950/40 border border-amber-800/30 px-2 py-0.5 rounded-full">
                            <Globe className="w-2.5 h-2.5" />
                            {domain}
                          </span>
                          <span className="text-[10px] text-slate-500">{src.source}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* No sources fallback */}
          {result.evidence_sources?.length === 0 && (
            <div className="text-center py-10 text-slate-400 text-xs">
              <Globe className="w-8 h-8 mx-auto mb-2 opacity-30" />
              No news articles found for this query. Try a different search term.
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Newspaper className="w-7 h-7 text-amber-400" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Live Financial Research</p>
            <p className="text-xs text-slate-400 mt-1 max-w-xs">
              Search any stock, mutual fund, market event, tax news, or RBI update.
              Results are fetched live from Google News and DuckDuckGo.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 max-w-md">
            {QUICK_SEARCHES.slice(0, 3).map((q) => (
              <button
                key={q}
                onClick={() => {
                  setQuery(q);
                  handleSearch(q);
                }}
                className="px-3 py-1.5 rounded-xl bg-card border border-border text-slate-400 hover:text-amber-300 hover:border-amber-500/40 text-[11px] font-medium transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
