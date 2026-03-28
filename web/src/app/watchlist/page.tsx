"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { addToWatchlist, getWatchlist, removeFromWatchlist } from "@/lib/api";
import type { WatchlistItem } from "@/lib/types";

const USER_ID = "default-user";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tickerInput, setTickerInput] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    void fetchWatchlist();
  }, []);

  async function fetchWatchlist() {
    setLoading(true);

    try {
      const response = await getWatchlist(USER_ID);
      setItems(response.items);
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Unable to load the watchlist");
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    const ticker = tickerInput.trim().toUpperCase();
    if (!ticker) return;

    setAdding(true);
    setError(null);

    try {
      await addToWatchlist(USER_ID, ticker);
      setTickerInput("");
      await fetchWatchlist();
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Unable to add this ticker");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(ticker: string) {
    try {
      await removeFromWatchlist(USER_ID, ticker);
      setItems((previous) => previous.filter((item) => item.ticker !== ticker));
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Unable to remove this ticker");
    }
  }

  const alertSummary = items
    .flatMap((item) => item.alert_on)
    .reduce<Record<string, number>>((summary, type) => {
      summary[type] = (summary[type] || 0) + 1;
      return summary;
    }, {});

  const topAlerts = Object.entries(alertSummary).sort((left, right) => right[1] - left[1]);

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="kicker">Monitored Book</div>
              <h1 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
                Treat your watchlist like an operating surface, not a favorites drawer.
              </h1>
              <p className="mt-4 text-base leading-8 text-(--color-text-secondary)">
                Add companies, see which alert categories dominate your book, and jump directly back into company-level research when a name starts moving.
              </p>
            </div>

            <form onSubmit={handleAdd} className="surface-panel-muted w-full max-w-lg rounded-[28px] p-4">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Add a company
              </div>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                <input
                  type="text"
                  value={tickerInput}
                  onChange={(event) => setTickerInput(event.target.value.toUpperCase())}
                  placeholder="e.g. NVDA"
                  maxLength={10}
                  disabled={adding}
                  className="w-full flex-1 rounded-[22px] border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-4 text-lg text-(--color-text-primary) outline-none focus:border-(--color-accent)"
                />
                <button
                  type="submit"
                  disabled={adding || !tickerInput.trim()}
                  className="rounded-[22px] bg-linear-to-r from-orange-500 to-amber-500 px-6 py-4 text-sm font-semibold text-white transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {adding ? "Adding..." : "Add ticker"}
                </button>
              </div>
            </form>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <WatchMetric label="Companies monitored" value={items.length} />
            <WatchMetric label="Alert categories" value={Object.keys(alertSummary).length} />
            <WatchMetric label="Most common alert" value={topAlerts[0]?.[0]?.replace(/_/g, " ") || "None"} />
          </div>
        </section>

        {error ? (
          <div className="rounded-[26px] border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-6 text-sm text-(--color-bearish)">
            {error}
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <section className="surface-panel rounded-[32px] p-5 lg:p-6">
            <div className="flex items-center justify-between gap-3 border-b border-(--color-border) pb-4">
              <div>
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                  Companies
                </div>
                <div className="mt-2 text-2xl font-semibold text-(--color-text-primary)">
                  {loading ? "Loading..." : `${items.length} monitored names`}
                </div>
              </div>
              <span className="status-pill">
                <span className="live-dot" />
                watchlist loaded
              </span>
            </div>

            {loading ? (
              <div className="flex h-72 items-center justify-center text-sm text-(--color-text-muted)">
                <div className="h-7 w-7 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
              </div>
            ) : items.length === 0 ? (
              <div className="flex h-72 flex-col items-center justify-center gap-3 text-center">
                <div className="text-2xl font-semibold text-(--color-text-primary)">Your monitored book is empty.</div>
                <p className="max-w-md text-sm leading-7 text-(--color-text-muted)">
                  Add a company above to start tracking hiring surges, executive moves, competitor shifts, and earnings signals.
                </p>
                <Link
                  href="/"
                  className="rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
                >
                  Explore the platform
                </Link>
              </div>
            ) : (
              <div className="mt-5 space-y-3">
                {items.map((item) => (
                  <div key={item.ticker} className="rounded-[24px] border border-(--color-border) bg-(--color-bg-hover)/26 p-4">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-3">
                          <Link href={`/company/${item.ticker}`} className="metric-value text-3xl text-(--color-text-primary)">
                            {item.ticker}
                          </Link>
                          <span className="text-sm text-(--color-text-secondary)">{item.company_name || "Tracked company"}</span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {item.alert_on.map((type) => (
                            <span key={type} className="data-chip">
                              {type.replace(/_/g, " ")}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <div className="text-xs text-(--color-text-muted)">
                          Added {new Date(item.added_at).toLocaleDateString()}
                        </div>
                        <Link
                          href={`/company/${item.ticker}`}
                          className="rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
                        >
                          Open company
                        </Link>
                        <button
                          onClick={() => handleRemove(item.ticker)}
                          className="rounded-full border border-(--color-bearish)/25 bg-(--color-bearish)/10 px-4 py-2 text-sm font-semibold text-(--color-bearish) transition hover:bg-(--color-bearish)/14"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <aside className="space-y-6">
            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Alert Coverage
              </div>
              <div className="mt-4 space-y-3">
                {topAlerts.length > 0 ? (
                  topAlerts.map(([type, count]) => (
                    <div key={type} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-semibold text-(--color-text-primary)">{type.replace(/_/g, " ")}</span>
                        <span className="metric-value text-2xl text-(--color-accent)">{count}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-(--color-text-muted)">No alert coverage yet.</div>
                )}
              </div>
            </section>

            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Why This Matters
              </div>
              <div className="mt-4 space-y-3 text-sm leading-7 text-(--color-text-secondary)">
                <p>Use the watchlist to keep an operational pulse on your highest-priority names.</p>
                <p>When a ticker changes, the rest of the platform gives you an immediate drilldown path.</p>
                <p>A more balanced alert mix usually means broader information coverage and better monitoring discipline.</p>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

function WatchMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="surface-panel hover-lift rounded-[28px] p-5">
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
        {label}
      </div>
      <div className="mt-4 metric-value text-4xl text-(--color-text-primary)">{value}</div>
    </div>
  );
}
