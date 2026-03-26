"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { analyzeTicker } from "@/lib/api";
import { collectEvidence, getSentimentBalance, getSignalMix } from "@/lib/presentation";
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
  const [tickerA, setTickerA] = useState(searchParams.get("a")?.toUpperCase() || "");
  const [tickerB, setTickerB] = useState("");
  const [insightA, setInsightA] = useState<Insight | null>(null);
  const [insightB, setInsightB] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare(event: React.FormEvent) {
    event.preventDefault();
    const a = tickerA.trim().toUpperCase();
    const b = tickerB.trim().toUpperCase();
    if (!a || !b) return;

    setLoading(true);
    setError(null);

    try {
      const [left, right] = await Promise.all([analyzeTicker(a), analyzeTicker(b)]);
      setInsightA(left);
      setInsightB(right);
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Unable to compare the selected companies");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="kicker">Competitive Intelligence</div>
          <h1 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
            Compare two companies without inventing anything the API did not return.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-8 text-(--color-text-secondary)">
            This view compares current scores, sentiment, summaries, evidence coverage, and signal mix. Synthetic trend overlays and invented talent flow have been removed.
          </p>

          <form onSubmit={handleCompare} className="mt-8 grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto] lg:items-end">
            <div>
              <label className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Company A
              </label>
              <input
                type="text"
                value={tickerA}
                onChange={(event) => setTickerA(event.target.value.toUpperCase())}
                placeholder="e.g. NVDA"
                maxLength={10}
                className="mt-2 w-full rounded-[22px] border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-4 text-lg text-(--color-text-primary) outline-none focus:border-(--color-accent)"
              />
            </div>

            <div className="pb-4 text-center text-sm font-semibold uppercase tracking-[0.24em] text-(--color-text-muted)">
              vs
            </div>

            <div>
              <label className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Company B
              </label>
              <input
                type="text"
                value={tickerB}
                onChange={(event) => setTickerB(event.target.value.toUpperCase())}
                placeholder="e.g. AMD"
                maxLength={10}
                className="mt-2 w-full rounded-[22px] border border-(--color-border) bg-(--color-bg-card-strong) px-4 py-4 text-lg text-(--color-text-primary) outline-none focus:border-(--color-accent)"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !tickerA.trim() || !tickerB.trim()}
              className="rounded-[22px] bg-linear-to-r from-orange-500 to-amber-500 px-6 py-4 text-sm font-semibold text-white transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? "Comparing..." : "Run comparison"}
            </button>
          </form>
        </section>

        {error ? (
          <div className="rounded-[26px] border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-6 text-sm text-(--color-bearish)">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="surface-panel flex min-h-[420px] items-center justify-center rounded-[32px]">
            <div className="flex items-center gap-3 text-sm text-(--color-text-muted)">
              <div className="h-7 w-7 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
              Comparing both companies across current API-backed signals...
            </div>
          </div>
        ) : insightA && insightB ? (
          <ComparisonView a={insightA} b={insightB} />
        ) : (
          <EmptyComparisonState />
        )}
      </div>
    </div>
  );
}

function EmptyComparisonState() {
  return (
    <section className="surface-panel rounded-[32px] p-6 lg:p-8">
      <div className="grid gap-4 lg:grid-cols-3">
        {[
          ["Momentum", "See which company is stacking more high-score signals right now."],
          ["Signal Mix", "Compare which signal families are actually present in each result set."],
          ["Research Speed", "Jump into detailed company pages once a winner or weak spot becomes obvious."],
        ].map(([title, description]) => (
          <div key={title} className="surface-panel-muted rounded-[26px] p-5">
            <div className="text-lg font-semibold text-(--color-text-primary)">{title}</div>
            <p className="mt-3 text-sm leading-7 text-(--color-text-secondary)">{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ComparisonView({ a, b }: { a: Insight; b: Insight }) {
  const mixA = getSignalMix(a.signals);
  const mixB = getSignalMix(b.signals);
  const balanceA = getSentimentBalance(a.signals);
  const balanceB = getSentimentBalance(b.signals);
  const evidenceA = collectEvidence(a.signals);
  const evidenceB = collectEvidence(b.signals);

  const scoreLeader = a.composite_score >= b.composite_score ? a.ticker : b.ticker;
  const signalLeader = a.signal_count >= b.signal_count ? a.ticker : b.ticker;
  const toneLeader = balanceA.net >= balanceB.net ? a.ticker : b.ticker;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <CompanyHeader insight={a} />
        <CompanyHeader insight={b} />
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <ComparisonLeadCard label="Composite score leader" leader={scoreLeader} detail={`${a.composite_score} vs ${b.composite_score}`} />
        <ComparisonLeadCard label="Signal volume leader" leader={signalLeader} detail={`${a.signal_count} vs ${b.signal_count}`} />
        <ComparisonLeadCard label="Sentiment leader" leader={toneLeader} detail={`${balanceA.net > 0 ? "+" : ""}${balanceA.net} vs ${balanceB.net > 0 ? "+" : ""}${balanceB.net}`} />
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <section className="grid gap-6 lg:grid-cols-2">
            <SignalMixPanel title={`${a.ticker} signal mix`} items={mixA} />
            <SignalMixPanel title={`${b.ticker} signal mix`} items={mixB} />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <NarrativePanel insight={a} />
            <NarrativePanel insight={b} />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <SignalsPanel insight={a} />
            <SignalsPanel insight={b} />
          </section>
        </div>

        <div className="space-y-6">
          <Panel title="Evidence coverage">
            <EvidenceCoveragePanel label={a.ticker} evidenceCount={evidenceA.length} />
            <div className="mt-3" />
            <EvidenceCoveragePanel label={b.ticker} evidenceCount={evidenceB.length} />
          </Panel>
          <Panel title="Analyst takeaways">
            <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
              <p>
                <span className="font-semibold text-(--color-text-primary)">{scoreLeader}</span> is currently ahead on total composite momentum.
              </p>
              <p>
                <span className="font-semibold text-(--color-text-primary)">{signalLeader}</span> is generating more raw signal volume, which usually means more surface area for follow-up work.
              </p>
              <p>
                Sentiment balance favors <span className="font-semibold text-(--color-text-primary)">{toneLeader}</span>, but it still needs to be read against evidence quality and signal mix.
              </p>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function CompanyHeader({ insight }: { insight: Insight }) {
  return (
    <section className="surface-panel rounded-[32px] p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
            {insight.company_name}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Link href={`/company/${insight.ticker}`} className="metric-value text-5xl text-(--color-text-primary)">
              {insight.ticker}
            </Link>
            <SentimentBadge sentiment={insight.sentiment as Sentiment} />
          </div>
        </div>
        <ScoreBadge score={insight.composite_score} size="lg" />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
          <div className="text-xs text-(--color-text-muted)">Signals</div>
          <div className="mt-2 metric-value text-3xl text-(--color-text-primary)">{insight.signal_count}</div>
        </div>
        <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
          <div className="text-xs text-(--color-text-muted)">Summary</div>
          <div className="mt-2 text-sm leading-6 text-(--color-text-secondary)">{insight.summary}</div>
        </div>
      </div>
    </section>
  );
}

function ComparisonLeadCard({ label, leader, detail }: { label: string; leader: string; detail: string }) {
  return (
    <div className="surface-panel rounded-[28px] p-5">
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
        {label}
      </div>
      <div className="mt-4 metric-value text-4xl text-(--color-accent)">{leader}</div>
      <div className="mt-2 text-sm text-(--color-text-secondary)">{detail}</div>
    </div>
  );
}

function SignalMixPanel({
  title,
  items,
}: {
  title: string;
  items: { label: string; count: number; avgScore: number }[];
}) {
  return (
    <Panel title={title}>
      <div className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.label} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-semibold text-(--color-text-primary)">{item.label}</div>
                  <div className="mt-1 text-xs text-(--color-text-muted)">{item.count} signals</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-(--color-text-muted)">Avg score</div>
                  <div className="metric-value text-2xl text-(--color-text-primary)">{item.avgScore}</div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-sm text-(--color-text-muted)">No signal mix available.</div>
        )}
      </div>
    </Panel>
  );
}

function NarrativePanel({ insight }: { insight: Insight }) {
  return (
    <Panel title={`${insight.ticker} narrative`}>
      <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
        <p>{insight.summary}</p>
        <p>{insight.llm_analysis}</p>
      </div>
    </Panel>
  );
}

function EvidenceCoveragePanel({ label, evidenceCount }: { label: string; evidenceCount: number }) {
  return (
    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-(--color-text-muted)">{label}</div>
      <div className="mt-2 metric-value text-3xl text-(--color-text-primary)">{evidenceCount}</div>
      <div className="mt-1 text-sm text-(--color-text-secondary)">evidence items attached to current signals</div>
    </div>
  );
}

function SignalsPanel({ insight }: { insight: Insight }) {
  return (
    <Panel title={`${insight.ticker} signal tape`}>
      <div className="space-y-3">
        {insight.signals.length ? (
          insight.signals.map((signal) => (
            <Link key={signal.id} href={`/signal/${signal.id}`} className="block rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4 transition hover:border-(--color-border-strong)">
              <div className="text-xs uppercase tracking-[0.18em] text-(--color-accent)">
                {signal.type.replace(/_/g, " ")}
              </div>
              <div className="mt-2 text-sm font-semibold text-(--color-text-primary)">{signal.headline}</div>
            </Link>
          ))
        ) : (
          <div className="text-sm text-(--color-text-muted)">No active signals.</div>
        )}
      </div>
    </Panel>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="surface-panel rounded-[30px] p-5">
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
        {title}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}
