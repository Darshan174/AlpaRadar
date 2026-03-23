"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api";
import type { WatchlistItem } from "@/lib/types";

const USER_ID = "default-user";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tickerInput, setTickerInput] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  async function fetchWatchlist() {
    setLoading(true);
    try {
      const res = await getWatchlist(USER_ID);
      setItems(res.items);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const ticker = tickerInput.trim().toUpperCase();
    if (!ticker) return;
    setAdding(true);
    try {
      await addToWatchlist(USER_ID, ticker);
      setTickerInput("");
      await fetchWatchlist();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(ticker: string) {
    try {
      await removeFromWatchlist(USER_ID, ticker);
      setItems((prev) => prev.filter((i) => i.ticker !== ticker));
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Watchlist</h1>
        <p className="text-sm text-(--color-text-muted)">
          Track companies and get automatic alerts when alt-data signals fire
        </p>
      </div>

      {/* Add ticker */}
      <form onSubmit={handleAdd} className="mb-6 flex max-w-md gap-2">
        <input
          type="text"
          value={tickerInput}
          onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
          placeholder="Add ticker (e.g. NVDA)"
          className="flex-1 rounded-xl border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent) focus:ring-2 focus:ring-(--color-accent)/20 card-shadow"
          maxLength={10}
          disabled={adding}
        />
        <button
          type="submit"
          disabled={adding || !tickerInput.trim()}
          className="rounded-xl bg-(--color-accent) px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-(--color-accent-hover) disabled:opacity-40"
        >
          {adding ? "..." : "Add"}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-3 text-sm text-(--color-bearish)">
          {error}
        </div>
      )}

      {/* Watchlist cards (mobile-friendly) */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-(--color-border)">
          <div className="text-sm text-(--color-text-muted)">Your watchlist is empty</div>
          <p className="text-xs text-(--color-text-muted)">Add tickers to get alerted on hiring surges, exec moves, and more</p>
          <Link href="/" className="text-xs text-(--color-accent) hover:underline">
            Explore trending companies
          </Link>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <div
              key={item.ticker}
              className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-4 transition-colors hover:border-(--color-accent)/30 card-shadow"
            >
              <div className="mb-3 flex items-center justify-between">
                <Link
                  href={`/company/${item.ticker}`}
                  className="text-lg font-bold transition-colors hover:text-(--color-accent)"
                >
                  {item.ticker}
                </Link>
                <button
                  onClick={() => handleRemove(item.ticker)}
                  className="rounded-lg px-2 py-1 text-[10px] text-(--color-text-muted) transition-colors hover:bg-(--color-bearish)/10 hover:text-(--color-bearish)"
                >
                  Remove
                </button>
              </div>

              {item.company_name && (
                <div className="mb-3 text-xs text-(--color-text-muted)">{item.company_name}</div>
              )}

              {/* Alert types */}
              <div className="mb-3 flex flex-wrap gap-1">
                {item.alert_on.map((type) => (
                  <span
                    key={type}
                    className="rounded-full bg-(--color-accent)/10 px-2 py-0.5 text-[10px] font-medium text-(--color-accent)"
                  >
                    {type.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between text-[10px] text-(--color-text-muted)">
                <span>Added {new Date(item.added_at).toLocaleDateString()}</span>
                <Link
                  href={`/company/${item.ticker}`}
                  className="text-(--color-accent) hover:underline"
                >
                  View DNA
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
