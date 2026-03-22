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
