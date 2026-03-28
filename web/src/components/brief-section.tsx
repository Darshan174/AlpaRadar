import type { Brief, Evidence } from "@/lib/types";
import { EvidenceCard } from "./evidence-card";

export function BriefSection({ brief }: { brief: Brief }) {
  const { sections } = brief;

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="surface-panel rounded-[28px] p-6">
          <h3 className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-accent)">
            What Happened
          </h3>
          <p className="mt-4 text-sm leading-7 text-(--color-text-primary)">
            {sections.what_happened}
          </p>
        </div>

        <div className="surface-panel rounded-[28px] p-6">
          <h3 className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-accent)">
            Why It Matters
          </h3>
          <p className="mt-4 text-sm leading-7 text-(--color-text-primary)">
            {sections.why_it_matters}
          </p>
        </div>
      </div>

      {typeof sections.supporting_evidence === "string" ? (
        <div className="surface-panel rounded-[28px] p-6">
          <h3 className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-secondary)">
            Analyst Notes
          </h3>
          <p className="mt-4 text-sm leading-7 text-(--color-text-secondary)">
            {sections.supporting_evidence}
          </p>
        </div>
      ) : null}

      {brief.evidence && brief.evidence.length > 0 ? (
        <div>
          <h3 className="mb-3 text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
            Supporting Evidence
          </h3>
          <div className="space-y-3">
            {brief.evidence.map((e: Evidence, i: number) => (
              <EvidenceCard key={i} evidence={e} />
            ))}
          </div>
        </div>
      ) : null}

      <div className="rounded-[28px] border border-(--color-bearish)/20 bg-(--color-bearish)/6 p-6">
        <h3 className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-bearish)">
          Risks And Alternative Explanations
        </h3>
        <p className="mt-4 text-sm leading-7 text-(--color-text-primary)">
          {sections.risks}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 text-[0.72rem] text-(--color-text-muted)">
        <span>Prompt {brief.prompt_version}</span>
        <span>{new Date(brief.generated_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
