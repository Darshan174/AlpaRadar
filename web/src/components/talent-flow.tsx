interface FlowItem {
  from: string;
  to: string;
  count: number;
}

interface TalentFlowProps {
  flows: FlowItem[];
  focusTicker?: string;
}

export function TalentFlow({ flows, focusTicker }: TalentFlowProps) {
  if (!flows.length) {
    return <div className="text-sm text-(--color-text-muted)">No talent flow data available</div>;
  }

  const maxCount = Math.max(...flows.map((f) => f.count));

  return (
    <div className="space-y-2">
      {flows.map((flow, i) => {
        const inbound = focusTicker && flow.to.toUpperCase() === focusTicker.toUpperCase();
        const barPct = (flow.count / maxCount) * 100;

        return (
          <div key={i} className="rounded-lg border border-(--color-border) bg-(--color-bg-card) p-3 card-shadow">
            <div className="mb-2 flex items-center gap-2 text-sm">
              <span className={`font-medium ${inbound ? "text-(--color-text-muted)" : "text-(--color-text-primary)"}`}>
                {flow.from}
              </span>
              <span className={`text-xs ${inbound ? "text-(--color-bullish)" : "text-(--color-bearish)"}`}>
                {inbound ? "-->" : "<--"}
              </span>
              <span className={`font-medium ${inbound ? "text-(--color-text-primary)" : "text-(--color-text-muted)"}`}>
                {flow.to}
              </span>
              <span className="ml-auto text-xs font-bold text-(--color-text-secondary)">
                {flow.count} people
              </span>
            </div>
            {/* Bar */}
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-(--color-bg-hover)">
              <div
                className={`h-full rounded-full transition-all ${inbound ? "bg-(--color-bullish)" : "bg-(--color-bearish)"}`}
                style={{ width: `${barPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
