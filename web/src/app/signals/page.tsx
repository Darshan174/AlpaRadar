"use client";

import { useEffect, useState } from "react";
import { SignalCard } from "@/components/signal-card";
import { getSignals, searchSignals } from "@/lib/api";
import { SIGNAL_LABELS } from "@/lib/types";
import type { Signal, SignalType } from "@/lib/types";

const TYPES: (SignalType | "all")[] = [
  "all",
  "hiring_surge",
  "executive_move",
  "growth_price_divergence",
  "competitor_shift",
  "sector_pulse",
];

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchSignals();
  }, [typeFilter]);

  async function fetchSignals() {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { limit: 50 };
      if (typeFilter !== "all") params.type = typeFilter;
      const data = await getSignals(params);
      setSignals(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return fetchSignals();
    setSearching(true);
    setError(null);
    try {
      const result = await searchSignals(searchQuery.trim());
      setSignals(result.results);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Signals</h1>
        <p className="text-sm text-(--color-text-muted)">
          Browse and search alternative data signals
        </p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="mb-4 flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Semantic search (e.g. 'AI companies hiring aggressively')..."
          className="flex-1 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
        />
        <button
          type="submit"
          disabled={searching}
          className="rounded-lg bg-(--color-accent) px-4 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
        >
          {searching ? "..." : "Search"}
        </button>
      </form>

      {/* Type filters */}
      <div className="mb-5 flex flex-wrap gap-2">
        {TYPES.map((type) => (
          <button
            key={type}
            onClick={() => { setTypeFilter(type); setSearchQuery(""); }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              typeFilter === type
                ? "bg-(--color-accent) text-white"
                : "border border-(--color-border) text-(--color-text-secondary) hover:bg-(--color-bg-hover)"
            }`}
          >
            {type === "all" ? "All" : SIGNAL_LABELS[type]}
          </button>
        ))}
      </div>

      {/* Results */}
      {loading && (
        <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
          Loading...
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-4 text-sm text-(--color-bearish)">
          {error}
        </div>
      )}

      {!loading && !error && signals.length === 0 && (
        <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
          No signals found. Try analyzing a ticker first.
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
