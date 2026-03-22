import type { Sentiment } from "@/lib/types";

const STYLES: Record<Sentiment, string> = {
  bullish: "text-(--color-bullish) bg-(--color-bullish)/10",
  bearish: "text-(--color-bearish) bg-(--color-bearish)/10",
  neutral: "text-(--color-neutral) bg-(--color-neutral)/10",
};

const ARROWS: Record<Sentiment, string> = {
  bullish: "^",
  bearish: "v",
  neutral: "-",
};

export function SentimentBadge({ sentiment }: { sentiment: Sentiment }) {
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${STYLES[sentiment]}`}
    >
      {ARROWS[sentiment]} {sentiment}
    </span>
  );
}
