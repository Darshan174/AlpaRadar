import Link from "next/link";

interface Executive {
  name: string;
  title: string;
  from_company?: string;
  is_new?: boolean;
  sentiment?: "bullish" | "bearish" | "neutral";
}

export function ExecRoster({ executives }: { executives: Executive[] }) {
  if (!executives.length) {
    return <div className="text-sm text-(--color-text-muted)">No executive data available</div>;
  }

  return (
    <div className="space-y-2">
      {executives.map((exec, i) => (
        <div
          key={i}
          className="flex items-center gap-3 rounded-lg border border-(--color-border) bg-(--color-bg-card) p-3 card-shadow"
        >
          {/* Avatar */}
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-(--color-accent)/15 text-xs font-bold text-(--color-accent)">
            {exec.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-(--color-text-primary) truncate">
                {exec.name}
              </span>
              {exec.is_new && (
                <span className="rounded bg-(--color-bullish)/15 px-1.5 py-0.5 text-[9px] font-bold text-(--color-bullish)">
                  NEW
                </span>
              )}
            </div>
            <div className="text-xs text-(--color-text-muted)">{exec.title}</div>
          </div>

          {/* Origin */}
          {exec.from_company && (
            <div className="shrink-0 text-right">
              <div className="text-[10px] text-(--color-text-muted)">from</div>
              <div className="text-xs font-medium text-(--color-accent)">{exec.from_company}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
