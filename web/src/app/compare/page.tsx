"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { HeadcountChart } from "@/components/headcount-chart";
import { TalentFlow } from "@/components/talent-flow";
import { analyzeTicker } from "@/lib/api";
import type { Insight, Sentiment } from "@/lib/types";

export default function ComparePage() {
  return (
    <Suspense>
      <CompareContent />
    </Suspense>
  );
}

function CompareContent() {
  const searchParams = useSearchParams();
  const initialA = searchParams.get("a")?.toUpperCase() || "";

  const [tickerA, setTickerA] = useState(initialA);
  const [tickerB, setTickerB] = useState("");
  const [insightA, setInsightA] = useState<Insight | null>(null);
  const [insightB, setInsightB] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare(e: React.FormEvent) {
    e.preventDefault();
    const a = tickerA.trim().toUpperCase();
    const b = tickerB.trim().toUpperCase();
    if (!a || !b) return;

    setLoading(true);
    setError(null);
    try {
      const [resA, resB] = await Promise.all([analyzeTicker(a), analyzeTicker(b)]);
      setInsightA(resA);
      setInsightB(resB);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Compare</h1>
        <p className="text-sm text-(--color-text-muted)">
          Side-by-side alternative data comparison between two companies
        </p>
      </div>

      {/* Inputs */}
      <form onSubmit={handleCompare} className="mb-8 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs text-(--color-text-muted)">Company A</label>
          <input
            type="text"
            value={tickerA}
            onChange={(e) => setTickerA(e.target.value.toUpperCase())}
            placeholder="e.g. NVDA"
            className="w-28 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-3 py-2.5 text-sm font-medium text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
            maxLength={10}
          />
        </div>
        <span className="pb-2.5 text-sm font-bold text-(--color-text-muted)">vs</span>
        <div>
          <label className="mb-1 block text-xs text-(--color-text-muted)">Company B</label>
          <input
            type="text"
            value={tickerB}
            onChange={(e) => setTickerB(e.target.value.toUpperCase())}
            placeholder="e.g. AMD"
            className="w-28 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-3 py-2.5 text-sm font-medium text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none focus:border-(--color-accent)"
            maxLength={10}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !tickerA.trim() || !tickerB.trim()}
          className="rounded-lg bg-(--color-accent) px-5 py-2.5 text-sm font-medium text-white transition hover:bg-(--color-accent-hover) disabled:opacity-40"
        >
          {loading ? "Analyzing..." : "Compare"}
        </button>
      </form>

      {loading && (
        <div className="flex items-center justify-center gap-3 py-16 text-sm text-(--color-text-muted)">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
          Analyzing both companies...
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-4 text-sm text-(--color-bearish)">
          {error}
        </div>
      )}

      {insightA && insightB && (
        <ComparisonView a={insightA} b={insightB} />
      )}
    </div>
  );
}

function ComparisonView({ a, b }: { a: Insight; b: Insight }) {
  const mockFlows = [
    { from: a.ticker, to: b.ticker, count: 12 },
    { from: b.ticker, to: a.ticker, count: 7 },
  ];

  return (
    <div className="space-y-6">
      {/* Score comparison */}
      <div className="grid grid-cols-2 gap-4">
        <CompanyHeader insight={a} />
        <CompanyHeader insight={b} />
      </div>

      {/* Headcount charts side by side */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
          <h3 className="mb-3 text-xs font-semibold text-(--color-text-muted)">
            {a.ticker} Headcount
          </h3>
          <HeadcountChart
            data={[
              { label: "Q1", value: 4200 },
              { label: "Q2", value: 4450 },
              { label: "Q3", value: 4800 },
              { label: "Q4", value: 5100 },
              { label: "Now", value: 5600 },
            ]}
            height={140}
          />
        </section>
        <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
          <h3 className="mb-3 text-xs font-semibold text-(--color-text-muted)">
            {b.ticker} Headcount
          </h3>
          <HeadcountChart
            data={[
              { label: "Q1", value: 3100 },
              { label: "Q2", value: 3050 },
              { label: "Q3", value: 3200 },
              { label: "Q4", value: 3350 },
              { label: "Now", value: 3500 },
            ]}
            height={140}
          />
        </section>
      </div>

      {/* Talent flow between them */}
      <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
        <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">
          Talent Flow: {a.ticker} vs {b.ticker}
        </h3>
        <TalentFlow flows={mockFlows} focusTicker={a.ticker} />
      </section>

      {/* Signal comparison */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">
            {a.ticker} Signals ({a.signal_count})
          </h3>
          <div className="space-y-2">
            {a.signals.map((s) => (
              <div key={s.id} className="rounded-lg border border-(--color-border) bg-(--color-bg-card) p-3 text-xs card-shadow">
                <span className="font-medium text-(--color-accent)">[{s.type.replace(/_/g, " ")}]</span>{" "}
                <span className="text-(--color-text-primary)">{s.headline}</span>
              </div>
            ))}
            {a.signals.length === 0 && (
              <div className="text-xs text-(--color-text-muted)">No signals</div>
            )}
          </div>
        </section>
        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">
            {b.ticker} Signals ({b.signal_count})
          </h3>
          <div className="space-y-2">
            {b.signals.map((s) => (
              <div key={s.id} className="rounded-lg border border-(--color-border) bg-(--color-bg-card) p-3 text-xs card-shadow">
                <span className="font-medium text-(--color-accent)">[{s.type.replace(/_/g, " ")}]</span>{" "}
                <span className="text-(--color-text-primary)">{s.headline}</span>
              </div>
            ))}
            {b.signals.length === 0 && (
              <div className="text-xs text-(--color-text-muted)">No signals</div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

function CompanyHeader({ insight }: { insight: Insight }) {
  return (
    <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
      <div className="mb-2 flex items-center gap-3">
        <Link href={`/company/${insight.ticker}`} className="text-xl font-bold hover:text-(--color-accent)">
          {insight.ticker}
        </Link>
        <SentimentBadge sentiment={insight.sentiment as Sentiment} />
      </div>
      <div className="mb-3 text-xs text-(--color-text-muted)">{insight.company_name}</div>
      <div className="flex items-center gap-4">
        <div>
          <div className="text-[10px] text-(--color-text-muted)">Score</div>
          <ScoreBadge score={insight.composite_score} size="lg" />
        </div>
        <div>
          <div className="text-[10px] text-(--color-text-muted)">Signals</div>
          <div className="text-lg font-bold text-(--color-accent)">{insight.signal_count}</div>
        </div>
      </div>
    </div>
  );
}
