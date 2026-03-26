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
    <div className="space-y-3">
      {executives.map((exec, i) => (
        <div
          key={i}
          className="surface-panel hover-lift flex items-center gap-4 rounded-[24px] p-4"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-linear-to-br from-orange-500/25 to-sky-500/25 text-sm font-bold text-(--color-text-primary)">
            {exec.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-semibold text-(--color-text-primary)">
                {exec.name}
              </span>
              {exec.is_new && (
                <span className="rounded-full border border-(--color-bullish)/25 bg-(--color-bullish)/12 px-2 py-0.5 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-(--color-bullish)">
                  New
                </span>
              )}
            </div>
            <div className="mt-1 text-xs text-(--color-text-secondary)">{exec.title}</div>
          </div>

          {exec.from_company && (
            <div className="shrink-0 text-right">
              <div className="text-[0.65rem] uppercase tracking-[0.18em] text-(--color-text-muted)">From</div>
              <div className="mt-1 text-xs font-semibold text-(--color-accent)">{exec.from_company}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
