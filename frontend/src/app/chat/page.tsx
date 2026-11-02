"use client";

import { useState } from "react";
import { Bot, Send, ShieldCheck, BookOpen, CheckCircle2 } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import { Citation } from "@/types";
import { FormattedMarkdown } from "@/components/FormattedMarkdown";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function ChatPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ sender: string; text: string; citations?: Citation[]; tools?: string[] }>>([
    {
      sender: "assistant",
      text: "Welcome to **ArthaAI Mutual Fund Agent**!\n\nI can analyze your portfolio XIRR, detect stock overlap across your funds, compute risk metrics (Sharpe ratio, Sortino, Max Drawdown), and answer questions using official factsheet citations.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;
    if (!queryText) setInput("");

    setMessages((prev) => [...prev, { sender: "user", text: textToSend }]);
    setLoading(true);

    const res = await sendChatMessage(textToSend);
    setLoading(false);

    setMessages((prev) => [
      ...prev,
      {
        sender: "assistant",
        text: res.answer,
        citations: res.citations,
        tools: res.tools_used,
      },
    ]);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 h-[85vh] flex flex-col">
      {/* Header */}
      <div className="bg-card p-4 rounded-2xl border border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">Mutual Fund AI Assistant</h1>
            <p className="text-[10px] text-blue-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Citation Grounded • Zero Hallucination Math
            </p>
          </div>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 bg-card border border-border rounded-2xl p-4 overflow-y-auto space-y-4 text-xs">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`p-4 rounded-2xl max-w-[82%] leading-relaxed ${
                m.sender === "user"
                  ? "bg-blue-500 text-slate-950 font-semibold rounded-br-none whitespace-pre-line"
                  : "bg-surface border border-border text-slate-200 rounded-bl-none"
              }`}
            >
              {m.sender === "user" ? m.text : <FormattedMarkdown content={m.text} />}
            </div>

            {/* Analysis Trace */}
            {m.tools && m.tools.length > 0 && (
              <div className="mt-2 p-3 rounded-xl bg-surface/80 border border-border max-w-[82%] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Analysis Trace</span>
                {m.tools.map((t, tIdx) => (
                  <div key={tIdx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>
                      {t === "get_portfolio_summary" && "Retrieved portfolio summary & computed exact XIRR"}
                      {t === "get_portfolio_overlap_analysis" && "Checked portfolio stock & sector concentration overlap"}
                      {t === "search_factsheets_and_disclosures" && "Retrieved official factsheet disclosures from Qdrant"}
                      {t !== "get_portfolio_summary" && t !== "get_portfolio_overlap_analysis" && t !== "search_factsheets_and_disclosures" && `Executed: ${t}`}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Citations */}
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 p-3 rounded-xl bg-blue-950/20 border border-blue-800/30 max-w-[82%] text-[11px] text-blue-200 space-y-1.5">
                <div className="font-bold flex items-center gap-1 text-blue-400">
                  <BookOpen className="w-3.5 h-3.5" /> Cited Evidence:
                </div>
                {m.citations.map((c, cIdx) => (
                  <div key={cIdx} className="border-l-2 border-blue-500 pl-2.5 py-0.5">
                    <p className="font-bold text-white">{c.document_name}</p>
                    <p className="text-slate-400 text-[10px]">{c.source} • Section: {c.section}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-blue-400 text-xs italic bg-surface border border-border p-3 rounded-xl">
            <Bot className="w-4 h-4 animate-spin text-blue-400" />
            Analyzing portfolio & factsheet disclosures...
          </div>
        )}
      </div>

      {/* Prompt Suggestions */}
      <div className="flex items-center gap-2 overflow-x-auto text-[11px] shrink-0">
        {[
          "Why is my portfolio underperforming?",
          "Which funds overlap?",
          "What changed in my portfolio?"
        ].map((q, qIdx) => (
          <button
            key={qIdx}
            onClick={() => handleSend(q)}
            className="px-3 py-1.5 rounded-xl bg-card border border-border text-slate-300 hover:text-white hover:border-blue-500/50 whitespace-nowrap transition-all"
          >
            "{q}"
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask ArthaAI about your portfolio..."
          className="flex-1 bg-card border border-border rounded-xl px-4 py-3 text-xs text-white focus:border-blue-500 outline-none"
        />
        <button type="submit" disabled={loading} className="bg-blue-500 hover:bg-blue-600 text-slate-950 p-3 rounded-xl font-bold transition-all">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
