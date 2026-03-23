"use client";

import Link from "next/link";

export interface SectorData {
  name: string;
  growth_pct: number;
  companies: number;
  top_ticker?: string;
}

const MOCK_SECTORS: SectorData[] = [
  { name: "AI / ML", growth_pct: 34, companies: 48, top_ticker: "NVDA" },
  { name: "Cloud Infra", growth_pct: 22, companies: 35, top_ticker: "AMZN" },
  { name: "Cybersecurity", growth_pct: 18, companies: 27, top_ticker: "CRWD" },
  { name: "Fintech", growth_pct: 12, companies: 42, top_ticker: "SQ" },
  { name: "SaaS", growth_pct: 8, companies: 63, top_ticker: "CRM" },
  { name: "E-commerce", growth_pct: 3, companies: 31, top_ticker: "SHOP" },
  { name: "Social Media", growth_pct: -2, companies: 18, top_ticker: "META" },
  { name: "Streaming", growth_pct: -5, companies: 12, top_ticker: "NFLX" },
  { name: "Crypto / Web3", growth_pct: -8, companies: 24, top_ticker: "COIN" },
  { name: "Biotech", growth_pct: 15, companies: 56, top_ticker: "MRNA" },
  { name: "EV / Clean", growth_pct: -4, companies: 22, top_ticker: "TSLA" },
  { name: "Semiconductors", growth_pct: 28, companies: 19, top_ticker: "AMD" },
];

export function SectorHeatmap({ sectors }: { sectors?: SectorData[] }) {
  const data = sectors || MOCK_SECTORS;

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
      className="group cursor-pointer rounded-lg border p-3 transition-all hover:scale-[1.02]"
      style={{ backgroundColor: bgColor, borderColor }}
    >
      <div className="mb-1 text-xs font-semibold text-(--color-text-primary) truncate">
        {sector.name}
      </div>
      <div className={`text-lg font-bold ${textColor}`}>
        {sector.growth_pct > 0 ? "+" : ""}{sector.growth_pct}%
      </div>
      <div className="flex items-center justify-between text-[10px] text-(--color-text-muted)">
        <span>{sector.companies} cos</span>
        {sector.top_ticker && (
          <Link
            href={`/company/${sector.top_ticker}`}
            className="text-(--color-accent) hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            {sector.top_ticker}
          </Link>
        )}
      </div>
    </div>
  );
}
