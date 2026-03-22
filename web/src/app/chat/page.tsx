"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/chat-message";
import { sendChat } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

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
      <div className="border-b border-(--color-border) px-6 py-4">
        <h1 className="text-lg font-bold">Chat</h1>
        <p className="text-xs text-(--color-text-muted)">
          Ask anything about stocks — powered by alternative data + RAG
        </p>
        {/* Optional ticker focus */}
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs text-(--color-text-muted)">Focus on ticker:</span>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Optional"
            className="w-24 rounded border border-(--color-border) bg-(--color-bg-card) px-2 py-1 text-xs text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
            maxLength={10}
          />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4">
            <div className="text-center">
              <div className="mb-2 text-lg font-semibold text-(--color-text-secondary)">
                Ask AlphaRadar
              </div>
              <p className="text-sm text-(--color-text-muted)">
                Get hedge fund-level insights from alternative data
              </p>
            </div>
            <div className="grid max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => handleSend(ex)}
                  className="rounded-lg border border-(--color-border) bg-(--color-bg-card) px-3 py-2 text-left text-xs text-(--color-text-secondary) transition-colors hover:border-(--color-accent)/40 hover:text-(--color-text-primary)"
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
            className="flex-1 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-lg bg-(--color-accent) px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
