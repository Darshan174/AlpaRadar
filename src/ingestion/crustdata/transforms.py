"""Transform Crustdata API responses into core domain models."""

from __future__ import annotations

from datetime import datetime

from src.core.models import (
    CompanyProfile,
    ExecutiveMove,
    ExecutiveProfile,
    FundingRound,
    HeadcountSnapshot,
    HeadcountTrend,
    Sentiment,
    SocialPost,
)

from .models import (
    CrustdataCompanyEnrichment,
    CrustdataPersonResult,
    CrustdataSocialPost,
)


def to_company_profile(raw: CrustdataCompanyEnrichment) -> CompanyProfile:
    """Convert Crustdata enrichment response to domain CompanyProfile."""
    headcount_history = [
        HeadcountSnapshot(
            date=_parse_date(h.date),
            total=h.headcount,
            department_breakdown=h.department_breakdown,
        )
        for h in raw.headcount_history
    ]

    headcount_trend = None
    if len(headcount_history) >= 2:
        current = headcount_history[-1].total
        previous = headcount_history[0].total
        if previous > 0:
            change_pct = ((current - previous) / previous) * 100
            headcount_trend = HeadcountTrend(
                current=current,
                previous=previous,
                period_days=max(
                    1,
                    (headcount_history[-1].date - headcount_history[0].date).days,
                ),
                change_pct=round(change_pct, 2),
            )

    funding_rounds = []
    if raw.funding.last_round_type:
        funding_rounds.append(
            FundingRound(
                date=_parse_date(raw.funding.last_round_date) if raw.funding.last_round_date else None,
                round_type=raw.funding.last_round_type,
                amount_usd=raw.funding.last_round_amount_usd,
                investors=raw.funding.investors,
            )
        )

    return CompanyProfile(
        crustdata_id=raw.company_id or None,
        name=raw.name,
        domain=raw.domain,
        ticker=None,
        industry=raw.industry,
        sector=raw.sector,
        country=raw.country,
        linkedin_url=raw.linkedin_url,
        description=raw.description,
        founded_year=raw.founded_year,
        total_headcount=raw.headcount.total or None,
        headcount_trend=headcount_trend,
        headcount_history=headcount_history,
        funding_total_usd=raw.funding.total_funding_usd,
        funding_rounds=funding_rounds,
        competitors=raw.competitors,
    )


def to_executive_profile(
    raw: CrustdataPersonResult,
    ticker: str | None = None,
) -> ExecutiveProfile:
    """Convert Crustdata person result to domain ExecutiveProfile."""
    previous_companies = []
    previous_titles = []
    for pos in raw.previous_positions:
        if pos.get("company"):
            previous_companies.append(pos["company"])
        if pos.get("title"):
            previous_titles.append(pos["title"])

    title = raw.title
    is_c = any(
        kw in title.lower()
        for kw in ["ceo", "cto", "cfo", "coo", "cpo", "chief", "president"]
    )

    return ExecutiveProfile(
        name=raw.name,
        title=title,
        company=raw.company_name,
        company_ticker=ticker,
        linkedin_url=raw.linkedin_url,
        previous_companies=previous_companies,
        previous_titles=previous_titles,
        is_c_suite=is_c,
    )


def to_social_post(raw: CrustdataSocialPost) -> SocialPost:
    """Convert Crustdata social post to domain SocialPost."""
    return SocialPost(
        author_name=raw.author_name,
        author_title=raw.author_title,
        content=raw.content,
        posted_at=_parse_date(raw.posted_at) if raw.posted_at else None,
        engagement=raw.engagement,
        sentiment=Sentiment.NEUTRAL,
    )


def _parse_date(val: str | None) -> datetime:
    if not val:
        return datetime.utcnow()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return datetime.utcnow()
