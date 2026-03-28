from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────


class SignalType(str, enum.Enum):
    HIRING_SURGE = "hiring_surge"
    EXECUTIVE_MOVE = "executive_move"
    GROWTH_PRICE_DIVERGENCE = "growth_price_divergence"
    COMPETITOR_SHIFT = "competitor_shift"
    SECTOR_PULSE = "sector_pulse"
    # MVP alt-data signal types
    INSIDER_BUY_CLUSTER = "insider_buy_cluster"
    HIRING_MOMENTUM = "hiring_momentum"
    FILING_CATALYST = "filing_catalyst"
    TRANSCRIPT_TONE_SHIFT = "transcript_tone_shift"


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


class TradeAction(str, enum.Enum):
    """Suggested portfolio action derived from signal fusion."""
    ACCUMULATE = "accumulate"  # Strong bullish conviction
    HOLD = "hold"              # Signals present but mixed
    REDUCE = "reduce"          # Negative signals emerging
    SHORT_CANDIDATE = "short_candidate"  # Strong bearish conviction
    PAIRS_TRADE = "pairs_trade"  # Long/short within sector
    TAKE_PROFIT = "take_profit"  # Price extended vs deteriorating alt-data
    NO_ACTION = "no_action"      # Insufficient data


class TimeHorizon(str, enum.Enum):
    """How soon the signal thesis should play out."""
    SHORT_TERM_CATALYST = "short_term_catalyst"  # Days to 2 weeks (e.g. earnings, exec departure)
    MEDIUM_TERM_SWING = "medium_term_swing"      # 2 weeks to 3 months
    LONG_TERM_COMPOUNDER = "long_term_compounder"  # 3+ months (e.g. sustained hiring surge)
    VALUE_TRAP = "value_trap"  # Looks cheap but alt-data says avoid


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
    historical_win_rate: float | None = None
    historical_avg_return: float | None = None
    historical_sample_size: int | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_actionable(self) -> bool:
        return self.strength in (SignalStrength.STRONG, SignalStrength.MODERATE) and self.score >= 60


class TradeSetup(BaseModel):
    """A concrete trade suggestion derived from fused signals."""
    action: TradeAction = TradeAction.NO_ACTION
    time_horizon: TimeHorizon = TimeHorizon.MEDIUM_TERM_SWING
    conviction: str = "low"  # "high", "medium", "low"
    rationale: str = ""
    risk_note: str = ""
    historical_win_rate: float | None = None  # 0.0-1.0 if backtested
    historical_avg_return: float | None = None  # percent
    historical_sample_size: int | None = None


class PairsTradeSetup(BaseModel):
    """A market-neutral long/short pair suggestion."""
    long_ticker: str
    short_ticker: str
    long_company: str = ""
    short_company: str = ""
    long_score: float = 0.0
    short_score: float = 0.0
    divergence_score: float = 0.0  # How far apart the two are
    rationale: str = ""
    sector: str = ""


class LLMStructuredThesis(BaseModel):
    """Structured fields parsed from the LLM narrative output."""
    suggested_action: str = ""
    time_horizon: str = ""
    conviction: str = ""


class FusedInsight(BaseModel):
    """Combined alternative data + market data insight."""

    ticker: str
    company_name: str = ""
    signals: list[Signal] = Field(default_factory=list)
    market_data: MarketData | None = None
    company_profile: CompanyProfile | None = None
    composite_score: float = 0.0
    sentiment: Sentiment = Sentiment.NEUTRAL
    suggested_action: TradeSetup | None = None
    pairs_trade: PairsTradeSetup | None = None
    llm_structured: LLMStructuredThesis | None = None
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


# ── Source Run Tracking ───────────────────────────────────────────────────────


class SourceRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceRun(BaseModel):
    id: UUID | None = None
    source_name: str
    ticker: str
    status: SourceRunStatus = SourceRunStatus.RUNNING
    records_fetched: int = 0
    records_stored: int = 0
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


# ── Raw Document ──────────────────────────────────────────────────────────────


class RawDocument(BaseModel):
    id: UUID | None = None
    source_name: str
    source_url: str | None = None
    ticker: str | None = None
    doc_type: str
    content_hash: str
    raw_payload: dict[str, Any]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    source_run_id: UUID | None = None


# ── Insider Trade ─────────────────────────────────────────────────────────────


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    GRANT = "grant"
    EXERCISE = "exercise"


class InsiderTrade(BaseModel):
    id: UUID | None = None
    ticker: str
    company_name: str = ""
    cik: str
    filer_name: str
    filer_title: str = ""
    is_officer: bool = False
    is_director: bool = False
    is_ten_pct_owner: bool = False
    transaction_type: TransactionType
    transaction_code: str = ""
    shares: float
    price_per_share: float | None = None
    total_value: float | None = None
    shares_owned_after: float | None = None
    filing_date: date
    transaction_date: date | None = None
    source_url: str
    source_timestamp: datetime | None = None
    idempotency_key: str = ""
    raw_document_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_buy(self) -> bool:
        return self.transaction_type == TransactionType.BUY

    @property
    def is_notable(self) -> bool:
        """Buys by officers/directors above $10k are notable."""
        return (
            self.is_buy
            and (self.is_officer or self.is_director)
            and (self.total_value or 0) >= 10_000
        )


# ── Job Posting ───────────────────────────────────────────────────────────────


class JobPosting(BaseModel):
    id: UUID | None = None
    ticker: str
    company_name: str = ""
    title: str
    department: str = ""
    seniority: str = ""
    location: str = ""
    is_remote: bool = False
    description_snippet: str = ""
    source_name: str
    source_url: str | None = None
    posted_date: date | None = None
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    idempotency_key: str = ""
    raw_document_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Filing Event ──────────────────────────────────────────────────────────────


class FilingEvent(BaseModel):
    id: UUID | None = None
    ticker: str
    company_name: str = ""
    cik: str
    filing_type: str
    form_items: list[str] = Field(default_factory=list)
    filing_date: date
    period_of_report: date | None = None
    headline: str = ""
    summary: str = ""
    source_url: str
    accession_number: str
    source_timestamp: datetime | None = None
    idempotency_key: str = ""
    raw_document_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_material(self) -> bool:
        """8-K items indicating material events."""
        material_items = {"1.01", "1.02", "2.01", "2.05", "2.06", "4.01", "5.02", "8.01"}
        return bool(set(self.form_items) & material_items)


# ── Transcript Chunk ──────────────────────────────────────────────────────────


class TranscriptChunk(BaseModel):
    id: UUID | None = None
    ticker: str
    company_name: str = ""
    fiscal_quarter: str
    call_date: date
    speaker_name: str = ""
    speaker_role: str = ""
    section: str = ""
    chunk_index: int = 0
    content: str
    word_count: int = 0
    source_name: str = ""
    source_url: str | None = None
    source_timestamp: datetime | None = None
    idempotency_key: str = ""
    raw_document_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Company (lightweight universe entry) ──────────────────────────────────────


class Company(BaseModel):
    ticker: str
    name: str
    cik: str | None = None
    sector: str = ""
    industry: str = ""
    domain: str = ""
    market_cap_bucket: str = ""
    in_universe: bool = True
    added_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Brief ─────────────────────────────────────────────────────────────────────


class Brief(BaseModel):
    id: UUID | None = None
    ticker: str
    signal_id: str | None = None
    brief_type: str = "signal"
    headline: str
    body: str
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    model_used: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
