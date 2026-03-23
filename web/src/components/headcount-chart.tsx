"use client";

interface DataPoint {
  label: string;
  value: number;
}

interface HeadcountChartProps {
  data: DataPoint[];
  height?: number;
}

export function HeadcountChart({ data, height = 160 }: HeadcountChartProps) {
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

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height }} preserveAspectRatio="none">
        <defs>
          <linearGradient id="hc-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fillColor} stopOpacity="0.2" />
            <stop offset="100%" stopColor={fillColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#hc-fill)" />
        <path d={linePath} fill="none" stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        {/* Endpoint dot */}
        <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="2" fill={strokeColor} />
      </svg>
      {/* Labels */}
      <div className="mt-1 flex justify-between text-[10px] text-(--color-text-muted)">
        <span>{data[0].label}</span>
        <span className="font-medium text-(--color-text-primary)">{data[data.length - 1].value.toLocaleString()} employees</span>
        <span>{data[data.length - 1].label}</span>
      </div>
    </div>
  );
}
