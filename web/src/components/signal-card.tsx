import type { Signal } from "@/lib/types";
import { SIGNAL_LABELS, SIGNAL_COLORS } from "@/lib/types";
import { extractDataHighlights, formatRelativeTime } from "@/lib/presentation";
import { ScoreBadge } from "./score-badge";
import { SentimentBadge } from "./sentiment-badge";

export function SignalCard({ signal }: { signal: Signal }) {
  const typeColor = SIGNAL_COLORS[signal.type] || "text-(--color-text-secondary)";
  const highlights = extractDataHighlights(signal.data, 3);

  return (
    <div className="surface-panel hover-lift rounded-[28px] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full border border-current/20 bg-white/5 px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.22em] ${typeColor}`}>
              {SIGNAL_LABELS[signal.type]}
            </span>
            <StrengthPill strength={signal.strength} />
            <SentimentBadge sentiment={signal.sentiment} />
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <span className="metric-value text-3xl text-(--color-text-primary)">
              {signal.ticker}
            </span>
            {signal.company_name ? (
              <span className="pb-1 text-sm text-(--color-text-secondary)">
                {signal.company_name}
              </span>
            ) : null}
          </div>
        </div>

        <ScoreBadge score={signal.score} size="lg" />
      </div>

      <div className="mt-5">
        <p className="text-lg font-semibold text-(--color-text-primary)">{signal.headline}</p>
        <p className="mt-2 text-sm leading-7 text-(--color-text-secondary)">{signal.detail}</p>
      </div>

      {highlights.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {highlights.map((item) => (
            <span key={item.label} className="data-chip">
              <span className="text-(--color-text-muted)">{item.label}</span>
              <span className="text-(--color-text-primary)">{item.value}</span>
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-(--color-border) pt-4 text-xs text-(--color-text-muted)">
        <span>{formatRelativeTime(signal.detected_at)}</span>
        <span>{signal.evidence?.length ?? 0} evidence points</span>
      </div>
    </div>
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
