"use client";

import { useState } from "react";
import { TickerInput } from "@/components/ticker-input";
import { SignalCard } from "@/components/signal-card";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { analyzeTicker } from "@/lib/api";
import type { Insight, Sentiment } from "@/lib/types";

export default function AnalyzePage() {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze(ticker: string) {
    setLoading(true);
    setError(null);
    setInsight(null);
    try {
      const result = await analyzeTicker(ticker);
      setInsight(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Analyze</h1>
        <p className="text-sm text-(--color-text-muted)">
          Enter a ticker to run full alternative data analysis — hiring trends, exec moves, growth/price gaps
        </p>
      </div>

      <div className="mb-8 max-w-lg">
        <TickerInput onSubmit={handleAnalyze} loading={loading} />
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-sm text-(--color-text-muted)">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
          <p>Fetching market data + Crustdata intelligence...</p>
          <p className="text-xs">This may take 10-30s on first run</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-4 text-sm text-(--color-bearish)">
          {error}
        </div>
      )}

      {insight && <InsightView insight={insight} />}
    </div>
  );
}

function InsightView({ insight }: { insight: Insight }) {
  return (
    <div className="space-y-6">
      {/* Hero banner */}
      <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-6">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <div className="text-xs text-(--color-text-muted)">Ticker</div>
            <div className="text-3xl font-bold">{insight.ticker}</div>
            <div className="text-sm text-(--color-text-secondary)">{insight.company_name}</div>
          </div>
          <div className="mx-4 hidden h-12 w-px bg-(--color-border) md:block" />
          <div className="text-center">
            <div className="text-xs text-(--color-text-muted)">Composite Score</div>
            <ScoreBadge score={insight.composite_score} size="lg" />
          </div>
          <div className="text-center">
            <div className="mb-1 text-xs text-(--color-text-muted)">Sentiment</div>
            <SentimentBadge sentiment={insight.sentiment as Sentiment} />
          </div>
          <div className="text-center">
            <div className="text-xs text-(--color-text-muted)">Signals</div>
            <div className="text-2xl font-bold text-(--color-accent)">{insight.signal_count}</div>
          </div>
        </div>
      </div>

      {/* LLM Analysis */}
      {insight.llm_analysis && (
        <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5">
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">AI Analysis</h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-(--color-text-primary)">
            {insight.llm_analysis}
          </div>
        </div>
      )}

      {/* Signals grid */}
      {insight.signals.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">
            Detected Signals ({insight.signals.length})
          </h3>
          <div className="grid gap-3 md:grid-cols-2">
            {insight.signals.map((signal) => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
