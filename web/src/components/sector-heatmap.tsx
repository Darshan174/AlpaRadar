"use client";

import Link from "next/link";

export interface SectorData {
  name: string;
  growth_pct: number;
  companies: number;
  top_ticker?: string;
}

export function SectorHeatmap({ sectors }: { sectors?: SectorData[] }) {
  const data = sectors || [];

  if (!data.length) {
    return (
      <div className="rounded-[24px] border border-dashed border-(--color-border) p-6 text-sm text-(--color-text-muted)">
        No sector data is available.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
      {data.map((sector) => (
        <SectorTile key={sector.name} sector={sector} />
      ))}
    </div>
  );
}

function SectorTile({ sector }: { sector: SectorData }) {
  const intensity = Math.min(Math.abs(sector.growth_pct) / 30, 1);
  const isPositive = sector.growth_pct >= 0;

  const bgColor = isPositive
    ? `rgba(34, 197, 94, ${0.08 + intensity * 0.2})`
    : `rgba(239, 68, 68, ${0.08 + intensity * 0.2})`;

  const borderColor = isPositive
    ? `rgba(34, 197, 94, ${0.15 + intensity * 0.3})`
    : `rgba(239, 68, 68, ${0.15 + intensity * 0.3})`;

  const textColor = isPositive ? "text-(--color-bullish)" : "text-(--color-bearish)";

  return (
    <div
      className="group relative overflow-hidden rounded-[24px] border p-4 transition-all hover:-translate-y-1"
      style={{ backgroundColor: bgColor, borderColor }}
    >
      <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-white/6 blur-2xl" />
      <div className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-(--color-text-muted)">
        {sector.name}
      </div>
      <div className={`metric-value text-3xl ${textColor}`}>
        {sector.growth_pct > 0 ? "+" : ""}{sector.growth_pct}%
      </div>
      <div className="mt-4 flex items-center justify-between text-[0.72rem] text-(--color-text-muted)">
        <span>{sector.companies} companies</span>
        {sector.top_ticker ? (
          <Link
            href={`/company/${sector.top_ticker}`}
            className="text-(--color-accent) hover:underline"
            onClick={(event) => event.stopPropagation()}
          >
            {sector.top_ticker} →
          </Link>
        ) : null}
      </div>
    </div>
  );
}
