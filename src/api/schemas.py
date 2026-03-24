"""API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.models import Sentiment, SignalStrength, SignalType


# ── Requests ───────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    ticker: str
    include_competitors: bool = True
    include_executives: bool = True


class ChatRequest(BaseModel):
    message: str
    ticker: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


class WatchlistAddRequest(BaseModel):
    ticker: str
    company_name: str = ""
    alert_on: list[str] = Field(default_factory=lambda: ["hiring_surge", "executive_move", "growth_price_divergence"])


class SectorScreenRequest(BaseModel):
    sector: str
    min_headcount_growth_pct: float | None = None
    country: str | None = None
    limit: int = 20


class CompanySearchRequest(BaseModel):
    query: str | None = None
    industry: str | None = None
    min_headcount: int | None = None
    min_headcount_growth_pct: float | None = None
    limit: int = 20


# ── Responses ──────────────────────────────────────────────────────────────────


class SignalResponse(BaseModel):
    id: str
    type: str
    strength: str
    sentiment: str
    ticker: str
    company_name: str
    headline: str
    detail: str
    score: float
    data: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime
    source_url: str | None = None
    source_name: str | None = None
    source_timestamp: datetime | None = None


class InsightResponse(BaseModel):
    ticker: str
    company_name: str
    composite_score: float
    sentiment: str
    signal_count: int
    signals: list[SignalResponse]
    llm_analysis: str
    summary: str
    generated_at: datetime


class ChatResponse(BaseModel):
    response: str
    ticker: str | None = None
    signals_referenced: int = 0


class WatchlistResponse(BaseModel):
    items: list[dict[str, Any]]


class SectorPulseResponse(BaseModel):
    sector: str
    signal: SignalResponse | None = None
    companies_tracked: int = 0


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── MVP Alt-Data Responses ────────────────────────────────────────────────────


class BriefResponse(BaseModel):
    id: str
    ticker: str
    signal_id: str | None = None
    brief_type: str
    headline: str
    body: str
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    model_used: str = ""
    generated_at: datetime


class SignalDetailResponse(BaseModel):
    """Signal with its brief and full evidence context."""
    signal: SignalResponse
    brief: BriefResponse | None = None


class CompanyDetailResponse(BaseModel):
    """Company overview with recent signals and briefs."""
    ticker: str
    name: str
    cik: str | None = None
    sector: str = ""
    industry: str = ""
    domain: str = ""
    market_cap_bucket: str = ""
    recent_signals: list[SignalResponse] = Field(default_factory=list)
    recent_briefs: list[BriefResponse] = Field(default_factory=list)
    profile: dict[str, Any] | None = None


class SignalFeedResponse(BaseModel):
    """Paginated signal feed."""
    signals: list[SignalResponse]
    total: int = 0
    has_more: bool = False


class InsiderTradeResponse(BaseModel):
    id: str
    ticker: str
    filer_name: str
    filer_title: str
    transaction_type: str
    shares: float
    price_per_share: float | None = None
    total_value: float | None = None
    filing_date: str
    transaction_date: str | None = None
    source_url: str
    is_officer: bool = False
    is_director: bool = False


class JobPostingSummaryResponse(BaseModel):
    ticker: str
    total_active: int = 0
    by_department: dict[str, int] = Field(default_factory=dict)
    recent_postings: list[dict[str, Any]] = Field(default_factory=list)


class FilingEventResponse(BaseModel):
    id: str
    ticker: str
    filing_type: str
    form_items: list[str] = Field(default_factory=list)
    filing_date: str
    headline: str = ""
    summary: str = ""
    source_url: str
    accession_number: str
