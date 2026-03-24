import type { Brief, Evidence } from "@/lib/types";
import { EvidenceCard } from "./evidence-card";

export function BriefSection({ brief }: { brief: Brief }) {
  const { sections } = brief;

  return (
    <div className="space-y-5">
      {/* What Happened */}
      <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-(--color-accent)">
          What Happened
        </h3>
        <p className="text-sm leading-relaxed text-(--color-text-primary)">
          {sections.what_happened}
        </p>
      </div>

      {/* Why It Matters */}
      <div className="rounded-xl border border-(--color-border) bg-(--color-bg-card) p-5 card-shadow">
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-(--color-accent)">
          Why It Matters
        </h3>
        <p className="text-sm leading-relaxed text-(--color-text-primary)">
          {sections.why_it_matters}
        </p>
      </div>

      {/* Supporting Evidence */}
      {brief.evidence && brief.evidence.length > 0 && (
        <div>
          <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-(--color-accent)">
            Supporting Evidence
          </h3>
          <div className="space-y-3">
            {brief.evidence.map((e: Evidence, i: number) => (
              <EvidenceCard key={i} evidence={e} />
            ))}
          </div>
        </div>
      )}

      {/* Risks */}
      <div className="rounded-xl border border-(--color-bearish)/20 bg-(--color-bearish)/5 p-5">
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-(--color-bearish)">
          Risks & Alternative Explanations
        </h3>
        <p className="text-sm leading-relaxed text-(--color-text-primary)">
          {sections.risks}
        </p>
      </div>

      {/* Prompt version footer */}
      <div className="text-right text-[10px] text-(--color-text-muted)">
        Brief generated with prompt {brief.prompt_version} &middot;{" "}
        {new Date(brief.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
