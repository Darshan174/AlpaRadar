"use client";

import { useEffect, useState } from "react";
import { SignalCard } from "@/components/signal-card";
import { StatCard } from "@/components/stat-card";
import { getSignals } from "@/lib/api";
import type { Signal } from "@/lib/types";

export default function Dashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSignals({ limit: 20, min_score: 40 })
      .then(setSignals)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const strong = signals.filter((s) => s.strength === "strong").length;
  const bullish = signals.filter((s) => s.sentiment === "bullish").length;
  const bearish = signals.filter((s) => s.sentiment === "bearish").length;
  const avgScore = signals.length
    ? (signals.reduce((a, s) => a + s.score, 0) / signals.length).toFixed(0)
    : "—";

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-(--color-text-muted)">
          Real-time alternative data signals across your universe
        </p>
      </div>

      {/* Stats row */}
      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Active Signals" value={signals.length} sub="Last 24h" />
        <StatCard label="Strong Signals" value={strong} color="text-(--color-strong)" />
        <StatCard
          label="Sentiment"
          value={bullish > bearish ? "Bullish" : bearish > bullish ? "Bearish" : "Mixed"}
          sub={`${bullish} bull / ${bearish} bear`}
          color={bullish > bearish ? "text-(--color-bullish)" : "text-(--color-bearish)"}
        />
        <StatCard label="Avg Score" value={avgScore} sub="out of 100" />
      </div>

      {/* Signal Feed */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Recent Signals</h2>
        <a href="/signals" className="text-xs text-(--color-accent) hover:underline">
          View all &rarr;
        </a>
      </div>

      {loading && (
        <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
          Loading signals...
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-4 text-sm text-(--color-bearish)">
          {error}
          <p className="mt-1 text-xs text-(--color-text-muted)">
            Make sure the API server is running on localhost:8000
          </p>
        </div>
      )}

      {!loading && !error && signals.length === 0 && (
        <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-(--color-border) text-sm text-(--color-text-muted)">
          <p>No signals yet</p>
          <a href="/analyze" className="text-(--color-accent) hover:underline">
            Analyze a ticker to generate signals &rarr;
          </a>
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {signals.map((signal) => (
          <SignalCard key={signal.id} signal={signal} />
        ))}
      </div>
    </div>
  );
}
