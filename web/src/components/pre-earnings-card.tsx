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
    <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-xs font-medium text-(--color-text-muted) uppercase tracking-wide">
            Pre-Earnings Intel
          </div>
          {props.earnings_date && (
            <div className="mt-0.5 text-xs text-(--color-text-secondary)">
              Earnings: {new Date(props.earnings_date).toLocaleDateString()}
            </div>
          )}
        </div>
        <div className="text-right">
          <div className="text-xs text-(--color-text-muted)">Beat Probability</div>
          <div className={`text-2xl font-bold ${isLikely ? "text-(--color-bullish)" : "text-(--color-bearish)"}`}>
            {pct}%
          </div>
        </div>
      </div>

      {/* Probability bar */}
      <div className="mb-4 h-2 w-full overflow-hidden rounded-full bg-(--color-bg-hover)">
        <div
          className={`h-full rounded-full transition-all ${isLikely ? "bg-(--color-bullish)" : "bg-(--color-bearish)"}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Factor grid */}
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
    <div className="rounded-lg bg-(--color-bg-hover)/50 p-2.5">
      <div className="text-[10px] text-(--color-text-muted)">{label}</div>
      {sentiment ? (
        <div className="mt-1"><SentimentBadge sentiment={sentiment} /></div>
      ) : (
        <div className={`text-sm font-semibold ${positive ? "text-(--color-bullish)" : "text-(--color-text-primary)"}`}>
          {value}
        </div>
      )}
    </div>
  );
}
