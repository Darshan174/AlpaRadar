export function ScoreBadge({ score, size = "sm" }: { score: number; size?: "sm" | "lg" }) {
  const tone =
    score >= 75
      ? {
          color: "var(--color-bullish)",
          borderColor: "rgba(34, 197, 94, 0.28)",
          backgroundColor: "rgba(34, 197, 94, 0.12)",
        }
      : score >= 50
        ? {
            color: "var(--color-neutral)",
            borderColor: "rgba(251, 191, 36, 0.28)",
            backgroundColor: "rgba(251, 191, 36, 0.12)",
          }
        : {
            color: "var(--color-text-secondary)",
            borderColor: "var(--color-border)",
            backgroundColor: "rgba(148, 163, 184, 0.08)",
          };

  const sizeClass = size === "lg"
    ? "h-[3.75rem] min-w-[3.75rem] px-4 text-2xl font-bold"
    : "h-10 min-w-10 px-3 text-sm font-semibold";

  return (
    <span
      className={`inline-flex items-center justify-center rounded-2xl border metric-value ${sizeClass}`}
      style={tone}
    >
      {score.toFixed(0)}
    </span>
  );
}
