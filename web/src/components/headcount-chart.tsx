"use client";

import { useId } from "react";

interface DataPoint {
  label: string;
  value: number;
}

interface HeadcountChartProps {
  data: DataPoint[];
  height?: number;
}

export function HeadcountChart({ data, height = 160 }: HeadcountChartProps) {
  const gradientId = useId().replace(/:/g, "");

  if (!data.length) {
    return (
      <div className="flex items-center justify-center text-sm text-(--color-text-muted)" style={{ height }}>
        No headcount data available
      </div>
    );
  }

  const values = data.map((d) => d.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  const isGrowing = values[values.length - 1] > values[0];

  // Build SVG path
  const w = 100;
  const h = 100;
  const padding = 4;
  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (w - padding * 2);
    const y = h - padding - ((d.value - min) / range) * (h - padding * 2);
    return { x, y };
  });

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${h} L ${points[0].x} ${h} Z`;

  const strokeColor = isGrowing ? "var(--color-bullish)" : "var(--color-bearish)";
  const fillColor = isGrowing ? "var(--color-bullish)" : "var(--color-bearish)";
  const changePct = Math.round(((values[values.length - 1] - values[0]) / Math.max(values[0], 1)) * 100);

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height }} preserveAspectRatio="none">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fillColor} stopOpacity="0.2" />
            <stop offset="100%" stopColor={fillColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {[20, 40, 60, 80].map((line) => (
          <path
            key={line}
            d={`M ${padding} ${line} L ${w - padding} ${line}`}
            fill="none"
            stroke="rgba(148, 163, 184, 0.12)"
            strokeDasharray="2 4"
          />
        ))}
        <path d={areaPath} fill={`url(#${gradientId})`} />
        <path d={linePath} fill="none" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="2" fill={strokeColor} />
      </svg>
      <div className="mt-3 flex items-center justify-between gap-3 text-[0.72rem] text-(--color-text-muted)">
        <span>{data[0].label}</span>
        <span className={`font-semibold ${isGrowing ? "text-(--color-bullish)" : "text-(--color-bearish)"}`}>
          {changePct > 0 ? "+" : ""}
          {changePct}% trend
        </span>
        <span className="font-medium text-(--color-text-primary)">{data[data.length - 1].value.toLocaleString()} employees</span>
        <span>{data[data.length - 1].label}</span>
      </div>
    </div>
  );
}
