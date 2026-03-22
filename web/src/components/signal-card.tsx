import type { Signal } from "@/lib/types";
import { SIGNAL_LABELS, SIGNAL_COLORS } from "@/lib/types";
import { ScoreBadge } from "./score-badge";
import { SentimentBadge } from "./sentiment-badge";

export function SignalCard({ signal }: { signal: Signal }) {
  const typeColor = SIGNAL_COLORS[signal.type] || "text-(--color-text-secondary)";

  return (
    <div className="card-shadow rounded-xl border border-(--color-border) bg-(--color-bg-card) p-4 transition-colors hover:border-(--color-accent)/40">
      {/* Header */}
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold uppercase tracking-wide ${typeColor}`}>
            {SIGNAL_LABELS[signal.type]}
          </span>
          <StrengthDot strength={signal.strength} />
        </div>
        <ScoreBadge score={signal.score} />
      </div>

      {/* Ticker */}
      <div className="mb-1 flex items-center gap-2">
        <span className="text-base font-bold">{signal.ticker}</span>
        {signal.company_name && (
          <span className="text-xs text-(--color-text-muted)">{signal.company_name}</span>
        )}
        <SentimentBadge sentiment={signal.sentiment} />
      </div>

      {/* Headline */}
      <p className="mb-1.5 text-sm text-(--color-text-primary)">{signal.headline}</p>

      {/* Detail */}
      <p className="text-xs leading-relaxed text-(--color-text-muted)">{signal.detail}</p>

      {/* Timestamp */}
      <div className="mt-3 text-[10px] text-(--color-text-muted)">
        {new Date(signal.detected_at).toLocaleString()}
      </div>
    </div>
  );
}

function StrengthDot({ strength }: { strength: string }) {
  const colors: Record<string, string> = {
    strong: "bg-(--color-strong)",
    moderate: "bg-(--color-accent)",
    weak: "bg-(--color-text-muted)",
  };
  return (
    <span
      className={`inline-block h-1.5 w-1.5 rounded-full ${colors[strength] || colors.weak}`}
      title={strength}
    />
  );
}
