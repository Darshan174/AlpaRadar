"""Input data models for the signal engine.

These represent the normalized records that collectors write.
Detectors consume these and produce Signal objects (from src.core.models).
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Signal types this engine produces ─────────────────────────────────────────

class MVPSignalType(str, enum.Enum):
    """Signal types produced by the MVP signal engine.

    These extend the existing SignalType enum in src.core.models
    without modifying that file.
    """
    INSIDER_BUY_CLUSTER = "insider_buy_cluster"
    HIRING_MOMENTUM = "hiring_momentum"
    MATERIAL_EVENT = "material_event"


# ── SEC Form 4 — Insider Transactions ────────────────────────────────────────

class InsiderTransaction(BaseModel):
    """A single SEC Form 4 insider transaction."""

    filing_date: datetime
    ticker: str
    company_name: str = ""
    insider_name: str
    insider_title: str = ""
    transaction_type: str  # "P" = purchase, "S" = sale, "A" = award
    shares: float
    price_per_share: float
    total_value: float = 0.0
    shares_owned_after: float = 0.0
    source_url: str = ""

    def model_post_init(self, __context: Any) -> None:
        if self.total_value == 0.0:
            self.total_value = abs(self.shares * self.price_per_share)


# ── Job Postings ─────────────────────────────────────────────────────────────

class JobPostingSnapshot(BaseModel):
    """A point-in-time count of job postings for a company."""

    date: datetime
    ticker: str
    company_name: str = ""
    total_postings: int = 0
    engineering_postings: int = 0
    sales_postings: int = 0
    department_breakdown: dict[str, int] = Field(default_factory=dict)


# ── 8-K Material Events ─────────────────────────────────────────────────────

class MaterialFiling(BaseModel):
    """An SEC 8-K filing record."""

    filing_date: datetime
    ticker: str
    company_name: str = ""
    form_type: str = "8-K"  # 8-K, 8-K/A
    items: list[str] = Field(default_factory=list)  # e.g. ["1.01", "9.01"]
    description: str = ""
    source_url: str = ""


# ── Earnings Transcript Sentiment ────────────────────────────────────────────

class TranscriptSentiment(BaseModel):
    """Deterministic sentiment summary of an earnings transcript.

    This is the *output* of a keyword/heuristic pre-processor,
    not an LLM analysis. The collector produces this.
    """

    date: datetime
    ticker: str
    company_name: str = ""
    quarter: str = ""  # e.g. "Q3 2025"
    # Sentiment scores (-1.0 to 1.0) from keyword analysis
    overall_sentiment: float = 0.0
    guidance_sentiment: float = 0.0
    # Keyword hit counts
    positive_keyword_hits: int = 0
    negative_keyword_hits: int = 0
    risk_keyword_hits: int = 0
    growth_keyword_hits: int = 0
    # Raw keyword evidence
    notable_phrases: list[str] = Field(default_factory=list)
    source_url: str = ""
