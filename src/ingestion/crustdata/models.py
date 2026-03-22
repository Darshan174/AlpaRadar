"""Response models for Crustdata API — typed wrappers around raw JSON."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Company Enrich Response ────────────────────────────────────────────────────


class CrustdataHeadcount(BaseModel):
    total: int = 0
    engineering: int | None = None
    sales: int | None = None
    departments: dict[str, int] = Field(default_factory=dict)


class CrustdataHeadcountHistory(BaseModel):
    date: str = ""
    headcount: int = 0
    department_breakdown: dict[str, int] = Field(default_factory=dict)


class CrustdataFunding(BaseModel):
    total_funding_usd: float | None = None
    last_round_type: str = ""
    last_round_date: str | None = None
    last_round_amount_usd: float | None = None
    investors: list[str] = Field(default_factory=list)


class CrustdataCompanyEnrichment(BaseModel):
    company_id: str = ""
    name: str = ""
    domain: str = ""
    linkedin_url: str = ""
    description: str = ""
    industry: str = ""
    sector: str = ""
    country: str = ""
    founded_year: int | None = None
    headcount: CrustdataHeadcount = Field(default_factory=CrustdataHeadcount)
    headcount_history: list[CrustdataHeadcountHistory] = Field(default_factory=list)
    funding: CrustdataFunding = Field(default_factory=CrustdataFunding)
    competitors: list[str] = Field(default_factory=list)
    growth_metrics: dict[str, Any] = Field(default_factory=dict)


# ── Company Search Response ────────────────────────────────────────────────────


class CrustdataCompanySearchResult(BaseModel):
    company_id: str = ""
    name: str = ""
    domain: str = ""
    industry: str = ""
    country: str = ""
    headcount: int = 0
    funding_total_usd: float | None = None
    headcount_growth_pct: float | None = None


class CrustdataCompanySearchResponse(BaseModel):
    results: list[CrustdataCompanySearchResult] = Field(default_factory=list)
    total_count: int = 0
    has_more: bool = False


# ── Person Search / Enrich Response ────────────────────────────────────────────


class CrustdataPersonResult(BaseModel):
    person_id: str = ""
    name: str = ""
    title: str = ""
    company_name: str = ""
    company_domain: str = ""
    linkedin_url: str = ""
    location: str = ""
    email: str | None = None
    previous_positions: list[dict[str, str]] = Field(default_factory=list)


class CrustdataPersonSearchResponse(BaseModel):
    results: list[CrustdataPersonResult] = Field(default_factory=list)
    total_count: int = 0


# ── Social Posts Response ──────────────────────────────────────────────────────


class CrustdataSocialPost(BaseModel):
    post_id: str = ""
    author_name: str = ""
    author_title: str = ""
    content: str = ""
    posted_at: str | None = None
    likes: int = 0
    comments: int = 0
    shares: int = 0

    @property
    def engagement(self) -> int:
        return self.likes + self.comments + self.shares
