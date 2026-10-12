import { useEffect, useRef, useState } from "react";
import { Bot, RefreshCw, Send, Sparkles, Trash2, UserRound, X } from "lucide-react";
import { clearChatHistory, fetchChatHistory, sendChatMessage } from "../api/client.js";

const MODES = [
  ["simple", "Simple"],
  ["technical", "Technical"],
  ["clinical_research", "Clinical / Research"],
];

const MODE_HELP = {
  simple: "Easy explanation with minimal ML/XAI jargon.",
  technical: "Deeper ML/XAI explanation using verified implementation details.",
  clinical_research: "Evidence, uncertainty and limitations for research discussion — not diagnosis or treatment.",
};

const SUGGESTIONS = [
  "Explain this scan result.",
  "What does the confidence score mean?",
  "What can Grad-CAM tell me about this prediction?",
  "Compare Grad-CAM, Integrated Gradients, and SHAP.",
];

function InlineFormat({ text }) {
  const parts = String(text).split(/(\*\*[^*]+\*\*|\x60[^\x60]+\x60)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index} className="font-semibold text-slate-100">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index} className="rounded bg-white/[0.06] px-1.5 py-0.5 text-xs text-brand-300">{part.slice(1, -1)}</code>;
    }
    return <span key={index}>{part}</span>;
  });
}

function SafeAssistantText({ content }) {
  return (
    <div className="space-y-2.5">
      {String(content).split("\n").map((raw, index) => {
        const line = raw.trim();
        if (!line) return <div key={index} className="h-1" />;
        const heading = line.match(/^#{1,4}\s+(.*)$/);
        if (heading) {
          return <h3 key={index} className="pt-1 text-sm font-semibold text-slate-100"><InlineFormat text={heading[1]} /></h3>;
        }
        const bullet = line.match(/^[-*]\s+(.*)$/);
        if (bullet) {
          return <div key={index} className="flex gap-2"><span className="mt-[1px] text-brand-400">•</span><p><InlineFormat text={bullet[1]} /></p></div>;
        }
        const numbered = line.match(/^(\d+)\.\s+(.*)$/);
        if (numbered) {
          return <div key={index} className="flex gap-2"><span className="min-w-5 font-medium text-brand-400">{numbered[1]}.</span><p><InlineFormat text={numbered[2]} /></p></div>;
        }
        if (line.startsWith("$$") && line.endsWith("$$")) {
          return <div key={index} className="overflow-x-auto rounded-lg bg-black/20 px-3 py-2 font-mono text-xs text-slate-300">{line.slice(2, -2)}</div>;
        }
        return <p key={index}><InlineFormat text={raw} /></p>;
      })}
    </div>
  );
}

export default function ScanAssistant({ scanId }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("simple");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [historyLoading, setHistoryLoading] = useState(true);
  const endRef = useRef(null);

  useEffect(() => {
    let active = true;
    setHistoryLoading(true);
    fetchChatHistory(scanId)
      .then((data) => {
        if (!active) return;
        setMessages(data.messages || []);
        if (data.mode) setMode(data.mode);
      })
      .catch(() => {
        if (active) setError("Previous assistant conversation could not be loaded.");
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => { active = false; };
  }, [scanId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, loading]);

  if (!scanId) return null;

  async function ask(question, { repeat = false } = {}) {
    const text = question.trim();
    if (!text || loading) return;

    const previous = messages.slice(-6);
    if (!repeat) {
      setMessages((items) => [...items, { role: "user", content: text }]);
    }
    setLastQuestion(text);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const data = await sendChatMessage(scanId, text, mode, previous);
      setMessages((items) => [
        ...items,
        { role: "assistant", content: data.answer, sources: data.sources || [] },
      ]);
    } catch (err) {
      const data = err?.response?.data;
      setError(data?.message || data?.error || "The NeuroScan XAI Assistant is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    ask(input);
  }

  async function clearConversation() {
    if (loading || historyLoading) return;
    try {
      await clearChatHistory(scanId);
      setMessages([]);
      setError("");
      setLastQuestion("");
    } catch {
      setError("The conversation could not be cleared. Please try again.");
    }
  }

  return (
    <section className="rounded-2xl border border-brand-400/15 bg-[#07131c]/90">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between gap-4 p-5 text-left">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-400/20 bg-brand-500/[0.07]">
            <Bot size={19} className="text-brand-400" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.13em] text-brand-400">Scan-Aware Assistant</p>
            <h2 className="mt-1 text-base font-semibold text-slate-100">Ask NeuroScan XAI</h2>
            <p className="mt-1 text-xs text-slate-500">Grounded in this scan's model and XAI evidence.</p>
          </div>
        </div>
        {open ? <X size={18} className="text-slate-500" /> : <Sparkles size={18} className="text-brand-400" />}
      </button>

      {open && (
        <div className="border-t border-sky-400/10 p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
            {MODES.map(([value, label]) => (
              <button key={value} type="button" disabled={loading} onClick={() => setMode(value)}
                className={`rounded-full border px-3 py-1.5 text-xs transition ${mode === value ? "border-brand-400/30 bg-brand-500/10 text-brand-300" : "border-white/[0.08] text-slate-500 hover:text-slate-300"}`}>
                {label}
              </button>
            ))}
            </div>
            {messages.length > 0 && (
              <button type="button" onClick={clearConversation} disabled={loading || historyLoading}
                className="flex shrink-0 items-center gap-1.5 rounded-lg border border-white/[0.07] px-2.5 py-1.5 text-[11px] text-slate-500 transition hover:border-red-400/20 hover:text-red-300 disabled:opacity-50">
                <Trash2 size={12} /> New conversation
              </button>
            )}
          </div>

          <div className="mb-4 rounded-xl border border-brand-400/10 bg-brand-500/[0.025] px-3.5 py-2.5">
            <p className="text-xs leading-5 text-slate-400">
              <span className="font-semibold text-brand-300">{MODES.find(([value]) => value === mode)?.[1]} mode:</span>{" "}{MODE_HELP[mode]}
            </p>
          </div>

          {historyLoading && (
            <div className="mb-4 flex items-center gap-2 text-xs text-slate-500">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand-400" />
              Loading this scan's conversation...
            </div>
          )}

          {!historyLoading && messages.length === 0 && (
            <div className="mb-4 grid gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((question) => (
                <button key={question} type="button" onClick={() => ask(question)}
                  className="rounded-xl border border-white/[0.07] bg-white/[0.02] px-3 py-2.5 text-left text-xs leading-5 text-slate-400 transition hover:border-brand-400/20 hover:text-slate-200">
                  {question}
                </button>
              ))}
            </div>
          )}

          {messages.length > 0 && (
            <div className="mb-4 max-h-[430px] space-y-3 overflow-y-auto rounded-xl border border-white/[0.06] bg-[#041018]/70 p-3">
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`flex gap-2.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  {message.role === "assistant" && <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-500/10"><Bot size={14} className="text-brand-400" /></div>}
                  <div className={`max-w-[88%] rounded-xl px-3.5 py-3 text-sm leading-6 ${message.role === "user" ? "bg-brand-500/10 text-slate-200" : "border border-white/[0.06] bg-white/[0.025] text-slate-300"}`}>
                    {message.role === "assistant" ? <SafeAssistantText content={message.content} /> : <p className="whitespace-pre-wrap">{message.content}</p>}
                    {message.role === "assistant" && message.sources?.length > 0 && (
                      <div className="mt-3 border-t border-white/[0.06] pt-2 text-[10px] text-slate-500">
                        Evidence available: {message.sources.join(" · ")}
                      </div>
                    )}
                  </div>
                  {message.role === "user" && <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/[0.04]"><UserRound size={14} className="text-slate-500" /></div>}
                </div>
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand-400" />
                  Interpreting the available model and XAI evidence...
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}

          {error && (
            <div className="mb-3 flex items-center justify-between gap-3 rounded-xl border border-amber-400/15 bg-amber-400/[0.04] px-3 py-2.5 text-xs leading-5 text-amber-200/80">
              <span>{error}</span>
              {lastQuestion && (
                <button type="button" disabled={loading} onClick={() => ask(lastQuestion, { repeat: true })}
                  className="flex shrink-0 items-center gap-1 rounded-lg border border-amber-300/15 px-2 py-1 text-amber-100/80 hover:bg-amber-300/[0.05]">
                  <RefreshCw size={12} /> Retry
                </button>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input value={input} onChange={(event) => setInput(event.target.value)} maxLength={4000} disabled={loading}
              placeholder="Ask about this prediction or its XAI evidence..."
              className="min-w-0 flex-1 rounded-xl border border-white/[0.08] bg-[#041018] px-4 py-3 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-brand-400/30 disabled:opacity-60" />
            <button type="submit" disabled={loading || !input.trim()} className="btn-primary px-4 disabled:cursor-not-allowed disabled:opacity-50" aria-label="Send question">
              <Send size={17} />
            </button>
          </form>

          <p className="mt-3 text-[10px] leading-4 text-slate-600">
            Research-use explanation of model and XAI outputs. Not an independent clinical diagnosis or treatment recommendation.
          </p>
        </div>
      )}
    </section>
  );
}
