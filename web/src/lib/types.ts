export type SignalType =
  | "hiring_surge"
  | "executive_move"
  | "growth_price_divergence"
  | "competitor_shift"
  | "sector_pulse";

export type SignalStrength = "strong" | "moderate" | "weak";
export type Sentiment = "bullish" | "bearish" | "neutral";

export interface Evidence {
  type: string;
  title: string;
  detail: string;
  source: string;
  url?: string;
  timestamp: string;
}

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
  historical_win_rate?: number | null;
  historical_avg_return?: number | null;
  historical_sample_size?: number | null;
  evidence?: Evidence[];
  detected_at: string;
}

export interface BriefSections {
  what_happened: string;
  why_it_matters: string;
  supporting_evidence: string | Evidence[];
  risks: string;
}

export interface Brief {
  signal_id: string;
  ticker: string;
  generated_at: string;
  prompt_version: string;
  sections: BriefSections;
  evidence?: Evidence[];
}

export interface SignalDetail {
  signal: Signal;
  brief: Brief | null;
  company: CompanyInfo | null;
}

export interface CompanyInfo {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  market_cap: number;
}

export interface TradeSetup {
  action: string;
  time_horizon: string;
  conviction: string;
  rationale: string;
  risk_note: string;
  historical_win_rate: number | null;
  historical_avg_return: number | null;
  historical_sample_size: number | null;
}

export interface PairsTradeSetup {
  long_ticker: string;
  short_ticker: string;
  long_company: string;
  short_company: string;
  long_score: number;
  short_score: number;
  divergence_score: number;
  rationale: string;
  sector: string;
}

export interface LLMStructuredThesis {
  suggested_action: string;
  time_horizon: string;
  conviction: string;
}

export interface CompanyDetail {
  company: CompanyInfo | null;
  signals: Signal[];
  briefs: Brief[];
  signal_count: number;
  suggested_action?: TradeSetup | null;
}

export interface FeedResponse {
  signals: Signal[];
  total: number;
  limit: number;
  offset: number;
}

export interface Insight {
  ticker: string;
  company_name: string;
  composite_score: number;
  sentiment: Sentiment;
  signal_count: number;
  signals: Signal[];
  suggested_action?: TradeSetup | null;
  pairs_trade?: PairsTradeSetup | null;
  llm_structured?: LLMStructuredThesis | null;
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

export const ACTION_LABELS: Record<string, string> = {
  accumulate: "Accumulate",
  hold: "Hold",
  reduce: "Reduce",
  short_candidate: "Short Candidate",
  pairs_trade: "Pairs Trade",
  take_profit: "Take Profit",
  no_action: "No Action",
};

export const ACTION_COLORS: Record<string, string> = {
  accumulate: "text-(--color-bullish)",
  hold: "text-(--color-neutral)",
  reduce: "text-(--color-bearish)",
  short_candidate: "text-(--color-bearish)",
  take_profit: "text-(--color-neutral)",
  pairs_trade: "text-(--color-strong)",
  no_action: "text-(--color-text-muted)",
};

export const HORIZON_LABELS: Record<string, string> = {
  short_term_catalyst: "Short-Term Catalyst",
  medium_term_swing: "Medium-Term Swing",
  long_term_compounder: "Long-Term Compounder",
  value_trap: "Value Trap",
};

export const CONVICTION_COLORS: Record<string, string> = {
  high: "text-(--color-bullish)",
  medium: "text-(--color-neutral)",
  low: "text-(--color-text-muted)",
};
