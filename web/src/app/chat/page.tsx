"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ChatMessage } from "@/components/chat-message";
import { sendChat } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const QUICK_ACTIONS = [
  { label: "Hiring surges", query: "Which companies have the biggest hiring surges right now?" },
  { label: "Exec moves", query: "What are the most significant executive movements this week?" },
  { label: "Sector trends", query: "Which sectors are seeing the most hiring growth?" },
  { label: "AI talent war", query: "Which companies are winning the AI talent war?" },
  { label: "Bearish signals", query: "Which public companies have the most bearish alternative data signals?" },
  { label: "Pre-earnings", query: "What upcoming earnings have the strongest alt-data signals?" },
];

const EXAMPLES = [
  "Which semiconductor companies hired the most AI engineers recently?",
  "Is PLTR's hiring trend bullish or bearish?",
  "Compare SNAP vs META talent flow",
  "What sectors are seeing hiring surges right now?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ticker, setTicker] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const message = (text || input).trim();
    if (!message || loading) return;

    const userMsg: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendChat(message, {
        ticker: ticker || undefined,
        history,
      });
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${e.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-(--color-border) px-6 py-3">
        <div>
          <h1 className="text-lg font-bold">Ask AlphaRadar</h1>
          <p className="text-xs text-(--color-text-muted)">
            Hedge fund-level insights via natural language
          </p>
        </div>
        {/* Ticker focus */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-(--color-text-muted) hidden sm:inline">Focus:</span>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Ticker"
            className="w-20 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-2 py-1 text-xs text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
            maxLength={10}
          />
        </div>
      </div>

      {/* Quick actions bar */}
      {messages.length === 0 && (
        <div className="flex gap-2 overflow-x-auto border-b border-(--color-border) px-6 py-2">
          {QUICK_ACTIONS.map((qa) => (
            <button
              key={qa.label}
              onClick={() => handleSend(qa.query)}
              className="shrink-0 rounded-full border border-(--color-border) bg-(--color-bg-card) px-3 py-1 text-[11px] font-medium text-(--color-text-secondary) transition-colors hover:border-(--color-accent)/40 hover:text-(--color-accent)"
            >
              {qa.label}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-(--color-accent)/10">
              <span className="text-2xl font-bold text-(--color-accent)">AI</span>
            </div>
            <div className="text-center">
              <div className="mb-1 text-lg font-semibold">What would you like to know?</div>
              <p className="text-sm text-(--color-text-muted)">
                Ask about any company, sector, or signal — backed by real-time alt-data
              </p>
            </div>
            <div className="grid max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => handleSend(ex)}
                  className="rounded-xl border border-(--color-border) bg-(--color-bg-card) px-4 py-3 text-left text-xs leading-relaxed text-(--color-text-secondary) transition-colors hover:border-(--color-accent)/40 hover:text-(--color-text-primary) card-shadow"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {messages.map((msg, i) => (
            <ChatMessage key={i} role={msg.role} content={msg.content} />
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md border border-(--color-border) bg-(--color-bg-card) px-4 py-3 text-sm text-(--color-text-muted)">
                <span className="inline-flex gap-1">
                  <span className="pulse-dot">.</span>
                  <span className="pulse-dot" style={{ animationDelay: "0.2s" }}>.</span>
                  <span className="pulse-dot" style={{ animationDelay: "0.4s" }}>.</span>
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-(--color-border) px-6 py-4">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about any stock, sector, or signal..."
            className="flex-1 rounded-xl border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent) focus:ring-2 focus:ring-(--color-accent)/20"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-(--color-accent) px-5 py-2.5 text-sm font-medium text-white transition hover:bg-(--color-accent-hover) disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
