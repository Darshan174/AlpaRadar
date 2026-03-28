"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { SignalCard } from "@/components/signal-card";
import { StatCard } from "@/components/stat-card";
import { getFeed } from "@/lib/api";
import { getAverageScore, getSectorSnapshots, getSentimentBalance, getSignalMix, getTopSignals } from "@/lib/presentation";
import type { Signal, SignalType } from "@/lib/types";
import { SIGNAL_LABELS } from "@/lib/types";

const SIGNAL_TYPES: SignalType[] = [
  "hiring_surge",
  "executive_move",
  "growth_price_divergence",
  "competitor_shift",
  "sector_pulse",
];

export default function RadarPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [totalSignals, setTotalSignals] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"feed" | "sector">("feed");
  const [tickerFilter, setTickerFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [minScore, setMinScore] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadSignals() {
      setLoading(true);
      setError(null);

      try {
        const response = await getFeed({
          ticker: tickerFilter || undefined,
          type: typeFilter || undefined,
          min_score: minScore || undefined,
          limit: 50,
        });

        if (!cancelled) {
          setSignals(response.signals);
          setTotalSignals(response.total);
        }
      } catch (issue) {
        if (!cancelled) {
          setError(issue instanceof Error ? issue.message : "Unable to load the radar feed");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadSignals();
    return () => {
      cancelled = true;
    };
  }, [tickerFilter, typeFilter, minScore]);

  const balance = getSentimentBalance(signals);
  const signalMix = getSignalMix(signals);
  const sectorSignals = getSectorSnapshots(signals);
  const topSignals = getTopSignals(signals, 3);
  const strongSignals = signals.filter((signal) => signal.strength === "strong").length;
  const avgScore = getAverageScore(signals);
  const tickerActivity = Object.entries(
    signals.reduce<Record<string, number>>((summary, signal) => {
      summary[signal.ticker] = (summary[signal.ticker] || 0) + 1;
      return summary;
    }, {}),
  )
    .sort((left, right) => right[1] - left[1])
    .slice(0, 5);

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <div className="kicker">Current signal radar</div>
              <h1 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
                The current feed, filtered and organized for actual research work.
              </h1>
              <p className="mt-4 text-base leading-8 text-(--color-text-secondary)">
                Filter the current signal set, surface the strongest stories, and pivot from a market-wide view into company and signal-level evidence without unsupported metrics or invented market views.
              </p>
            </div>

            <div className="inline-flex rounded-full border border-(--color-border) bg-(--color-bg-card-strong) p-1">
              <button
                onClick={() => setView("feed")}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  view === "feed"
                    ? "bg-linear-to-r from-orange-500 to-amber-500 text-white"
                    : "text-(--color-text-secondary)"
                }`}
              >
                Signal feed
              </button>
              <button
                onClick={() => setView("sector")}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  view === "sector"
                    ? "bg-linear-to-r from-orange-500 to-amber-500 text-white"
                    : "text-(--color-text-secondary)"
                }`}
              >
                Sector signals
              </button>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Signals in result set" value={totalSignals} sub="api total" />
            <StatCard label="Average score" value={avgScore || "--"} sub="derived" />
            <StatCard label="Strong conviction" value={strongSignals} sub="priority" color="text-(--color-strong)" />
            <StatCard
              label="Net sentiment"
              value={balance.net > 0 ? `+${balance.net}` : balance.net}
              sub={balance.bias}
              color={
                balance.bias === "bullish"
                  ? "text-(--color-bullish)"
                  : balance.bias === "bearish"
                    ? "text-(--color-bearish)"
                    : "text-(--color-text-primary)"
              }
            />
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="surface-panel rounded-[32px] p-5 lg:p-6">
            <div className="flex flex-col gap-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                    Feed Controls
                  </div>
                  <div className="mt-2 text-2xl font-semibold text-(--color-text-primary)">
                    {view === "feed" ? "Conviction-ranked signal stream" : "Sector signals from the current result set"}
                  </div>
                </div>

                {view === "feed" ? (
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      value={tickerFilter}
                      onChange={(event) => setTickerFilter(event.target.value.toUpperCase())}
                      placeholder="Ticker"
                      className="rounded-full border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-2 text-sm text-(--color-text-primary) outline-none focus:border-(--color-accent)"
                    />
                    <select
                      value={typeFilter}
                      onChange={(event) => setTypeFilter(event.target.value)}
                      className="rounded-full border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-2 text-sm text-(--color-text-primary) outline-none focus:border-(--color-accent)"
                    >
                      <option value="">All signal types</option>
                      {SIGNAL_TYPES.map((signalType) => (
                        <option key={signalType} value={signalType}>
                          {SIGNAL_LABELS[signalType]}
                        </option>
                      ))}
                    </select>
                    <select
                      value={minScore}
                      onChange={(event) => setMinScore(Number(event.target.value))}
                      className="rounded-full border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-2 text-sm text-(--color-text-primary) outline-none focus:border-(--color-accent)"
                    >
                      <option value={0}>Any score</option>
                      <option value={50}>50+</option>
                      <option value={70}>70+</option>
                      <option value={80}>80+</option>
                    </select>
                    {(tickerFilter || typeFilter || minScore > 0) ? (
                      <button
                        onClick={() => {
                          setTickerFilter("");
                          setTypeFilter("");
                          setMinScore(0);
                        }}
                        className="rounded-full border border-(--color-border) px-4 py-2 text-sm text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
                      >
                        Reset
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>

              {loading ? (
                <div className="flex h-80 items-center justify-center text-sm text-(--color-text-muted)">
                  <div className="h-7 w-7 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
                </div>
              ) : error ? (
                <div className="rounded-[26px] border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-6 text-sm text-(--color-bearish)">
                  {error}
                  <p className="mt-2 text-(--color-text-secondary)">Make sure the API is running on `http://localhost:8000`.</p>
                </div>
              ) : view === "feed" ? (
                signals.length > 0 ? (
                  <div className="space-y-4">
                    {signals.map((signal) => (
                      <Link key={signal.id} href={`/signal/${signal.id}`} className="block">
                        <SignalCard signal={signal} />
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="flex h-72 flex-col items-center justify-center gap-3 rounded-[28px] border border-dashed border-(--color-border) text-center">
                    <div className="text-lg font-semibold text-(--color-text-primary)">No signals match the current filter set.</div>
                    <p className="max-w-md text-sm text-(--color-text-muted)">
                      Clear the feed controls or open a company directly to inspect what the current dataset contains.
                    </p>
                    <Link href="/" className="rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)">
                      Explore landing page
                    </Link>
                  </div>
                )
              ) : (
                <div>
                  <p className="mb-5 max-w-2xl text-sm leading-7 text-(--color-text-secondary)">
                    These panels are built only from actual `sector_pulse` signals returned in the current result set. If the feed has no sector signals, nothing is inferred.
                  </p>
                  {sectorSignals.length > 0 ? (
                    <div className="grid gap-4 lg:grid-cols-2">
                      {sectorSignals.map((item) => (
                        <Link key={item.id} href={`/signal/${item.id}`} className="surface-panel hover-lift rounded-[28px] p-5">
                          <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                            {item.sector}
                          </div>
                          <div className="mt-3 text-lg font-semibold text-(--color-text-primary)">
                            {item.headline}
                          </div>
                          <div className="mt-4 grid grid-cols-2 gap-3">
                            <div className="rounded-[20px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                              <div className="text-xs text-(--color-text-muted)">Aggregate postings</div>
                              <div className="mt-1 metric-value text-3xl text-(--color-text-primary)">{item.aggregatePostings ?? "—"}</div>
                            </div>
                            <div className="rounded-[20px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                              <div className="text-xs text-(--color-text-muted)">AI share</div>
                              <div className="mt-1 metric-value text-3xl text-(--color-text-primary)">
                                {item.aiSharePct != null ? `${item.aiSharePct.toFixed(0)}%` : "—"}
                              </div>
                            </div>
                          </div>
                          <div className="mt-4 flex flex-wrap gap-2">
                            {[...item.expanding, ...item.flat].map((ticker) => (
                              <span key={`${item.id}-${ticker}`} className="data-chip">{ticker}</span>
                            ))}
                          </div>
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-[28px] border border-dashed border-(--color-border) p-8 text-sm text-(--color-text-muted)">
                      No sector-pulse signals are available in the current result set.
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          <div className="space-y-6">
            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Market Pulse
              </div>
              <div className="mt-4 grid grid-cols-3 gap-3">
                <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/32 p-3">
                  <div className="text-xs text-(--color-text-muted)">Bullish</div>
                  <div className="mt-2 metric-value text-3xl text-(--color-bullish)">{balance.bullish}</div>
                </div>
                <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/32 p-3">
                  <div className="text-xs text-(--color-text-muted)">Neutral</div>
                  <div className="mt-2 metric-value text-3xl text-(--color-neutral)">{balance.neutral}</div>
                </div>
                <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/32 p-3">
                  <div className="text-xs text-(--color-text-muted)">Bearish</div>
                  <div className="mt-2 metric-value text-3xl text-(--color-bearish)">{balance.bearish}</div>
                </div>
              </div>
            </section>

            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Signal Mix
              </div>
              <div className="mt-4 space-y-3">
                {signalMix.length > 0 ? (
                  signalMix.map((bucket) => (
                    <div key={bucket.type} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="font-semibold text-(--color-text-primary)">{bucket.label}</div>
                          <div className="mt-1 text-xs text-(--color-text-muted)">{bucket.count} signals</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-(--color-text-muted)">Avg score</div>
                          <div className="metric-value text-2xl text-(--color-text-primary)">{bucket.avgScore}</div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-(--color-text-muted)">No live mix data yet.</div>
                )}
              </div>
            </section>

            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Spotlight Signals
              </div>
              <div className="mt-4 space-y-3">
                {topSignals.map((signal) => (
                  <Link
                    key={signal.id}
                    href={`/signal/${signal.id}`}
                    className="block rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4 transition hover:border-(--color-border-strong)"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-semibold text-(--color-text-primary)">{signal.ticker}</div>
                        <div className="mt-1 text-sm text-(--color-text-secondary)">{signal.headline}</div>
                      </div>
                      <div className="metric-value text-2xl text-(--color-accent)">{signal.score}</div>
                    </div>
                  </Link>
                ))}
                {topSignals.length === 0 ? (
                  <div className="text-sm text-(--color-text-muted)">No standout signals yet.</div>
                ) : null}
              </div>
            </section>

            <section className="surface-panel rounded-[30px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Active Tickers
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {tickerActivity.length > 0 ? (
                  tickerActivity.map(([ticker, count]) => (
                    <Link key={ticker} href={`/company/${ticker}`} className="data-chip hover:border-(--color-border-strong)">
                      <span>{ticker}</span>
                      <span className="text-(--color-text-muted)">{count}</span>
                    </Link>
                  ))
                ) : (
                  <span className="text-sm text-(--color-text-muted)">No ticker activity yet.</span>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
