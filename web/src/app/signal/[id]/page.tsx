"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getSignalDetail } from "@/lib/api";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { BriefSection } from "@/components/brief-section";
import { EvidenceCard } from "@/components/evidence-card";
import { extractDataHighlights, formatRelativeTime } from "@/lib/presentation";
import type { SignalDetail } from "@/lib/types";
import { SIGNAL_LABELS, SIGNAL_COLORS } from "@/lib/types";

export default function SignalDetailPage() {
  const params = useParams();
  const signalId = params.id as string;
  const [data, setData] = useState<SignalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!signalId) return;
    let cancelled = false;

    async function loadSignal() {
      setLoading(true);
      setError(null);

      try {
        const result = await getSignalDetail(signalId);
        if (!cancelled) setData(result);
      } catch (issue) {
        if (!cancelled) setError(issue instanceof Error ? issue.message : "Unable to load this signal");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadSignal();
    return () => {
      cancelled = true;
    };
  }, [signalId]);

  if (loading) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-[1600px] items-center justify-center p-6">
        <div className="flex items-center gap-3 text-sm text-(--color-text-muted)">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
          Loading signal detail...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-[1600px] items-center justify-center p-6">
        <div className="rounded-[28px] border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-8 text-center text-sm text-(--color-bearish)">
          <div className="text-lg font-semibold">Signal not found</div>
          <p className="mt-2 text-(--color-text-secondary)">{error || "Unknown error"}</p>
          <Link href="/radar" className="mt-5 inline-flex rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary)">
            Return to radar
          </Link>
        </div>
      </div>
    );
  }

  const { signal, brief, company } = data;
  const typeColor = SIGNAL_COLORS[signal.type] || "text-(--color-text-secondary)";
  const highlights = extractDataHighlights(signal.data, 8);

  return (
    <div className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
      <div className="space-y-6">
        <section className="surface-panel rounded-[34px] p-6 lg:p-8">
          <div className="flex flex-wrap items-center gap-2 text-[0.72rem] uppercase tracking-[0.18em] text-(--color-text-muted)">
            <Link href="/radar" className="hover:text-(--color-text-primary)">Radar</Link>
            <span>/</span>
            <Link href={`/company/${signal.ticker}`} className="hover:text-(--color-text-primary)">{signal.ticker}</Link>
            <span>/</span>
            <span>Signal Detail</span>
          </div>

          <div className="mt-5 flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-4xl">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border border-current/20 bg-white/5 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.22em] ${typeColor}`}>
                  {SIGNAL_LABELS[signal.type]}
                </span>
                <StrengthPill strength={signal.strength} />
                <SentimentBadge sentiment={signal.sentiment} />
              </div>

              <h1 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
                {signal.headline}
              </h1>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-(--color-text-secondary)">
                <Link href={`/company/${signal.ticker}`} className="font-semibold text-(--color-text-primary)">
                  {signal.ticker}
                </Link>
                {company ? <span>{company.name}</span> : null}
                <span>{formatRelativeTime(signal.detected_at)}</span>
              </div>
            </div>

            <ScoreBadge score={signal.score} size="lg" />
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3 xl:grid-cols-4">
            <MetricCard label="Signal score" value={signal.score} />
            <MetricCard label="Strength" value={signal.strength} />
            <MetricCard label="Evidence count" value={signal.evidence?.length || 0} />
            <MetricCard label="Company" value={signal.ticker} />
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <Panel title="Signal detail">
              <p className="text-sm leading-8 text-(--color-text-secondary)">{signal.detail}</p>
            </Panel>

            {signal.evidence?.length ? (
              <Panel title={`Source evidence (${signal.evidence.length})`}>
                <div className="space-y-3">
                  {signal.evidence.map((item, index) => (
                    <EvidenceCard key={`${item.title}-${index}`} evidence={item} />
                  ))}
                </div>
              </Panel>
            ) : null}

            {brief ? (
              <Panel title="AI intelligence brief">
                <BriefSection brief={brief} />
              </Panel>
            ) : null}
          </div>

          <div className="space-y-6">
            <Panel title="Signal anatomy">
              <div className="space-y-3">
                {highlights.length ? (
                  highlights.map((item) => (
                    <div key={item.label} className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                      <div className="text-xs uppercase tracking-[0.18em] text-(--color-text-muted)">{item.label}</div>
                      <div className="mt-2 text-lg font-semibold text-(--color-text-primary)">{item.value}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-(--color-text-muted)">No structured signal data was attached.</div>
                )}
              </div>
            </Panel>

            <Panel title="Decision framing">
              <div className="space-y-3 text-sm leading-7 text-(--color-text-secondary)">
                <p>Use the score and strength to judge urgency, but confirm with evidence breadth before acting.</p>
                <p>Read this signal alongside company-level tabs to understand whether it is isolated or part of a broader pattern.</p>
                <p>When the signal carries supporting evidence plus a generated brief, it is usually worth escalation.</p>
              </div>
            </Panel>

            <Panel title="Compliance note">
              <p className="text-sm leading-7 text-(--color-text-secondary)">
                AlphaRadar provides alternative-data signals for informational purposes only. This is not financial advice and should be treated as research input rather than a recommendation.
              </p>
            </Panel>
          </div>
        </div>
      </div>
    </div>
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

function StrengthPill({ strength }: { strength: string }) {
  const colors: Record<string, string> = {
    strong: "border-(--color-strong)/25 bg-(--color-strong)/12 text-(--color-strong)",
    moderate: "border-(--color-accent)/25 bg-(--color-accent)/12 text-(--color-accent)",
    weak: "border-(--color-border-strong) bg-(--color-bg-hover)/55 text-(--color-text-muted)",
  };

  return (
    <span className={`rounded-full border px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.2em] ${colors[strength] || colors.weak}`}>
      {strength}
    </span>
  );
}
