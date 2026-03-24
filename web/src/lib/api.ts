const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Intelligence ──────────────────────────────────────────────────────────────

import type {
  Insight, Signal, ChatResponse, SectorPulse, WatchlistItem,
  SignalDetail, Brief, CompanyDetail, CompanyInfo, FeedResponse,
} from "./types";

export async function analyzeTicker(
  ticker: string,
  opts?: { include_competitors?: boolean; include_executives?: boolean }
): Promise<Insight> {
  return request<Insight>("/v1/analyze", {
    method: "POST",
    body: JSON.stringify({
      ticker,
      include_competitors: opts?.include_competitors ?? true,
      include_executives: opts?.include_executives ?? true,
    }),
  });
}

export async function analyzeSector(
  sector: string,
  opts?: { min_headcount_growth_pct?: number; limit?: number }
): Promise<SectorPulse> {
  return request<SectorPulse>("/v1/analyze/sector", {
    method: "POST",
    body: JSON.stringify({ sector, ...opts }),
  });
}

// ── Signals ───────────────────────────────────────────────────────────────────

export async function getSignals(params?: {
  ticker?: string;
  type?: string;
  min_score?: number;
  limit?: number;
}): Promise<Signal[]> {
  const qs = new URLSearchParams();
  if (params?.ticker) qs.set("ticker", params.ticker);
  if (params?.type) qs.set("type", params.type);
  if (params?.min_score) qs.set("min_score", String(params.min_score));
  if (params?.limit) qs.set("limit", String(params.limit));
  return request<Signal[]>(`/v1/signals?${qs}`);
}

export async function searchSignals(
  query: string,
  limit = 10
): Promise<{ query: string; results: Signal[] }> {
  return request(`/v1/signals/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

// ── Feed & Detail ────────────────────────────────────────────────────────────

export async function getFeed(params?: {
  ticker?: string;
  type?: string;
  min_score?: number;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}): Promise<FeedResponse> {
  const qs = new URLSearchParams();
  if (params?.ticker) qs.set("ticker", params.ticker);
  if (params?.type) qs.set("type", params.type);
  if (params?.min_score) qs.set("min_score", String(params.min_score));
  if (params?.date_from) qs.set("date_from", params.date_from);
  if (params?.date_to) qs.set("date_to", params.date_to);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  return request<FeedResponse>(`/v1/feed?${qs}`);
}

export async function getSignalDetail(signalId: string): Promise<SignalDetail> {
  return request<SignalDetail>(`/v1/signal/${signalId}`);
}

export async function generateBrief(
  signalId: string,
  promptVersion = "v1"
): Promise<Brief> {
  return request<Brief>(`/v1/signal/${signalId}/brief?prompt_version=${promptVersion}`, {
    method: "POST",
  });
}

export async function getCompanyDetail(ticker: string): Promise<CompanyDetail> {
  return request<CompanyDetail>(`/v1/company/${ticker}`);
}

export async function listCompanies(): Promise<{ companies: CompanyInfo[]; total: number }> {
  return request(`/v1/companies`);
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendChat(
  message: string,
  opts?: { ticker?: string; history?: { role: string; content: string }[] }
): Promise<ChatResponse> {
  return request<ChatResponse>("/v1/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      ticker: opts?.ticker,
      history: opts?.history ?? [],
    }),
  });
}

// ── Watchlist ─────────────────────────────────────────────────────────────────

export async function getWatchlist(userId: string): Promise<{ items: WatchlistItem[] }> {
  return request(`/v1/watchlist?user_id=${encodeURIComponent(userId)}`);
}

export async function addToWatchlist(
  userId: string,
  ticker: string,
  companyName?: string
): Promise<{ status: string }> {
  return request(`/v1/watchlist?user_id=${encodeURIComponent(userId)}`, {
    method: "POST",
    body: JSON.stringify({ ticker, company_name: companyName ?? "" }),
  });
}

export async function removeFromWatchlist(
  userId: string,
  ticker: string
): Promise<{ status: string }> {
  return request(`/v1/watchlist/${ticker}?user_id=${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
}
