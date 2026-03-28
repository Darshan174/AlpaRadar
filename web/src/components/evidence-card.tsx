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
    <div className={`rounded-[26px] border p-5 ${colorClass} shadow-[0_16px_36px_rgba(2,6,23,0.12)] transition-colors`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex items-center gap-3">
          <span className="inline-flex h-10 w-12 items-center justify-center rounded-2xl bg-(--color-bg-primary)/45 text-[0.68rem] font-bold tracking-[0.24em] text-(--color-text-secondary)">
            {icon}
          </span>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-(--color-text-primary)">{evidence.title}</div>
            <div className="mt-1 text-[0.72rem] uppercase tracking-[0.22em] text-(--color-text-muted)">
              {evidence.source}
            </div>
          </div>
        </div>
      </div>

      {evidence.detail && (
        <p className="mt-4 text-sm leading-7 text-(--color-text-secondary)">{evidence.detail}</p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3 text-[0.72rem] text-(--color-text-muted)">
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
            Open source
          </a>
        )}
      </div>
    </div>
  );
}
