import type { Sentiment } from "@/lib/types";

const STYLES: Record<Sentiment, { borderColor: string; backgroundColor: string; color: string }> = {
  bullish: {
    color: "var(--color-bullish)",
    borderColor: "rgba(34, 197, 94, 0.24)",
    backgroundColor: "rgba(34, 197, 94, 0.1)",
  },
  bearish: {
    color: "var(--color-bearish)",
    borderColor: "rgba(248, 113, 113, 0.24)",
    backgroundColor: "rgba(248, 113, 113, 0.1)",
  },
  neutral: {
    color: "var(--color-neutral)",
    borderColor: "rgba(251, 191, 36, 0.24)",
    backgroundColor: "rgba(251, 191, 36, 0.1)",
  },
};

const ARROWS: Record<Sentiment, string> = {
  bullish: "↗",
  bearish: "↘",
  neutral: "•",
};

export function SentimentBadge({ sentiment }: { sentiment: Sentiment }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[0.66rem] font-semibold uppercase tracking-[0.18em]"
      style={STYLES[sentiment]}
    >
      {ARROWS[sentiment]} {sentiment}
    </span>
  );
}
