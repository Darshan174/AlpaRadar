"use client";

import { useEffect, useState } from "react";
import { SentimentBadge } from "@/components/sentiment-badge";
import { getWatchlist, addToWatchlist, removeFromWatchlist } from "@/lib/api";
import type { WatchlistItem, Sentiment } from "@/lib/types";

const USER_ID = "default-user"; // Replace with auth later

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
          Track tickers and get automatic alerts when signals fire
        </p>
      </div>

      {/* Add ticker */}
      <form onSubmit={handleAdd} className="mb-6 flex max-w-md gap-2">
        <input
          type="text"
          value={tickerInput}
          onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
          placeholder="Add ticker (e.g. NVDA)"
          className="flex-1 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
          maxLength={10}
          disabled={adding}
        />
        <button
          type="submit"
          disabled={adding || !tickerInput.trim()}
          className="rounded-lg bg-(--color-accent) px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
        >
          {adding ? "Adding..." : "Add"}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-3 text-sm text-(--color-bearish)">
          {error}
        </div>
      )}

      {/* Watchlist table */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-sm text-(--color-text-muted)">
          Loading...
        </div>
      ) : items.length === 0 ? (
        <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-(--color-border) text-sm text-(--color-text-muted)">
          <p>Your watchlist is empty</p>
          <p className="text-xs">Add tickers above to start receiving signal alerts</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-(--color-border)">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-(--color-border) bg-(--color-bg-secondary)">
                <th className="px-4 py-3 text-xs font-medium text-(--color-text-muted)">Ticker</th>
                <th className="px-4 py-3 text-xs font-medium text-(--color-text-muted)">Company</th>
                <th className="px-4 py-3 text-xs font-medium text-(--color-text-muted)">Alerts</th>
                <th className="px-4 py-3 text-xs font-medium text-(--color-text-muted)">Added</th>
                <th className="px-4 py-3 text-xs font-medium text-(--color-text-muted)"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.ticker}
                  className="border-b border-(--color-border) transition-colors hover:bg-(--color-bg-hover)"
                >
                  <td className="px-4 py-3 font-bold">{item.ticker}</td>
                  <td className="px-4 py-3 text-(--color-text-secondary)">
                    {item.company_name || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {item.alert_on.map((type) => (
                        <span
                          key={type}
                          className="rounded bg-(--color-bg-secondary) px-1.5 py-0.5 text-[10px] text-(--color-text-muted)"
                        >
                          {type.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-(--color-text-muted)">
                    {new Date(item.added_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleRemove(item.ticker)}
                      className="text-xs text-(--color-bearish) hover:underline"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
