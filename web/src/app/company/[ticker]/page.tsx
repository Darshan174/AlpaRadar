"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { SignalCard } from "@/components/signal-card";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { HeadcountChart } from "@/components/headcount-chart";
import { ExecRoster } from "@/components/exec-roster";
import { TalentFlow } from "@/components/talent-flow";
import { PreEarningsCard } from "@/components/pre-earnings-card";
import { analyzeTicker } from "@/lib/api";
import type { Insight, Sentiment } from "@/lib/types";

type Tab = "overview" | "executives" | "competitors" | "earnings";

export default function CompanyDNAPage() {
  const params = useParams();
  const ticker = (params.ticker as string)?.toUpperCase() || "";
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    analyzeTicker(ticker)
      .then(setInsight)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-(--color-text-muted)">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
        <p className="text-sm">Analyzing {ticker}...</p>
        <p className="text-xs">Fetching market data + Crustdata intelligence</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6">
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-6 text-center text-sm text-(--color-bearish)">
          <p className="font-medium">Could not analyze {ticker}</p>
          <p className="mt-1 text-xs text-(--color-text-muted)">{error}</p>
        </div>
        <Link href="/" className="text-sm text-(--color-accent) hover:underline">Back to home</Link>
      </div>
    );
  }

  if (!insight) return null;

  return (
    <div className="flex h-full flex-col">
      {/* Header bar */}
      <div className="border-b border-(--color-border) px-6 py-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="mr-auto">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{insight.ticker}</h1>
              <SentimentBadge sentiment={insight.sentiment as Sentiment} />
            </div>
            <p className="text-sm text-(--color-text-muted)">{insight.company_name}</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-[10px] text-(--color-text-muted) uppercase">Score</div>
              <ScoreBadge score={insight.composite_score} size="lg" />
            </div>
            <div className="text-center">
              <div className="text-[10px] text-(--color-text-muted) uppercase">Signals</div>
              <div className="text-xl font-bold text-(--color-accent)">{insight.signal_count}</div>
            </div>
            <Link
              href={`/compare?a=${ticker}`}
              className="rounded-lg border border-(--color-border) px-3 py-1.5 text-xs font-medium text-(--color-text-secondary) hover:border-(--color-accent)/40 hover:text-(--color-accent)"
            >
              Compare
            </Link>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-4 flex gap-1">
          {(["overview", "executives", "competitors", "earnings"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                tab === t
                  ? "bg-(--color-accent)/15 text-(--color-accent)"
                  : "text-(--color-text-muted) hover:text-(--color-text-primary)"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-6">
        {tab === "overview" && <OverviewTab insight={insight} />}
        {tab === "executives" && <ExecutivesTab insight={insight} />}
        {tab === "competitors" && <CompetitorsTab insight={insight} />}
        {tab === "earnings" && <EarningsTab insight={insight} />}
      </div>
    </div>
  );
}

// ── Overview Tab ──────────────────────────────────────────────────────────────

function OverviewTab({ insight }: { insight: Insight }) {
  // Mock headcount data derived from signals
  const hcData = [
    { label: "Q1 '25", value: 4200 },
    { label: "Q2 '25", value: 4450 },
    { label: "Q3 '25", value: 4800 },
    { label: "Q4 '25", value: 5100 },
    { label: "Q1 '26", value: 5600 },
  ];

  return (
    <div className="space-y-6">
      {/* Two-column on desktop */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: chart + analysis */}
        <div className="space-y-6 lg:col-span-3">
          {/* Headcount chart */}
          <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
            <h3 className="mb-4 text-sm font-semibold text-(--color-text-secondary)">Headcount Trend</h3>
            <HeadcountChart data={hcData} height={180} />
          </section>

          {/* LLM Analysis */}
          {insight.llm_analysis && (
            <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
              <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">AI Analysis</h3>
              <div className="whitespace-pre-wrap text-sm leading-relaxed text-(--color-text-primary)">
                {insight.llm_analysis}
              </div>
            </section>
          )}
        </div>

        {/* Right: signal feed */}
        <div className="space-y-3 lg:col-span-2">
          <h3 className="text-sm font-semibold text-(--color-text-secondary)">
            Active Signals ({insight.signal_count})
          </h3>
          {insight.signals.length === 0 ? (
            <div className="rounded-xl border border-dashed border-(--color-border) p-6 text-center text-xs text-(--color-text-muted)">
              No signals detected. Company may lack Crustdata coverage.
            </div>
          ) : (
            insight.signals.map((s) => <SignalCard key={s.id} signal={s} />)
          )}
        </div>
      </div>
    </div>
  );
}

// ── Executives Tab ────────────────────────────────────────────────────────────

function ExecutivesTab({ insight }: { insight: Insight }) {
  const mockExecs = [
    { name: "Jensen Huang", title: "CEO", from_company: undefined, is_new: false },
    { name: "Colette Kress", title: "CFO", from_company: undefined, is_new: false },
    { name: "Devi Shankar", title: "VP of AI Platforms", from_company: "Google", is_new: true },
    { name: "Michael Chen", title: "CTO", from_company: "Meta", is_new: true },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">Executive Roster</h3>
          <ExecRoster executives={mockExecs} />
        </section>

        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">Executive Signals</h3>
          {insight.signals.filter((s) => s.type === "executive_move").length === 0 ? (
            <div className="rounded-xl border border-dashed border-(--color-border) p-6 text-center text-xs text-(--color-text-muted)">
              No executive movement signals detected
            </div>
          ) : (
            <div className="space-y-3">
              {insight.signals
                .filter((s) => s.type === "executive_move")
                .map((s) => <SignalCard key={s.id} signal={s} />)}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// ── Competitors Tab ───────────────────────────────────────────────────────────

function CompetitorsTab({ insight }: { insight: Insight }) {
  const mockFlows = [
    { from: "AMD", to: insight.ticker, count: 23 },
    { from: "Intel", to: insight.ticker, count: 18 },
    { from: insight.ticker, to: "OpenAI", count: 8 },
    { from: "Google", to: insight.ticker, count: 15 },
    { from: insight.ticker, to: "Meta", count: 5 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">Talent Flow</h3>
          <p className="mb-3 text-xs text-(--color-text-muted)">
            Where employees are moving to/from. Green = inbound (bullish), red = outbound.
          </p>
          <TalentFlow flows={mockFlows} focusTicker={insight.ticker} />
        </section>

        <section>
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">Competitor Signals</h3>
          {insight.signals.filter((s) => s.type === "competitor_shift").length === 0 ? (
            <div className="rounded-xl border border-dashed border-(--color-border) p-6 text-center text-xs text-(--color-text-muted)">
              No competitor shift signals detected
            </div>
          ) : (
            <div className="space-y-3">
              {insight.signals
                .filter((s) => s.type === "competitor_shift")
                .map((s) => <SignalCard key={s.id} signal={s} />)}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// ── Earnings Tab ──────────────────────────────────────────────────────────────

function EarningsTab({ insight }: { insight: Insight }) {
  const hiringSignal = insight.signals.find((s) => s.type === "hiring_surge");
  const hiringPct = hiringSignal?.data?.headcount_change_pct as number | undefined;

  return (
    <div className="max-w-xl space-y-6">
      <PreEarningsCard
        ticker={insight.ticker}
        beat_probability={insight.composite_score / 100}
        hiring_trend_pct={hiringPct ?? null as any}
        exec_sentiment={(insight.sentiment as Sentiment) || "neutral"}
        technical_setup={insight.composite_score >= 60 ? "bullish" : insight.composite_score >= 40 ? "neutral" : "bearish"}
        signals_count={insight.signal_count}
      />

      {insight.llm_analysis && (
        <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
          <h3 className="mb-3 text-sm font-semibold text-(--color-text-secondary)">Earnings Thesis</h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-(--color-text-primary)">
            {insight.llm_analysis}
          </div>
        </section>
      )}
    </div>
  );
}
