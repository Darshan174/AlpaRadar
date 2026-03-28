"use client";

import { useEffect, useRef, useState } from "react";
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

    const nextUserMessage: Message = { role: "user", content: message };
    setMessages((previous) => [...previous, nextUserMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(message, {
        ticker: ticker || undefined,
        history: messages.map((item) => ({ role: item.role, content: item.content })),
      });

      setMessages((previous) => [...previous, { role: "assistant", content: response.response }]);
    } catch (issue) {
      const text = issue instanceof Error ? issue.message : "Unable to contact the chat service";
      setMessages((previous) => [...previous, { role: "assistant", content: `Error: ${text}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="kicker">Analyst Copilot</div>
              <h1 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
                Query the platform in natural language without leaving context.
              </h1>
              <p className="mt-4 text-base leading-8 text-(--color-text-secondary)">
                Ask about companies, sectors, signals, and rival dynamics. The redesigned workspace keeps prompts, examples, and conversation state in a single dense research surface.
              </p>
            </div>

            <div className="surface-panel-muted rounded-[26px] p-4">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Optional ticker focus
              </div>
              <input
                type="text"
                value={ticker}
                onChange={(event) => setTicker(event.target.value.toUpperCase())}
                placeholder="e.g. NVDA"
                maxLength={10}
                className="mt-3 w-full bg-transparent text-lg text-(--color-text-primary) outline-none placeholder:text-(--color-text-muted)"
              />
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="space-y-6">
            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Quick Actions
              </div>
              <div className="mt-4 grid gap-3">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => handleSend(action.query)}
                    className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 px-4 py-3 text-left text-sm font-semibold text-(--color-text-primary) transition hover:border-(--color-border-strong)"
                  >
                    <div>{action.label}</div>
                    <div className="mt-1 text-xs font-normal leading-6 text-(--color-text-muted)">
                      {action.query}
                    </div>
                  </button>
                ))}
              </div>
            </section>

            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Best Uses
              </div>
              <div className="mt-4 space-y-3 text-sm leading-7 text-(--color-text-secondary)">
                <p>Interrogate sector hiring acceleration and executive churn.</p>
                <p>Run ad hoc company comparisons before opening the dedicated compare view.</p>
                <p>Get fast summaries of where signal clusters are forming across the platform.</p>
              </div>
            </section>
          </aside>

          <section className="surface-panel flex min-h-[760px] flex-col rounded-[32px] p-4 sm:p-5">
            <div className="flex items-center justify-between gap-3 border-b border-(--color-border) px-2 pb-4">
              <div>
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                  Conversation
                </div>
                <div className="mt-2 text-xl font-semibold text-(--color-text-primary)">
                  {ticker ? `Focused on ${ticker}` : "General market intelligence"}
                </div>
              </div>
              <span className="status-pill">
                <span className="live-dot" />
                AI active
              </span>
            </div>

            <div className="app-scroll flex-1 overflow-y-auto px-2 py-5">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-6 text-center">
                  <div className="flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-[30px] bg-linear-to-br from-orange-500/20 to-sky-500/20 text-3xl font-black text-(--color-text-primary)">
                    AI
                  </div>
                  <div>
                    <div className="font-display text-3xl text-(--color-text-primary)">What do you want to investigate?</div>
                    <p className="mt-3 max-w-2xl text-base leading-8 text-(--color-text-secondary)">
                      Ask a direct question or use one of the prompt starters below. The conversation will stay grounded in AlphaRadar’s company and signal context.
                    </p>
                  </div>
                  <div className="grid w-full max-w-3xl gap-3 md:grid-cols-2">
                    {EXAMPLES.map((example) => (
                      <button
                        key={example}
                        onClick={() => handleSend(example)}
                        className="rounded-[24px] border border-(--color-border) bg-(--color-bg-hover)/28 px-5 py-4 text-left text-sm leading-7 text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, index) => (
                    <ChatMessage key={index} role={message.role} content={message.content} />
                  ))}
                  {loading ? (
                    <div className="flex justify-start">
                      <div className="surface-panel rounded-[24px] rounded-bl-md px-4 py-4 text-sm text-(--color-text-muted)">
                        <span className="inline-flex gap-1">
                          <span className="pulse-dot">.</span>
                          <span className="pulse-dot" style={{ animationDelay: "0.2s" }}>.</span>
                          <span className="pulse-dot" style={{ animationDelay: "0.4s" }}>.</span>
                        </span>
                      </div>
                    </div>
                  ) : null}
                  <div ref={bottomRef} />
                </div>
              )}
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                handleSend();
              }}
              className="border-t border-(--color-border) px-2 pt-4"
            >
              <div className="flex flex-col gap-3 lg:flex-row">
                <input
                  type="text"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Ask about any company, sector, signal, or talent shift..."
                  disabled={loading}
                  className="w-full flex-1 rounded-[22px] border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-4 text-sm text-(--color-text-primary) outline-none focus:border-(--color-accent)"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="rounded-[22px] bg-linear-to-r from-orange-500 to-amber-500 px-6 py-4 text-sm font-semibold text-white transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Send prompt
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
