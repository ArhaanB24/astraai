"use client";

import { useState, useRef, useEffect } from "react";
import { Bot, Send, ShieldCheck, BookOpen, CheckCircle2, Wallet, AlertCircle } from "lucide-react";
import { sendFinanceChat } from "@/lib/api";
import { Citation } from "@/types";
import { FormattedMarkdown } from "@/components/FormattedMarkdown";
import { useRequireAuth } from "@/lib/useRequireAuth";

export default function PersonalFinanceChatPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Array<{ sender: string; text: string; citations?: Citation[]; tools?: string[]; error?: boolean }>>([
    {
      sender: "assistant",
      text: "Welcome to **ArthaAI Personal Finance Assistant**!\n\nI analyze your monthly financial health, calculate exact required SIP contributions for active financial goals, evaluate car purchase affordability, and simulate non-destructive What-If scenarios.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;
    if (!queryText) setInput("");

    setMessages((prev) => [...prev, { sender: "user", text: textToSend }]);
    setLoading(true);

    try {
      const res = await sendFinanceChat(textToSend);
      setLoading(false);

      if (res && res.answer) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: res.answer,
            citations: res.citations,
            tools: res.tools_used,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            text: "Unable to reach Personal Finance AI. Please check the backend connection.",
            error: true,
          },
        ]);
      }
    } catch (e) {
      setLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: "Unable to reach Personal Finance AI. Please check the backend connection.",
          error: true,
        },
      ]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-4 h-[85vh] flex flex-col">
      {/* Header */}
      <div className="bg-card p-4 rounded-2xl border border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
            <Wallet className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white">Personal Finance AI Assistant</h1>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                Personal Finance Agent
              </span>
            </div>
            <p className="text-[10px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <ShieldCheck className="w-3 h-3" /> Deterministic Cash Flow & Goal Grounded • Zero Hallucination Math
            </p>
          </div>
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 bg-card border border-border rounded-2xl p-4 overflow-y-auto space-y-4 text-xs">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`p-4 rounded-2xl max-w-[85%] leading-relaxed ${
                m.sender === "user"
                  ? "bg-emerald-500 text-slate-950 font-semibold rounded-br-none whitespace-pre-line"
                  : m.error
                  ? "bg-rose-950/40 border border-rose-800/60 text-rose-200 rounded-bl-none whitespace-pre-line"
                  : "bg-surface border border-border text-slate-200 rounded-bl-none"
              }`}
            >
              {m.error && (
                <div className="flex items-center gap-1.5 font-bold text-rose-400 mb-1">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Connection Error</span>
                </div>
              )}
              {m.sender === "user" ? m.text : <FormattedMarkdown content={m.text} />}
            </div>

            {/* Analysis Trace */}
            {m.tools && m.tools.length > 0 && (
              <div className="mt-2 p-3 rounded-xl bg-surface/80 border border-border max-w-[85%] space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Analysis Trace
                </span>
                {m.tools.map((t, tIdx) => (
                  <div key={tIdx} className="flex items-center gap-1.5 text-[11px] text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>
                      {t === "calculate_financial_health" && "Evaluated income, expenses, DTI %, and net monthly surplus"}
                      {t === "simulate_what_if_scenario" && "Executed non-destructive What-If scenario simulation engine"}
                      {t === "calculate_goal_required_sip" && "Computed exact required monthly SIP contribution for goal"}
                      {t === "calculate_purchase_affordability" && "Evaluated loan EMI, post-purchase surplus & risk flags"}
                      {t === "search_financial_rules" && "Retrieved official 50/30/20 & 20/4/10 rule of thumb guidelines"}
                      {t !== "calculate_financial_health" &&
                        t !== "simulate_what_if_scenario" &&
                        t !== "calculate_goal_required_sip" &&
                        t !== "calculate_purchase_affordability" &&
                        t !== "search_financial_rules" &&
                        `Executed: ${t}`}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Citations */}
            {m.citations && m.citations.length > 0 && (
              <div className="mt-2 p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 max-w-[85%] text-[11px] text-emerald-200 space-y-1.5">
                <div className="font-bold flex items-center gap-1 text-emerald-400">
                  <BookOpen className="w-3.5 h-3.5" /> Cited Rule Guidelines:
                </div>
                {m.citations.map((c, cIdx) => (
                  <div key={cIdx} className="border-l-2 border-emerald-500 pl-2.5 py-0.5">
                    <p className="font-bold text-white">{c.document_name}</p>
                    <p className="text-slate-400 text-[10px]">
                      {c.source} • Section: {c.section}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-emerald-400 text-xs italic bg-surface border border-border p-3 rounded-xl">
            <Bot className="w-4 h-4 animate-spin text-emerald-400 shrink-0" />
            Evaluating personal financial profile & running scenario engines...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Clickable Starter Prompt Suggestions */}
      <div className="flex items-center gap-2 overflow-x-auto text-[11px] shrink-0 pb-1 scrollbar-none">
        {[
          "How financially healthy am I?",
          "What is my monthly surplus?",
          "What happens if my salary increases by 20%?",
          "How much should I invest monthly for my house down payment?",
          "How much emergency fund should I maintain?",
          "Can I afford a ₹15 lakh car?"
        ].map((q, qIdx) => (
          <button
            key={qIdx}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="px-3 py-1.5 rounded-xl bg-card border border-border text-slate-300 hover:text-white hover:border-emerald-500/50 whitespace-nowrap transition-all disabled:opacity-50"
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
          placeholder="Ask ArthaAI about your personal finances, goals, or what-if scenarios..."
          className="flex-1 bg-card border border-border rounded-xl px-4 py-3 text-xs text-white focus:border-emerald-500 outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 p-3 rounded-xl font-bold transition-all"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
