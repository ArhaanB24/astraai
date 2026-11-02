"use client";

import { useState, useRef, useEffect } from "react";
import { sendTaxChat } from "@/lib/api";
import { ChatMessage, Citation } from "@/types";
import { FormattedMarkdown } from "@/components/FormattedMarkdown";
import {
  Send,
  Bot,
  User,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Layers,
  Info,
  Scale,
  RefreshCw
} from "lucide-react";

import { useRequireAuth } from "@/lib/useRequireAuth";

export default function TaxChatPage() {
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-tax",
      role: "assistant",
      content:
        "Hello! I am your dedicated **Tax AI Advisor**.\n\nI can help you evaluate your income tax liability, optimize between the **Old and New Tax Regimes (Section 115BAC)**, analyze **Section 80C and 80D** deduction benefits, and explain **Section 87A rebate and marginal relief**.\n\nAll tax figures are calculated using deterministic Python engines based on the **Income Tax Act, 1961**.\n\nHow can I help with your taxes today?",
      timestamp: "Just now",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] text-slate-400 font-semibold text-xs">
        Authenticating...
      </div>
    );
  }

  const starterQuestions = [
    "How much tax will I pay?",
    "Which tax regime is better for me?",
    "How does Section 80C save tax?",
    "Explain Section 87A rebate and marginal relief.",
    "How much can I save under the new regime?",
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const response = await sendTaxChat(query);

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        tools_used: response.tools_used,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto p-4 md:p-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border/80 mb-4 shrink-0">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-purple-500/10 text-purple-400 border border-purple-500/20 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Tax Agent AI
            </span>
            <span className="text-xs text-slate-500 font-medium">Income Tax Act, 1961 Grounded</span>
          </div>
          <h1 className="text-xl font-black text-white flex items-center gap-2">
            <Scale className="w-6 h-6 text-purple-400" /> Statutory Tax Advisory Assistant
          </h1>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.map((m) => {
          const isAssistant = m.role === "assistant";
          return (
            <div
              key={m.id}
              className={`flex gap-3.5 ${isAssistant ? "items-start" : "items-start flex-row-reverse"}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                  isAssistant
                    ? "bg-purple-600 text-white shadow-md shadow-purple-500/20"
                    : "bg-slate-800 text-slate-300 border border-slate-700"
                }`}
              >
                {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
              </div>

              {/* Message Bubble Container */}
              <div className={`space-y-3 max-w-[85%] ${isAssistant ? "items-start" : "items-end"}`}>
                {/* Bubble */}
                <div
                  className={`p-4 rounded-2xl text-xs leading-relaxed ${
                    isAssistant
                      ? "bg-card border border-border/80 text-slate-200 shadow-sm"
                      : "bg-purple-600 text-white font-medium"
                  }`}
                >
                  {isAssistant ? (
                    <FormattedMarkdown content={m.content} />
                  ) : (
                    <p className="whitespace-pre-wrap">{m.content}</p>
                  )}
                  <span
                    className={`block text-[10px] mt-2 font-mono ${
                      isAssistant ? "text-slate-500" : "text-purple-200"
                    }`}
                  >
                    {m.timestamp}
                  </span>
                </div>

                {/* Analysis Trace & Tools */}
                {isAssistant && m.tools_used && m.tools_used.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {m.tools_used.map((tool, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-950/40 border border-purple-800/30 text-[10px] font-mono text-purple-300"
                      >
                        <Layers className="w-2.5 h-2.5 text-purple-400" />
                        Engine: {tool}
                      </span>
                    ))}
                  </div>
                )}

                {/* Statutory Citations */}
                {isAssistant && m.citations && m.citations.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Cited Statutory References:
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {m.citations.map((c: Citation, idx: number) => (
                        <div
                          key={idx}
                          className="bg-slate-900/60 border border-border/60 rounded-xl p-2.5 text-[11px] text-slate-300 flex items-start justify-between gap-2"
                        >
                          <div>
                            <p className="font-semibold text-purple-300">{c.document_name}</p>
                            <p className="text-[10px] text-slate-400 mt-0.5">{c.section}</p>
                            <p className="text-[9px] text-slate-500 font-mono mt-0.5">Source: {c.source}</p>
                          </div>
                          {c.url && (
                            <a
                              href={c.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-purple-400 hover:text-purple-300 shrink-0 p-1"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-3.5 items-start">
            <div className="w-8 h-8 rounded-xl bg-purple-600 flex items-center justify-center text-white shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-card border border-border/80 flex items-center gap-2 text-xs text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
              Computing statutory tax rules & regime models...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Starter Questions Bar */}
      {messages.length === 1 && (
        <div className="pt-3 pb-2 flex flex-wrap gap-2 shrink-0">
          {starterQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(q)}
              className="text-[11px] bg-slate-900 hover:bg-purple-950/50 text-slate-300 hover:text-purple-300 border border-border hover:border-purple-500/40 px-3 py-1.5 rounded-xl transition-all font-medium"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="pt-3 shrink-0"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your tax liability, Old vs New regime, 80C deductions..."
            disabled={loading}
            className="w-full bg-slate-900 border border-border rounded-2xl px-4 py-3.5 pr-12 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-all font-medium"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white rounded-xl transition-all shadow-md shadow-purple-500/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-slate-500 text-center mt-2 flex items-center justify-center gap-1">
          <Info className="w-3 h-3" /> All tax computations are strictly deterministic. Not formal Chartered Accountant advice.
        </p>
      </form>
    </div>
  );
}
