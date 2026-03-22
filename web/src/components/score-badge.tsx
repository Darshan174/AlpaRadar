export function ScoreBadge({ score, size = "sm" }: { score: number; size?: "sm" | "lg" }) {
  const color =
    score >= 75
      ? "text-(--color-bullish) border-(--color-bullish)/30 bg-(--color-bullish)/10"
      : score >= 50
        ? "text-(--color-neutral) border-(--color-neutral)/30 bg-(--color-neutral)/10"
        : "text-(--color-text-muted) border-(--color-border) bg-(--color-bg-secondary)";

  const sizeClass = size === "lg" ? "px-3 py-1.5 text-lg font-bold" : "px-2 py-0.5 text-xs font-semibold";

  return (
    <span className={`inline-flex items-center rounded-md border ${color} ${sizeClass}`}>
      {score.toFixed(0)}
    </span>
  );
}
