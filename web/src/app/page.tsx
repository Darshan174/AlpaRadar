"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const FEATURES = [
  { title: "Hiring Surges", desc: "Spot companies scaling headcount before Wall Street notices", icon: TrendUpIcon },
  { title: "Executive Moves", desc: "Track C-suite movements between public companies in real-time", icon: PeopleIcon },
  { title: "Growth / Price Gaps", desc: "Find stocks where fundamentals outpace the stock price", icon: GapIcon },
  { title: "Competitor Intel", desc: "See talent flowing between rivals — who's winning the war", icon: FlowIcon },
  { title: "Pre-Earnings Intel", desc: "Predict beats and misses using hiring + exec sentiment", icon: CalendarIcon },
  { title: "Sector Pulse", desc: "Heatmap of which industries are expanding or contracting", icon: GridIcon },
];

const TRENDING = ["NVDA", "PLTR", "META", "SNOW", "CRM", "TSLA"];

export default function LandingPage() {
  const [ticker, setTicker] = useState("");
  const router = useRouter();

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const val = ticker.trim().toUpperCase();
    if (val) router.push(`/company/${val}`);
  }

  return (
    <div className="flex min-h-full flex-col">
      {/* Hero */}
      <section className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-(--color-accent)/20 bg-(--color-accent-subtle) px-4 py-1.5 text-xs font-medium text-(--color-accent)">
          <span className="pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-(--color-accent)" />
          Scanning 80M+ companies in real-time
        </div>

        <h1 className="mb-4 max-w-2xl text-4xl font-bold leading-tight tracking-tight md:text-5xl">
          See what{" "}
          <span className="text-(--color-accent)">hedge funds</span>{" "}
          see — before the move
        </h1>

        <p className="mb-8 max-w-lg text-base text-(--color-text-secondary) md:text-lg">
          Real-time hiring surges, executive movements, and competitive intelligence.
          The alternative data edge, democratized.
        </p>

        {/* Search */}
        <form onSubmit={handleSearch} className="mb-6 flex w-full max-w-md gap-2">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter any ticker (e.g. NVDA)"
            className="flex-1 rounded-xl border border-(--color-border) bg-(--color-bg-card) px-5 py-3 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none transition-all focus:border-(--color-accent) focus:ring-2 focus:ring-(--color-accent)/20 card-shadow"
            maxLength={10}
          />
          <button
            type="submit"
            disabled={!ticker.trim()}
            className="rounded-xl bg-(--color-accent) px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-(--color-accent-hover) disabled:opacity-40"
          >
            Analyze
          </button>
        </form>

        {/* Trending tickers */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          <span className="text-xs text-(--color-text-muted)">Trending:</span>
          {TRENDING.map((t) => (
            <Link
              key={t}
              href={`/company/${t}`}
              className="rounded-lg border border-(--color-border) bg-(--color-bg-card) px-3 py-1 text-xs font-medium text-(--color-text-secondary) transition-colors hover:border-(--color-accent)/40 hover:text-(--color-accent)"
            >
              {t}
            </Link>
          ))}
        </div>
      </section>

      {/* Feature grid */}
      <section className="border-t border-(--color-border) bg-(--color-bg-secondary) px-6 py-12">
        <div className="mx-auto max-w-4xl">
          <h2 className="mb-2 text-center text-lg font-semibold">
            Intelligence that was <span className="text-(--color-accent)">$100K/year</span>. Now free.
          </h2>
          <p className="mb-8 text-center text-sm text-(--color-text-muted)">
            Every signal hedge funds use to front-run earnings, spot sector rotations, and track talent wars.
          </p>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 transition-colors hover:border-(--color-accent)/30 card-shadow"
              >
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-(--color-accent)/10">
                  <f.icon className="h-4.5 w-4.5 text-(--color-accent)" />
                </div>
                <div className="mb-1 text-sm font-semibold text-(--color-text-primary)">{f.title}</div>
                <div className="text-xs leading-relaxed text-(--color-text-muted)">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="flex items-center justify-center gap-4 border-t border-(--color-border) px-6 py-8">
        <Link
          href="/radar"
          className="rounded-xl bg-(--color-accent) px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-(--color-accent-hover)"
        >
          Open Live Radar
        </Link>
        <Link
          href="/chat"
          className="rounded-xl border border-(--color-border) px-6 py-2.5 text-sm font-medium text-(--color-text-secondary) transition hover:border-(--color-accent)/40 hover:text-(--color-accent)"
        >
          Ask AI anything
        </Link>
      </section>
    </div>
  );
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function TrendUpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
    </svg>
  );
}
function PeopleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}
function GapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5 7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
    </svg>
  );
}
function FlowIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  );
}
function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
    </svg>
  );
}
function GridIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
    </svg>
  );
}
