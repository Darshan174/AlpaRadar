interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

export function StatCard({ label, value, sub, color }: StatCardProps) {
  return (
    <div className="surface-panel hover-lift rounded-[26px] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
          {label}
        </div>
        {sub ? (
          <span className="rounded-full border border-(--color-border) bg-(--color-bg-hover)/40 px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-(--color-text-secondary)">
            {sub}
          </span>
        ) : null}
      </div>
      <div className={`mt-4 metric-value text-3xl ${color || "text-(--color-text-primary)"}`}>{value}</div>
    </div>
  );
}
