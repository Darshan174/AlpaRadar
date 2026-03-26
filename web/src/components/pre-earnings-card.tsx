import { SentimentBadge } from "./sentiment-badge";
import type { Sentiment } from "@/lib/types";

interface PreEarningsProps {
  ticker: string;
  earnings_date?: string;
  beat_probability: number;
  hiring_trend_pct?: number;
  exec_sentiment: Sentiment;
  technical_setup: Sentiment;
  signals_count: number;
}

export function PreEarningsCard(props: PreEarningsProps) {
  const pct = Math.round(props.beat_probability * 100);
  const isLikely = pct >= 60;

  return (
    <div className="surface-panel rounded-[30px] p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-[0.72rem] font-medium text-(--color-text-muted) uppercase tracking-[0.24em]">
            Pre-Earnings Intel
          </div>
          {props.earnings_date && (
            <div className="mt-1 text-xs text-(--color-text-secondary)">
              Earnings: {new Date(props.earnings_date).toLocaleDateString()}
            </div>
          )}
        </div>
        <div className="text-right">
          <div className="text-xs uppercase tracking-[0.18em] text-(--color-text-muted)">Beat Probability</div>
          <div className={`metric-value text-4xl ${isLikely ? "text-(--color-bullish)" : "text-(--color-bearish)"}`}>
            {pct}%
          </div>
        </div>
      </div>

      <div className="mb-5 h-2.5 w-full overflow-hidden rounded-full bg-(--color-bg-hover)">
        <div
          className={`h-full rounded-full transition-all ${isLikely ? "bg-(--color-bullish)" : "bg-(--color-bearish)"}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Factor
          label="Hiring Trend"
          value={props.hiring_trend_pct != null ? `${props.hiring_trend_pct > 0 ? "+" : ""}${props.hiring_trend_pct}%` : "N/A"}
          positive={props.hiring_trend_pct != null && props.hiring_trend_pct > 5}
        />
        <Factor label="Exec Sentiment" value={props.exec_sentiment} sentiment={props.exec_sentiment} />
        <Factor label="Technical Setup" value={props.technical_setup} sentiment={props.technical_setup} />
        <Factor label="Alt-Data Signals" value={`${props.signals_count} active`} positive={props.signals_count >= 2} />
      </div>
    </div>
  );
}

function Factor({ label, value, positive, sentiment }: {
  label: string;
  value: string;
  positive?: boolean;
  sentiment?: Sentiment;
}) {
  return (
    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/32 p-3">
      <div className="text-[0.68rem] uppercase tracking-[0.2em] text-(--color-text-muted)">{label}</div>
      {sentiment ? (
        <div className="mt-3"><SentimentBadge sentiment={sentiment} /></div>
      ) : (
        <div className={`mt-3 text-sm font-semibold ${positive ? "text-(--color-bullish)" : "text-(--color-text-primary)"}`}>
          {value}
        </div>
      )}
    </div>
  );
}
