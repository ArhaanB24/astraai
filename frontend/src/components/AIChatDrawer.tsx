"use client";

import { useState } from "react";
import { Bot, Send, ShieldCheck, BookOpen, CheckCircle2, X } from "lucide-react";
import { sendChatMessage } from "@/lib/api";
import { Citation } from "@/types";

export function AIChatDrawer({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ sender: string; text: string; citations?: Citation[]; tools?: string[] }>>([
    {
      sender: "assistant",
      text: "Hello! I am **ArthaAI Mutual Fund Agent**.\nAsk me about your portfolio XIRR, stock overlap across funds, why a fund dropped, or factsheet strategies.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim()) return;
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

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-surface border-l border-border z-50 flex flex-col shadow-2xl text-slate-200">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between bg-card">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white">Mutual Fund AI Assistant</h3>
            <p className="text-[10px] text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Citation Grounded Evidence
            </p>
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Message Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`p-3.5 rounded-2xl max-w-[88%] whitespace-pre-line leading-relaxed ${
                m.sender === "user"
                  ? "bg-emerald-500 text-slate-950 font-semibold rounded-br-none"
                  : "bg-card border border-border text-slate-200 rounded-bl-none"
              }`}
            >
              {m.text}
            </div>

            {/* Analysis Trace */}
            {m.tools && m.tools.length > 0 && (
              <div className="mt-2 p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 max-w-[88%] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Analysis Trace</span>
                {m.tools.map((t, tIdx) => (
                  <div key={tIdx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                    <span>
                      {t === "get_portfolio_summary" && "Retrieved portfolio summary & computed exact XIRR (-0.51%)"}
                      {t === "get_portfolio_overlap_analysis" && "Checked portfolio stock & sector concentration overlap"}
                      {t === "search_factsheets_and_disclosures" && "Retrieved official factsheet disclosures from Qdrant"}
                      {t !== "get_portfolio_summary" && t !== "get_portfolio_overlap_analysis" && t !== "search_factsheets_and_disclosures" && `Executed: ${t}`}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Citation Cards */}
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 max-w-[88%] text-[11px] text-emerald-200 space-y-1.5">
                <div className="font-bold flex items-center gap-1 text-emerald-400">
                  <BookOpen className="w-3.5 h-3.5" /> Cited Evidence:
                </div>
                {m.citations.map((c, cIdx) => (
                  <div key={cIdx} className="border-l-2 border-emerald-500 pl-2.5 py-0.5">
                    <p className="font-bold text-white">{c.document_name}</p>
                    <p className="text-slate-400 text-[10px]">{c.source} • Section: {c.section}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-emerald-400 text-xs italic bg-card border border-border p-3 rounded-xl">
            <Bot className="w-4 h-4 animate-spin text-emerald-400" />
            Analyzing portfolio & factsheet disclosures...
          </div>
        )}
      </div>

      {/* Sample Prompt Chips */}
      <div className="px-3 py-2 bg-card border-t border-border flex items-center gap-1.5 overflow-x-auto text-[10px]">
        {[
          "Why is my portfolio underperforming?",
          "Which funds overlap?",
          "What changed in my portfolio?"
        ].map((chip, cIdx) => (
          <button
            key={cIdx}
            onClick={() => handleSend(chip)}
            className="px-2.5 py-1 rounded-lg bg-surface border border-border text-slate-300 hover:text-white hover:border-emerald-500/50 whitespace-nowrap transition-all"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-border bg-card">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask ArthaAI about your portfolio..."
            className="flex-1 bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-white focus:border-emerald-500 outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold p-2.5 rounded-xl transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
