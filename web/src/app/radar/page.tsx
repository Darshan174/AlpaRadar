"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SignalCard } from "@/components/signal-card";
import { SectorHeatmap } from "@/components/sector-heatmap";
import { StatCard } from "@/components/stat-card";
import { getSignals } from "@/lib/api";
import type { Signal } from "@/lib/types";

export default function RadarPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"feed" | "heatmap">("feed");

  useEffect(() => {
    getSignals({ limit: 30, min_score: 30 })
      .then(setSignals)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const strong = signals.filter((s) => s.strength === "strong").length;
  const bullish = signals.filter((s) => s.sentiment === "bullish").length;
  const bearish = signals.filter((s) => s.sentiment === "bearish").length;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-(--color-border) px-6 py-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">Live Radar</h1>
              <span className="pulse-dot inline-block h-2 w-2 rounded-full bg-(--color-bullish)" />
            </div>
            <p className="text-xs text-(--color-text-muted)">
              Real-time alternative data signals across all tracked companies
            </p>
          </div>

          {/* View toggle */}
          <div className="flex rounded-lg border border-(--color-border) p-0.5">
            <button
              onClick={() => setView("feed")}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                view === "feed"
                  ? "bg-(--color-accent) text-white"
                  : "text-(--color-text-secondary) hover:text-(--color-text-primary)"
              }`}
            >
              Signal Feed
            </button>
            <button
              onClick={() => setView("heatmap")}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                view === "heatmap"
                  ? "bg-(--color-accent) text-white"
                  : "text-(--color-text-secondary) hover:text-(--color-text-primary)"
              }`}
            >
              Sector Heatmap
            </button>
          </div>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-3 border-b border-(--color-border) px-6 py-3">
        <StatCard label="Active Signals" value={signals.length} sub="scanning" />
        <StatCard label="Strong" value={strong} color="text-(--color-strong)" />
        <StatCard
          label="Net Sentiment"
          value={bullish > bearish ? `+${bullish - bearish} bull` : bearish > bullish ? `+${bearish - bullish} bear` : "Balanced"}
          color={bullish > bearish ? "text-(--color-bullish)" : bearish > bullish ? "text-(--color-bearish)" : "text-(--color-text-secondary)"}
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading && (
          <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-4 text-sm text-(--color-bearish)">
            {error}
            <p className="mt-1 text-xs text-(--color-text-muted)">
              Make sure the API is running on localhost:8000
            </p>
          </div>
        )}

        {!loading && !error && view === "feed" && (
          <div>
            {signals.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-(--color-border) text-sm text-(--color-text-muted)">
                <p>No signals detected yet</p>
                <Link href="/" className="text-(--color-accent) hover:underline">
                  Analyze a company to start generating signals
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {signals.map((signal) => (
                  <Link key={signal.id} href={`/company/${signal.ticker}`} className="block">
                    <SignalCard signal={signal} />
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {!loading && !error && view === "heatmap" && (
          <div>
            <p className="mb-4 text-sm text-(--color-text-secondary)">
              Sector hiring trends — green = expanding, red = contracting. Click a ticker to explore.
            </p>
            <SectorHeatmap />
          </div>
        )}
      </div>
    </div>
  );
}
