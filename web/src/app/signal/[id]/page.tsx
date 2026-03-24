"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getSignalDetail } from "@/lib/api";
import { ScoreBadge } from "@/components/score-badge";
import { SentimentBadge } from "@/components/sentiment-badge";
import { BriefSection } from "@/components/brief-section";
import { EvidenceCard } from "@/components/evidence-card";
import type { SignalDetail, Evidence } from "@/lib/types";
import { SIGNAL_LABELS, SIGNAL_COLORS } from "@/lib/types";

export default function SignalDetailPage() {
  const params = useParams();
  const signalId = params.id as string;
  const [data, setData] = useState<SignalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!signalId) return;
    setLoading(true);
    getSignalDetail(signalId)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [signalId]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-(--color-accent) border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6">
        <div className="rounded-lg border border-(--color-bearish)/30 bg-(--color-bearish)/10 p-6 text-center text-sm text-(--color-bearish)">
          <p className="font-medium">Signal not found</p>
          <p className="mt-1 text-xs text-(--color-text-muted)">{error || "Unknown error"}</p>
        </div>
        <Link href="/radar" className="text-sm text-(--color-accent) hover:underline">
          Back to Radar
        </Link>
      </div>
    );
  }

  const { signal, brief, company } = data;
  const typeColor = SIGNAL_COLORS[signal.type] || "text-(--color-text-secondary)";

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-(--color-border) px-6 py-4">
        <div className="mb-2 flex items-center gap-2 text-xs text-(--color-text-muted)">
          <Link href="/radar" className="hover:text-(--color-accent)">Radar</Link>
          <span>/</span>
          <Link href={`/company/${signal.ticker}`} className="hover:text-(--color-accent)">
            {signal.ticker}
          </Link>
          <span>/</span>
          <span className="text-(--color-text-secondary)">Signal</span>
        </div>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <span className={`text-xs font-bold uppercase tracking-wider ${typeColor}`}>
                {SIGNAL_LABELS[signal.type]}
              </span>
              <StrengthPill strength={signal.strength} />
              <SentimentBadge sentiment={signal.sentiment} />
            </div>
            <h1 className="text-xl font-bold text-(--color-text-primary)">{signal.headline}</h1>
            <div className="mt-1 flex items-center gap-3 text-xs text-(--color-text-muted)">
              <Link href={`/company/${signal.ticker}`} className="font-semibold text-(--color-text-primary) hover:text-(--color-accent)">
                {signal.ticker}
              </Link>
              {company && <span>{company.name}</span>}
              <span>{new Date(signal.detected_at).toLocaleString()}</span>
            </div>
          </div>
          <ScoreBadge score={signal.score} size="lg" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl space-y-8">
          {/* Signal detail */}
          <section className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-(--color-text-muted)">
              Signal Detail
            </h3>
            <p className="text-sm leading-relaxed text-(--color-text-primary)">{signal.detail}</p>

            {/* Data points */}
            {signal.data && Object.keys(signal.data).length > 0 && (
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                {Object.entries(signal.data)
                  .filter(([k]) => !["source", "source_url"].includes(k))
                  .slice(0, 6)
                  .map(([key, value]) => (
                    <div key={key} className="rounded-lg border border-(--color-border) bg-(--color-bg-secondary) p-3">
                      <div className="text-[10px] text-(--color-text-muted)">{key.replace(/_/g, " ")}</div>
                      <div className="text-sm font-semibold text-(--color-text-primary)">
                        {typeof value === "number"
                          ? value > 1_000_000
                            ? `$${(value / 1_000_000).toFixed(1)}M`
                            : value % 1 !== 0
                            ? value.toFixed(1)
                            : value.toLocaleString()
                          : Array.isArray(value)
                          ? value.join(", ")
                          : String(value)}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </section>

          {/* Evidence cards */}
          {signal.evidence && signal.evidence.length > 0 && (
            <section>
              <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-(--color-text-muted)">
                Source Evidence ({signal.evidence.length})
              </h3>
              <div className="space-y-3">
                {signal.evidence.map((e: Evidence, i: number) => (
                  <EvidenceCard key={i} evidence={e} />
                ))}
              </div>
            </section>
          )}

          {/* AI Brief */}
          {brief && (
            <section>
              <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-(--color-text-muted)">
                AI Intelligence Brief
              </h3>
              <BriefSection brief={brief} />
            </section>
          )}

          {/* Disclaimer */}
          <div className="rounded-lg border border-(--color-border) bg-(--color-bg-secondary) p-4 text-center text-[10px] text-(--color-text-muted)">
            AlphaRadar provides alternative data signals for informational purposes only.
            This is not financial advice. Always do your own research before making investment decisions.
          </div>
        </div>
      </div>
    </div>
  );
}

function StrengthPill({ strength }: { strength: string }) {
  const colors: Record<string, string> = {
    strong: "bg-(--color-strong)/15 text-(--color-strong)",
    moderate: "bg-(--color-accent)/15 text-(--color-accent)",
    weak: "bg-(--color-text-muted)/15 text-(--color-text-muted)",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${colors[strength] || colors.weak}`}>
      {strength}
    </span>
  );
}
