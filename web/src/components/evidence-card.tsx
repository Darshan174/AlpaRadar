import type { Evidence } from "@/lib/types";

const TYPE_ICONS: Record<string, string> = {
  sec_filing: "SEC",
  job_data: "JOBS",
  linkedin: "LI",
  market_data: "MKT",
  historical: "HIST",
  earnings_transcript: "EARN",
  contract: "GOV",
};

const TYPE_COLORS: Record<string, string> = {
  sec_filing: "border-(--color-strong)/40 bg-(--color-strong)/10",
  job_data: "border-(--color-bullish)/40 bg-(--color-bullish)/10",
  linkedin: "border-(--color-accent)/40 bg-(--color-accent)/10",
  market_data: "border-(--color-neutral)/40 bg-(--color-neutral)/10",
  historical: "border-(--color-text-muted)/40 bg-(--color-text-muted)/10",
  earnings_transcript: "border-(--color-accent)/40 bg-(--color-accent)/10",
  contract: "border-(--color-bullish)/40 bg-(--color-bullish)/10",
};

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const icon = TYPE_ICONS[evidence.type] || "SRC";
  const colorClass = TYPE_COLORS[evidence.type] || "border-(--color-border) bg-(--color-bg-card)";

  return (
    <div className={`rounded-xl border p-4 ${colorClass} transition-colors`}>
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 w-10 items-center justify-center rounded-md bg-(--color-bg-primary)/50 text-[9px] font-bold tracking-wider text-(--color-text-secondary)">
            {icon}
          </span>
          <span className="text-sm font-semibold text-(--color-text-primary)">{evidence.title}</span>
        </div>
      </div>

      {evidence.detail && (
        <p className="mb-2 text-xs leading-relaxed text-(--color-text-secondary)">{evidence.detail}</p>
      )}

      <div className="flex flex-wrap items-center gap-3 text-[10px] text-(--color-text-muted)">
        <span>Source: {evidence.source}</span>
        {evidence.timestamp && (
          <span>{new Date(evidence.timestamp).toLocaleDateString()}</span>
        )}
        {evidence.url && (
          <a
            href={evidence.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-(--color-accent) hover:underline"
          >
            View source
          </a>
        )}
      </div>
    </div>
  );
}
