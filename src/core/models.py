from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────


class SignalType(str, enum.Enum):
    HIRING_SURGE = "hiring_surge"
    EXECUTIVE_MOVE = "executive_move"
    GROWTH_PRICE_DIVERGENCE = "growth_price_divergence"
    COMPETITOR_SHIFT = "competitor_shift"
    SECTOR_PULSE = "sector_pulse"


class SignalStrength(str, enum.Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class Sentiment(str, enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class AlertChannel(str, enum.Enum):
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


# ── Company Intelligence (from Crustdata) ──────────────────────────────────────


class HeadcountSnapshot(BaseModel):
    date: datetime
    total: int
    engineering: int | None = None
    sales: int | None = None
    department_breakdown: dict[str, int] = Field(default_factory=dict)


class HeadcountTrend(BaseModel):
    current: int
    previous: int
    period_days: int = 90
    change_pct: float
    department_trends: dict[str, float] = Field(default_factory=dict)

    @property
    def is_surging(self) -> bool:
        return self.change_pct >= 20.0

    @property
    def is_declining(self) -> bool:
        return self.change_pct <= -10.0


class FundingRound(BaseModel):
    date: datetime | None = None
    round_type: str = ""
    amount_usd: float | None = None
    investors: list[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    """Core company data enriched from Crustdata."""

    crustdata_id: str | None = None
    name: str
    domain: str = ""
    ticker: str | None = None
    industry: str = ""
    sector: str = ""
    country: str = ""
    linkedin_url: str = ""
    description: str = ""
    founded_year: int | None = None
    total_headcount: int | None = None
    headcount_trend: HeadcountTrend | None = None
    headcount_history: list[HeadcountSnapshot] = Field(default_factory=list)
    funding_total_usd: float | None = None
    funding_rounds: list[FundingRound] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ── Executive / People Intelligence ────────────────────────────────────────────


class ExecutiveProfile(BaseModel):
    name: str
    title: str = ""
    company: str = ""
    company_ticker: str | None = None
    linkedin_url: str = ""
    previous_companies: list[str] = Field(default_factory=list)
    previous_titles: list[str] = Field(default_factory=list)
    start_date: datetime | None = None
    is_c_suite: bool = False

    @property
    def seniority_tier(self) -> str:
        title_lower = self.title.lower()
        if any(t in title_lower for t in ["ceo", "cto", "cfo", "coo", "cpo", "chief"]):
            return "c_suite"
        if any(t in title_lower for t in ["vp", "vice president", "svp", "evp"]):
            return "vp"
        if "director" in title_lower:
            return "director"
        return "other"


class ExecutiveMove(BaseModel):
    person: ExecutiveProfile
    from_company: str
    to_company: str
    from_ticker: str | None = None
    to_ticker: str | None = None
    move_date: datetime | None = None
    significance_score: float = 0.0


class SocialPost(BaseModel):
    author_name: str = ""
    author_title: str = ""
    content: str = ""
    posted_at: datetime | None = None
    engagement: int = 0
    sentiment: Sentiment = Sentiment.NEUTRAL


# ── Market Data ────────────────────────────────────────────────────────────────


class PriceBar(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class TechnicalIndicators(BaseModel):
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    atr_14: float | None = None
    adx_14: float | None = None
    vwap: float | None = None
    volume_sma_20: float | None = None
    price: float | None = None


class MarketData(BaseModel):
    ticker: str
    company_name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float | None = None
    pe_ratio: float | None = None
    price_history: list[PriceBar] = Field(default_factory=list)
    technicals: TechnicalIndicators | None = None
    price_change_pct_30d: float | None = None
    price_change_pct_90d: float | None = None
    price_change_pct_180d: float | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


# ── Signals ────────────────────────────────────────────────────────────────────


class Signal(BaseModel):
    """A detected alternative-data signal."""

    id: str = ""
    type: SignalType
    strength: SignalStrength
    sentiment: Sentiment
    ticker: str
    company_name: str = ""
    headline: str
    detail: str
    score: float = Field(ge=0, le=100)
    data: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_actionable(self) -> bool:
        return self.strength in (SignalStrength.STRONG, SignalStrength.MODERATE) and self.score >= 60


class FusedInsight(BaseModel):
    """Combined alternative data + market data insight."""

    ticker: str
    company_name: str = ""
    signals: list[Signal] = Field(default_factory=list)
    market_data: MarketData | None = None
    company_profile: CompanyProfile | None = None
    composite_score: float = 0.0
    sentiment: Sentiment = Sentiment.NEUTRAL
    llm_analysis: str = ""
    summary: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def signal_count(self) -> int:
        return len(self.signals)

    @property
    def actionable_signals(self) -> list[Signal]:
        return [s for s in self.signals if s.is_actionable]


# ── Watchlist ──────────────────────────────────────────────────────────────────


class WatchlistItem(BaseModel):
    user_id: str
    ticker: str
    company_name: str = ""
    added_at: datetime = Field(default_factory=datetime.utcnow)
    alert_on: list[SignalType] = Field(default_factory=lambda: list(SignalType))


class WatchlistAlert(BaseModel):
    user_id: str
    ticker: str
    signal: Signal
    channel: AlertChannel = AlertChannel.SLACK
    sent_at: datetime | None = None


# ── Chat / RAG ─────────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RAGContext(BaseModel):
    query: str
    retrieved_chunks: list[str] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    company_profile: CompanyProfile | None = None
    relevance_scores: list[float] = Field(default_factory=list)


# ── Pre-Earnings Intelligence ──────────────────────────────────────────────────


class EarningsIntel(BaseModel):
    ticker: str
    company_name: str = ""
    earnings_date: datetime | None = None
    hiring_trend: HeadcountTrend | None = None
    exec_sentiment: Sentiment = Sentiment.NEUTRAL
    competitor_momentum: float = 0.0
    technical_setup: Sentiment = Sentiment.NEUTRAL
    beat_probability: float = 0.5
    signals: list[Signal] = Field(default_factory=list)
    analysis: str = ""
