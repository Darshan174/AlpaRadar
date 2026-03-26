import type { Evidence, Sentiment, Signal, SignalType } from "./types";
import { SIGNAL_LABELS } from "./types";

export function formatKeyLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

export function formatMetricValue(value: unknown) {
  if (typeof value === "number") {
    if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (Math.abs(value) >= 1_000) return value.toLocaleString();
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(1);
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

export function formatRelativeTime(timestamp: string) {
  const elapsedMs = Date.now() - new Date(timestamp).getTime();
  if (!Number.isFinite(elapsedMs)) return new Date(timestamp).toLocaleString();

  const minutes = Math.round(elapsedMs / 60_000);
  if (minutes < 60) return `${Math.max(minutes, 1)}m ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;

  return new Date(timestamp).toLocaleDateString();
}

export function extractDataHighlights(data: Record<string, unknown>, limit = 4) {
  return Object.entries(data)
    .filter(([key]) => !["source", "source_url"].includes(key))
    .slice(0, limit)
    .map(([key, value]) => ({
      label: formatKeyLabel(key),
      value: formatMetricValue(value),
    }));
}

export function getSignalMix(signals: Signal[]) {
  return (Object.keys(SIGNAL_LABELS) as SignalType[])
    .map((type) => {
      const bucket = signals.filter((signal) => signal.type === type);
      return {
        type,
        label: SIGNAL_LABELS[type],
        count: bucket.length,
        avgScore: bucket.length
          ? Math.round(bucket.reduce((sum, signal) => sum + signal.score, 0) / bucket.length)
          : 0,
      };
    })
    .filter((bucket) => bucket.count > 0)
    .sort((left, right) => right.count - left.count || right.avgScore - left.avgScore);
}

export function getSentimentBalance(signals: Signal[]) {
  const counts = { bullish: 0, bearish: 0, neutral: 0 };
  for (const signal of signals) counts[signal.sentiment] += 1;

  const bias: Sentiment =
    counts.bullish > counts.bearish
      ? "bullish"
      : counts.bearish > counts.bullish
        ? "bearish"
        : "neutral";

  return { ...counts, bias, net: counts.bullish - counts.bearish };
}

export function collectEvidence(signals: Signal[]) {
  return signals
    .flatMap((signal) => signal.evidence ?? [])
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime());
}

export function getAverageScore(signals: Signal[]) {
  return signals.length
    ? Math.round(signals.reduce((sum, signal) => sum + signal.score, 0) / signals.length)
    : 0;
}

export function getTopSignals(signals: Signal[], limit = 3) {
  return [...signals].sort((left, right) => right.score - left.score).slice(0, limit);
}

export function getEvidenceSources(evidence: Evidence[]) {
  return [...new Set(evidence.map((item) => item.source))];
}

export function extractExecutiveMentions(signals: Signal[]) {
  return signals
    .filter((signal) => signal.type === "executive_move")
    .map((signal) => ({
      name: typeof signal.data["person_name"] === "string" ? (signal.data["person_name"] as string) : signal.headline,
      title:
        typeof signal.data["to_title"] === "string"
          ? (signal.data["to_title"] as string)
          : typeof signal.data["title"] === "string"
            ? (signal.data["title"] as string)
            : signal.company_name,
      from_company: typeof signal.data["from_company"] === "string" ? (signal.data["from_company"] as string) : undefined,
      is_new: typeof signal.data["person_name"] === "string" || typeof signal.data["from_company"] === "string",
      signalId: signal.id,
    }));
}

export function extractReferencedCompanies(signals: Signal[]) {
  const companies = signals.flatMap((signal) => {
    const values: string[] = [];

    if (typeof signal.data["from_company"] === "string") {
      values.push(signal.data["from_company"] as string);
    }

    for (const key of ["companies_expanding", "companies_flat"] as const) {
      const current = signal.data[key];
      if (Array.isArray(current)) {
        values.push(...current.filter((item): item is string => typeof item === "string"));
      }
    }

    return values;
  });

  return [...new Set(companies)];
}

export function getSectorSnapshots(signals: Signal[]) {
  return signals
    .filter((signal) => signal.type === "sector_pulse")
    .map((signal) => ({
      id: signal.id,
      headline: signal.headline,
      sector: typeof signal.data["sector"] === "string" ? (signal.data["sector"] as string) : signal.company_name,
      aggregatePostings:
        typeof signal.data["aggregate_postings"] === "number" ? (signal.data["aggregate_postings"] as number) : null,
      aiSharePct: typeof signal.data["ai_share_pct"] === "number" ? (signal.data["ai_share_pct"] as number) : null,
      expanding: Array.isArray(signal.data["companies_expanding"])
        ? signal.data["companies_expanding"].filter((item): item is string => typeof item === "string")
        : [],
      flat: Array.isArray(signal.data["companies_flat"])
        ? signal.data["companies_flat"].filter((item): item is string => typeof item === "string")
        : [],
      score: signal.score,
    }));
}
