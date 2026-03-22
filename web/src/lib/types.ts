export type SignalType =
  | "hiring_surge"
  | "executive_move"
  | "growth_price_divergence"
  | "competitor_shift"
  | "sector_pulse";

export type SignalStrength = "strong" | "moderate" | "weak";
export type Sentiment = "bullish" | "bearish" | "neutral";

export interface Signal {
  id: string;
  type: SignalType;
  strength: SignalStrength;
  sentiment: Sentiment;
  ticker: string;
  company_name: string;
  headline: string;
  detail: string;
  score: number;
  data: Record<string, unknown>;
  detected_at: string;
}

export interface Insight {
  ticker: string;
  company_name: string;
  composite_score: number;
  sentiment: Sentiment;
  signal_count: number;
  signals: Signal[];
  llm_analysis: string;
  summary: string;
  generated_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  response: string;
  ticker: string | null;
  signals_referenced: number;
}

export interface WatchlistItem {
  user_id: string;
  ticker: string;
  company_name: string;
  alert_on: string[];
  added_at: string;
}

export interface SectorPulse {
  sector: string;
  signal: Signal | null;
  companies_tracked: number;
}

export const SIGNAL_LABELS: Record<SignalType, string> = {
  hiring_surge: "Hiring Surge",
  executive_move: "Exec Move",
  growth_price_divergence: "Growth/Price Gap",
  competitor_shift: "Competitor Shift",
  sector_pulse: "Sector Pulse",
};

export const SIGNAL_COLORS: Record<SignalType, string> = {
  hiring_surge: "text-(--color-bullish)",
  executive_move: "text-(--color-strong)",
  growth_price_divergence: "text-(--color-accent)",
  competitor_shift: "text-(--color-neutral)",
  sector_pulse: "text-(--color-accent)",
};
