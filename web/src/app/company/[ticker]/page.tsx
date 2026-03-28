"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { SignalCard } from "@/components/signal-card";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { ExecRoster } from "@/components/exec-roster";
import { EvidenceCard } from "@/components/evidence-card";
import { getCompanyDetail } from "@/lib/api";
import {
  collectEvidence,
  extractDataHighlights,
  extractExecutiveMentions,
  extractReferencedCompanies,
  getAverageScore,
  getEvidenceSources,
  getSentimentBalance,
  getSignalMix,
  getTopSignals,
} from "@/lib/presentation";
import type { Brief, CompanyDetail, CompanyInfo, Signal, TradeSetup } from "@/lib/types";
import { ACTION_LABELS, ACTION_COLORS, HORIZON_LABELS, CONVICTION_COLORS } from "@/lib/types";

type Tab = "overview" | "executives" | "competitors" | "earnings";

export default function CompanyDNAPage() {
  const params = useParams();
  const ticker = (params.ticker as string)?.toUpperCase() || "";
  const [data, setData] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");

  useEffect(() => {
    if (!ticker) return;
    let cancelled = false;

    async function loadCompany() {
      setLoading(true);
      setError(null);

      try {
        const result = await getCompanyDetail(ticker);
        if (!cancelled) setData(result);
      } catch (issue) {
        if (!cancelled) setError(issue instanceof Error ? issue.message : "Unable to load company intelligence");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadCompany();
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (loading) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-[1600px] items-center justify-center p-6">
        <div className="flex items-center gap-3 text-sm text-(--color-text-muted)">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
          Loading company intelligence for {ticker}...
        </div>
      </div>
    );
  }

  if (error || !data?.company) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-[1600px] items-center justify-center p-6">
        <div className="rounded-[28px] border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-8 text-center text-sm text-(--color-bearish)">
          <div className="text-lg font-semibold">Could not load {ticker}</div>
          <p className="mt-2 text-(--color-text-secondary)">{error || "Unknown error"}</p>
          <Link href="/" className="mt-5 inline-flex rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary)">
            Return to landing page
          </Link>
        </div>
      </div>
    );
  }

  const { company, signals, briefs, suggested_action } = data;
  const sentiment = getSentimentBalance(signals);
  const avgScore = getAverageScore(signals);
  const executives = extractExecutiveMentions(signals);
  const evidence = collectEvidence(signals);
  const signalMix = getSignalMix(signals);
  const topSignals = getTopSignals(signals, 4);
  const evidenceSources = getEvidenceSources(evidence);
  const referencedCompanies = extractReferencedCompanies(signals);

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-3xl">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-(--color-text-muted)">
                Company DNA
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-4">
                <h1 className="metric-value text-6xl text-(--color-text-primary)">{company.ticker}</h1>
                <SentimentBadge sentiment={sentiment.bias} />
                <ScoreBadge score={avgScore} size="lg" />
              </div>
              <p className="mt-3 text-xl text-(--color-text-secondary)">{company.name}</p>
              <p className="mt-2 text-sm leading-7 text-(--color-text-muted)">
                {company.sector} · {company.industry}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                href={`/compare?a=${ticker}`}
                className="rounded-full border border-(--color-border) px-5 py-3 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
              >
                Compare ticker
              </Link>
              <Link
                href="/radar"
                className="rounded-full bg-linear-to-r from-orange-500 to-amber-500 px-5 py-3 text-sm font-semibold text-white transition hover:translate-y-[-1px]"
              >
                Back to radar
              </Link>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Average signal score" value={avgScore} />
            <MetricCard label="Total active signals" value={signals.length} />
            <MetricCard label="Net sentiment" value={sentiment.net > 0 ? `+${sentiment.net}` : sentiment.net} />
            <MetricCard label="Evidence sources" value={evidenceSources.length} />
          </div>

          <div className="mt-8 flex flex-wrap gap-2">
            {(["overview", "executives", "competitors", "earnings"] as Tab[]).map((item) => (
              <button
                key={item}
                onClick={() => setTab(item)}
                className={`rounded-full px-4 py-2 text-sm font-semibold capitalize transition ${
                  tab === item
                    ? "bg-linear-to-r from-orange-500 to-amber-500 text-white"
                    : "border border-(--color-border) text-(--color-text-secondary) hover:border-(--color-border-strong) hover:text-(--color-text-primary)"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
        </section>

        {tab === "overview" ? (
          <OverviewTab
            company={company}
            signals={signals}
            briefs={briefs}
            evidence={evidence}
            signalMix={signalMix}
            topSignals={topSignals}
            suggestedAction={suggested_action || undefined}
          />
        ) : null}

        {tab === "executives" ? (
          <ExecutivesTab signals={signals} executives={executives} sentimentBias={sentiment.bias} />
        ) : null}

        {tab === "competitors" ? (
          <CompetitorsTab signals={signals} referencedCompanies={referencedCompanies} />
        ) : null}

        {tab === "earnings" ? (
          <EarningsTab signals={signals} avgScore={avgScore} sentiment={sentiment.bias} latestBrief={briefs[0] || null} />
        ) : null}
      </div>
    </div>
  );
}

function OverviewTab({
  company,
  signals,
  briefs,
  evidence,
  signalMix,
  topSignals,
  suggestedAction,
}: {
  company: CompanyInfo;
  signals: Signal[];
  briefs: Brief[];
  evidence: ReturnType<typeof collectEvidence>;
  signalMix: ReturnType<typeof getSignalMix>;
  topSignals: Signal[];
  suggestedAction?: TradeSetup;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        {suggestedAction ? <TradeSetupCard setup={suggestedAction} /> : null}

        <Panel title="Signal overview">
          <div className="grid gap-3 md:grid-cols-2">
            {topSignals.length ? (
              topSignals.map((signal) => (
                <Link key={signal.id} href={`/signal/${signal.id}`} className="block rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4 transition hover:border-(--color-border-strong)">
                  <div className="text-xs uppercase tracking-[0.18em] text-(--color-accent)">
                    {signal.type.replace(/_/g, " ")}
                  </div>
                  <div className="mt-2 text-sm font-semibold text-(--color-text-primary)">{signal.headline}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {signal.historical_win_rate != null ? (
                      <span className="data-chip border-(--color-bullish)/30 bg-(--color-bullish)/8">
                        <span className="text-(--color-text-muted)">Historical edge</span>
                        <span className="text-(--color-bullish)">
                          {(signal.historical_win_rate * 100).toFixed(0)}%
                          {signal.historical_avg_return != null ? ` / +${signal.historical_avg_return}%` : ""}
                        </span>
                      </span>
                    ) : null}
                    {extractDataHighlights(signal.data, 2).map((item) => (
                      <span key={`${signal.id}-${item.label}`} className="data-chip">
                        <span className="text-(--color-text-muted)">{item.label}</span>
                        <span>{item.value}</span>
                      </span>
                    ))}
                  </div>
                </Link>
              ))
            ) : (
              <div className="text-sm text-(--color-text-muted)">No active signals are available for this company.</div>
            )}
          </div>
        </Panel>

        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Latest AI brief">
            {briefs[0] ? (
              <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
                <p>{briefs[0].sections.what_happened}</p>
                <p>{briefs[0].sections.why_it_matters}</p>
              </div>
            ) : (
              <div className="text-sm text-(--color-text-muted)">
                No generated brief is stored for {company.ticker} yet.
              </div>
            )}
          </Panel>

          <Panel title="Current dataset scope">
            <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
              <p>This company view only shows current signals, briefs, and evidence returned by the API.</p>
              <p>Unsupported panels such as synthetic headcount charts and invented talent flow have been removed.</p>
            </div>
          </Panel>
        </div>

        <Panel title={`Evidence stream (${evidence.length})`}>
          {evidence.length ? (
            <div className="space-y-3">
              {evidence.slice(0, 6).map((item, index) => (
                <EvidenceCard key={`${item.title}-${index}`} evidence={item} />
              ))}
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">No source evidence attached yet.</div>
          )}
        </Panel>
      </div>

      <div className="space-y-6">
        <Panel title="Signal mix">
          <div className="space-y-3">
            {signalMix.length ? (
              signalMix.map((bucket) => (
                <div key={bucket.type} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-(--color-text-primary)">{bucket.label}</div>
                      <div className="mt-1 text-xs text-(--color-text-muted)">{bucket.count} signals</div>
                    </div>
                    <div className="metric-value text-2xl text-(--color-text-primary)">{bucket.avgScore}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-(--color-text-muted)">No signal mix detected yet.</div>
            )}
          </div>
        </Panel>

        <Panel title={`Active signals (${signals.length})`}>
          {signals.length ? (
            <div className="space-y-4">
              {signals.map((signal) => (
                <Link key={signal.id} href={`/signal/${signal.id}`} className="block">
                  <SignalCard signal={signal} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">No live signals for this company.</div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function ExecutivesTab({
  signals,
  executives,
  sentimentBias,
}: {
  signals: Signal[];
  executives: ReturnType<typeof extractExecutiveMentions>;
  sentimentBias: "bullish" | "bearish" | "neutral";
}) {
  const executiveSignals = signals.filter((signal) => signal.type === "executive_move");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Exec signals" value={executiveSignals.length} />
        <MetricCard label="Named executives" value={executives.length} />
        <MetricCard label="Leadership tone" value={sentimentBias} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Panel title="Executive roster">
          {executives.length ? (
            <ExecRoster executives={executives} />
          ) : (
            <div className="text-sm text-(--color-text-muted)">No executive names or titles are present in the current signal set.</div>
          )}
        </Panel>

        <div className="space-y-6">
          <Panel title="Leadership read-through">
            <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
              <p>This tab now surfaces only executive context explicitly named in the current company signals.</p>
              <p>If the API has no executive names or titles for this company, the section remains empty rather than fabricating a roster.</p>
            </div>
          </Panel>

          <Panel title={`Executive signals (${executiveSignals.length})`}>
            {executiveSignals.length ? (
              <div className="space-y-4">
                {executiveSignals.map((signal) => (
                  <Link key={signal.id} href={`/signal/${signal.id}`} className="block">
                    <SignalCard signal={signal} />
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-sm text-(--color-text-muted)">No executive movement signals are active.</div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

function CompetitorsTab({
  signals,
  referencedCompanies,
}: {
  signals: Signal[];
  referencedCompanies: string[];
}) {
  const competitorSignals = signals.filter((signal) => signal.type === "competitor_shift");
  const sectorSignals = signals.filter((signal) => signal.type === "sector_pulse");
  const hiringSignals = signals.filter((signal) => signal.type === "hiring_surge");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Competitor signals" value={competitorSignals.length} />
        <MetricCard label="Sector signals" value={sectorSignals.length} />
        <MetricCard label="Hiring signals" value={hiringSignals.length} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Panel title="Referenced companies in current signals">
          {referencedCompanies.length ? (
            <div className="flex flex-wrap gap-2">
              {referencedCompanies.map((item) => (
                <span key={item} className="data-chip">{item}</span>
              ))}
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">
              The current company dataset does not name competitor companies directly.
            </div>
          )}
        </Panel>

        <Panel title="Context">
          <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
            <p>This tab only shows competitor or sector context that is explicitly present in the current company data.</p>
            <p>If no competitor-shift data exists for this company, AlphaRadar now leaves the section empty rather than inferring talent flow or rival movement.</p>
          </div>
        </Panel>
      </div>

      <Panel title={`Competitor-related signals (${competitorSignals.length + sectorSignals.length})`}>
        {competitorSignals.length || sectorSignals.length ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {[...competitorSignals, ...sectorSignals].map((signal) => (
              <Link key={signal.id} href={`/signal/${signal.id}`} className="block">
                <SignalCard signal={signal} />
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-sm text-(--color-text-muted)">No competitor or sector context signals are available for this company.</div>
        )}
      </Panel>
    </div>
  );
}

function EarningsTab({
  signals,
  avgScore,
  sentiment,
  latestBrief,
}: {
  signals: Signal[];
  avgScore: number;
  sentiment: "bullish" | "bearish" | "neutral";
  latestBrief: Brief | null;
}) {
  const relevantSignals = signals.filter((signal) => ["hiring_surge", "growth_price_divergence", "executive_move"].includes(signal.type));
  const earningsMetrics = relevantSignals.flatMap((signal) =>
    extractDataHighlights(signal.data, 3).map((item) => ({
      signalId: signal.id,
      type: signal.type,
      ...item,
    })),
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        <Panel title="Available earnings context">
          <div className="grid gap-3 md:grid-cols-2">
            <MetricCard label="Average signal score" value={avgScore} />
            <MetricCard label="Signal sentiment" value={sentiment} />
          </div>
          <p className="mt-4 text-sm leading-7 text-(--color-text-secondary)">
            This section only surfaces signal data that exists for the current company. Beat probabilities and inferred earnings forecasts are intentionally not generated in the UI.
          </p>
        </Panel>

        <Panel title="Catalyst stack">
          {relevantSignals.length ? (
            <div className="grid gap-3 md:grid-cols-2">
              {relevantSignals.map((signal) => (
                <Link key={signal.id} href={`/signal/${signal.id}`} className="block rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4 transition hover:border-(--color-border-strong)">
                  <div className="text-xs uppercase tracking-[0.18em] text-(--color-accent)">
                    {signal.type.replace(/_/g, " ")}
                  </div>
                  <div className="mt-2 text-sm font-semibold text-(--color-text-primary)">{signal.headline}</div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">No earnings-relevant signals are available in the current dataset.</div>
          )}
        </Panel>

        <Panel title="Structured metrics">
          {earningsMetrics.length ? (
            <div className="grid gap-3 md:grid-cols-2">
              {earningsMetrics.map((metric, index) => (
                <Link key={`${metric.signalId}-${metric.label}-${index}`} href={`/signal/${metric.signalId}`} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4 transition hover:border-(--color-border-strong)">
                  <div className="text-xs uppercase tracking-[0.18em] text-(--color-text-muted)">{metric.type.replace(/_/g, " ")}</div>
                  <div className="mt-2 text-sm font-semibold text-(--color-text-primary)">{metric.label}</div>
                  <div className="mt-1 text-lg text-(--color-text-secondary)">{metric.value}</div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">No structured metrics are available for current earnings-related signals.</div>
          )}
        </Panel>
      </div>

      <div className="space-y-6">
        <Panel title="Briefing context">
          {latestBrief ? (
            <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
              <p>{latestBrief.sections.why_it_matters}</p>
              <p>{latestBrief.sections.risks}</p>
            </div>
          ) : (
            <div className="text-sm text-(--color-text-muted)">
              No stored earnings framing is available yet.
            </div>
          )}
        </Panel>

        <Panel title="Checklist">
          <div className="space-y-3 text-sm text-(--color-text-secondary)">
            {[
              "Review whether hiring metrics in the current signals support an operating acceleration story.",
              "Confirm whether executive changes reinforce or weaken the current thesis.",
              "Check if evidence breadth is wide enough to trust the signal cluster.",
            ].map((item) => (
              <div key={item} className="flex items-start gap-3 rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                <span className="mt-1 h-2 w-2 rounded-full bg-(--color-accent)" />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function TradeSetupCard({ setup }: { setup: TradeSetup }) {
  const actionLabel = ACTION_LABELS[setup.action] || setup.action;
  const actionColor = ACTION_COLORS[setup.action] || "text-(--color-text-primary)";
  const horizonLabel = HORIZON_LABELS[setup.time_horizon] || setup.time_horizon;
  const convictionColor = CONVICTION_COLORS[setup.conviction] || "text-(--color-text-muted)";

  const isBullish = ["accumulate"].includes(setup.action);
  const isBearish = ["short_candidate", "reduce", "take_profit"].includes(setup.action);

  const borderColor = isBullish
    ? "border-(--color-bullish)/30"
    : isBearish
      ? "border-(--color-bearish)/30"
      : "border-(--color-border)";

  const bgTint = isBullish
    ? "bg-(--color-bullish)/6"
    : isBearish
      ? "bg-(--color-bearish)/6"
      : "";

  return (
    <section className={`surface-panel rounded-[30px] p-5 lg:p-6 ${borderColor} ${bgTint}`}>
      <div className="min-w-0 flex-1">
        <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
          Suggested Action
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className={`metric-value text-3xl ${actionColor}`}>{actionLabel}</span>
          <span className={`data-chip ${convictionColor}`}>
            {setup.conviction.toUpperCase()} conviction
          </span>
          <span className="data-chip">{horizonLabel}</span>
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-(--color-text-secondary)">
          {setup.rationale}
        </p>
      </div>

      {setup.risk_note ? (
        <div className="mt-4 rounded-[18px] border border-(--color-border) bg-(--color-bg-secondary)/60 px-4 py-3">
          <div className="flex items-start gap-2 text-sm text-(--color-text-secondary)">
            <span className="mt-0.5 text-(--color-neutral)">⚠</span>
            <span>{setup.risk_note}</span>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="surface-panel rounded-[28px] p-5">
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
        {label}
      </div>
      <div className="mt-4 metric-value text-4xl text-(--color-text-primary)">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="surface-panel rounded-[30px] p-5 lg:p-6">
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
        {title}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}
