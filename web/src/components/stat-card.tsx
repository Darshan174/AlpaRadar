interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}

export function StatCard({ label, value, sub, color }: StatCardProps) {
  return (
    <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-4">
      <div className="mb-1 text-xs text-(--color-text-muted)">{label}</div>
      <div className={`text-2xl font-bold ${color || "text-(--color-text-primary)"}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-(--color-text-secondary)">{sub}</div>}
    </div>
  );
}
