"""Seed data for AlphaRadar MVP — realistic mock signals, companies, and briefs.

Used when Supabase/Crustdata are unavailable. Every signal includes source evidence
and timestamps so the UI can render source-backed cards.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from src.core.models import CompanyProfile, FusedInsight, Sentiment, Signal, SignalStrength, SignalType
from src.intelligence.scorer import (
    SIGNAL_HISTORICAL_STATS,
    attach_historical_signal_stats,
    score_insight,
    suggest_action,
)

now = datetime.now(timezone.utc)


def _id() -> str:
    return uuid.uuid4().hex[:12]


# ── Companies ─────────────────────────────────────────────────────────────────

COMPANIES: list[dict] = [
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors", "market_cap": 2_800_000_000_000},
    {"ticker": "PLTR", "name": "Palantir Technologies", "sector": "Technology", "industry": "Software — Infrastructure", "market_cap": 120_000_000_000},
    {"ticker": "META", "name": "Meta Platforms Inc", "sector": "Communication Services", "industry": "Internet Content & Information", "market_cap": 1_500_000_000_000},
    {"ticker": "SNOW", "name": "Snowflake Inc", "sector": "Technology", "industry": "Software — Application", "market_cap": 55_000_000_000},
    {"ticker": "CRM", "name": "Salesforce Inc", "sector": "Technology", "industry": "Software — Application", "market_cap": 275_000_000_000},
    {"ticker": "TSLA", "name": "Tesla Inc", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers", "market_cap": 650_000_000_000},
    {"ticker": "AMZN", "name": "Amazon.com Inc", "sector": "Consumer Cyclical", "industry": "Internet Retail", "market_cap": 1_900_000_000_000},
    {"ticker": "GOOGL", "name": "Alphabet Inc", "sector": "Communication Services", "industry": "Internet Content & Information", "market_cap": 2_100_000_000_000},
    {"ticker": "AAPL", "name": "Apple Inc", "sector": "Technology", "industry": "Consumer Electronics", "market_cap": 3_400_000_000_000},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software — Infrastructure", "market_cap": 3_100_000_000_000},
]

COMPANY_BY_TICKER = {c["ticker"]: c for c in COMPANIES}

# ── Signals ───────────────────────────────────────────────────────────────────

SIGNALS: list[dict] = [
    # -- NVDA signals --
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "strong",
        "sentiment": "bullish",
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "headline": "NVIDIA posted 340+ engineering roles in 14 days",
        "detail": "Job postings on LinkedIn and careers page spiked 62% week-over-week, concentrated in GPU architecture and CUDA teams. Historically, hiring surges of this magnitude precede revenue beats by 1-2 quarters.",
        "score": 88.0,
        "data": {
            "job_postings_14d": 342,
            "wow_change_pct": 62.0,
            "top_departments": ["GPU Architecture", "CUDA Engineering", "AI Research"],
            "headcount_change_pct": 8.5,
            "source": "LinkedIn Jobs API via SerpAPI",
            "source_url": "https://www.linkedin.com/company/nvidia/jobs/",
        },
        "evidence": [
            {"type": "job_data", "title": "LinkedIn job postings for NVIDIA", "detail": "342 new engineering roles posted in past 14 days", "source": "SerpAPI / Google Jobs", "url": "https://www.google.com/search?q=nvidia+jobs", "timestamp": (now - timedelta(hours=6)).isoformat()},
            {"type": "historical", "title": "Prior hiring surge correlation", "detail": "Q3 2024 hiring spike of +55% preceded a 22% revenue beat", "source": "AlphaRadar historical analysis", "timestamp": (now - timedelta(days=180)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=3)).isoformat(),
    },
    {
        "id": _id(),
        "type": "executive_move",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "NVDA",
        "company_name": "NVIDIA Corporation",
        "headline": "Former Google VP of AI Infrastructure joins NVIDIA as SVP",
        "detail": "Devi Shankar, who led Google's TPU infrastructure team for 5 years, joined NVIDIA as SVP of AI Platforms. C-suite hires from competitors signal aggressive expansion into cloud AI services.",
        "score": 72.0,
        "data": {
            "person_name": "Devi Shankar",
            "from_company": "Google",
            "from_title": "VP of AI Infrastructure",
            "to_title": "SVP of AI Platforms",
            "seniority": "vp",
            "source": "SEC Form 8-K filing",
            "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810&type=8-K",
        },
        "evidence": [
            {"type": "sec_filing", "title": "NVIDIA 8-K — Executive Appointment", "detail": "Material event filing announcing SVP appointment", "source": "SEC EDGAR", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810&type=8-K", "timestamp": (now - timedelta(days=2)).isoformat()},
            {"type": "linkedin", "title": "Devi Shankar LinkedIn profile update", "detail": "Profile updated to reflect NVIDIA SVP role", "source": "LinkedIn (public profile)", "timestamp": (now - timedelta(days=1)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=18)).isoformat(),
    },

    # -- PLTR signals --
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "strong",
        "sentiment": "bullish",
        "ticker": "PLTR",
        "company_name": "Palantir Technologies",
        "headline": "Palantir hiring 200+ sales engineers — largest expansion in 2 years",
        "detail": "Federal and commercial sales teams expanding simultaneously. 85 new AIP (Artificial Intelligence Platform) specialist roles suggest acceleration of commercial revenue pipeline.",
        "score": 82.0,
        "data": {
            "job_postings_14d": 215,
            "wow_change_pct": 48.0,
            "top_departments": ["Sales Engineering", "AIP Specialists", "Federal Solutions"],
            "headcount_change_pct": 12.3,
            "source": "Google Jobs via SerpAPI",
        },
        "evidence": [
            {"type": "job_data", "title": "Palantir job postings surge", "detail": "215 new roles posted, 85 in AIP specialization", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=12)).isoformat()},
            {"type": "contract", "title": "Recent federal contract awards", "detail": "3 new DoD contracts worth $120M+ in past 30 days", "source": "USAspending.gov", "url": "https://www.usaspending.gov", "timestamp": (now - timedelta(days=5)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=8)).isoformat(),
    },
    {
        "id": _id(),
        "type": "executive_move",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "PLTR",
        "company_name": "Palantir Technologies",
        "headline": "3 senior Amazon AWS leaders join Palantir's commercial team",
        "detail": "Three Director+ hires from AWS in past 30 days targeting enterprise AIP deployment. This pattern mirrors Snowflake's 2021 talent acquisition strategy that preceded their hypergrowth phase.",
        "score": 68.0,
        "data": {
            "hires_count": 3,
            "from_company": "Amazon (AWS)",
            "seniority": "director",
            "source": "SEC Form 4 + LinkedIn",
        },
        "evidence": [
            {"type": "linkedin", "title": "AWS → Palantir talent movement", "detail": "3 Director-level hires from AWS in 30 days", "source": "LinkedIn public profiles", "timestamp": (now - timedelta(days=3)).isoformat()},
        ],
        "detected_at": (now - timedelta(days=1)).isoformat(),
    },

    # -- META signals --
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "META",
        "company_name": "Meta Platforms Inc",
        "headline": "Meta ramps Reality Labs hiring +35% despite broader tech layoffs",
        "detail": "While many tech companies cut headcount, Meta's Reality Labs division posted 180+ new roles focused on AR/VR hardware and spatial computing. This contrarian signal suggests conviction in their metaverse bet.",
        "score": 71.0,
        "data": {
            "job_postings_14d": 184,
            "wow_change_pct": 35.0,
            "top_departments": ["Reality Labs", "AR/VR Hardware", "Spatial Computing"],
            "headcount_change_pct": 4.2,
            "source": "Google Jobs via SerpAPI",
        },
        "evidence": [
            {"type": "job_data", "title": "Meta Reality Labs hiring spike", "detail": "184 new roles, 35% WoW increase in Reality Labs", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=10)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=14)).isoformat(),
    },
    {
        "id": _id(),
        "type": "growth_price_divergence",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "META",
        "company_name": "Meta Platforms Inc",
        "headline": "Meta's hiring growth (+4.2%) diverges from stock decline (-8.3% 30d)",
        "detail": "Stock pulled back on macro fears while company continues aggressive hiring across AI and Reality Labs. Historical analysis shows this divergence pattern resolves bullishly 73% of the time within 90 days.",
        "score": 65.0,
        "data": {
            "headcount_change_pct": 4.2,
            "price_change_30d_pct": -8.3,
            "divergence_score": 12.5,
            "historical_resolution": "bullish in 73% of cases",
            "source": "yfinance + SerpAPI",
        },
        "evidence": [
            {"type": "market_data", "title": "META 30-day price decline", "detail": "Stock down 8.3% while S&P 500 flat", "source": "yfinance", "timestamp": now.isoformat()},
            {"type": "job_data", "title": "Hiring trend positive", "detail": "Headcount growth +4.2% QoQ despite stock weakness", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=10)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=5)).isoformat(),
    },

    # -- TSLA signals --
    {
        "id": _id(),
        "type": "executive_move",
        "strength": "strong",
        "sentiment": "bearish",
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "headline": "Tesla CFO sells $45M in shares — largest insider sale in 6 months",
        "detail": "CFO Vaibhav Taneja sold 150,000 shares at ~$300/share. This is the largest insider sale since September 2025. While insiders sell for many reasons, concentrated large sales by CFOs historically correlate with upcoming guidance revisions.",
        "score": 78.0,
        "data": {
            "person_name": "Vaibhav Taneja",
            "title": "CFO",
            "shares_sold": 150000,
            "sale_value_usd": 45_000_000,
            "form_type": "Form 4",
            "source": "SEC EDGAR Form 4",
            "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=4",
        },
        "evidence": [
            {"type": "sec_filing", "title": "Tesla Form 4 — Insider Sale", "detail": "CFO Vaibhav Taneja sold 150,000 shares ($45M)", "source": "SEC EDGAR", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001318605&type=4", "timestamp": (now - timedelta(days=1)).isoformat()},
            {"type": "historical", "title": "Prior insider sale pattern", "detail": "CFO sold $30M in shares in Aug 2025 — stock dropped 12% over next 60 days", "source": "OpenInsider", "url": "https://openinsider.com/screener?s=TSLA", "timestamp": (now - timedelta(days=180)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=6)).isoformat(),
    },
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "weak",
        "sentiment": "neutral",
        "ticker": "TSLA",
        "company_name": "Tesla Inc",
        "headline": "Tesla hiring flat — Robotaxi team grows while manufacturing shrinks",
        "detail": "Net hiring is roughly flat (+1.2%), but composition shift is notable: Robotaxi/FSD team up 25% while Fremont and Austin manufacturing roles down 15%. Suggests strategic pivot toward autonomy.",
        "score": 52.0,
        "data": {
            "job_postings_14d": 95,
            "wow_change_pct": 1.2,
            "top_departments": ["Robotaxi/FSD", "AI Training", "Manufacturing (declining)"],
            "headcount_change_pct": 1.2,
            "source": "Google Jobs via SerpAPI",
        },
        "evidence": [
            {"type": "job_data", "title": "Tesla job postings composition shift", "detail": "FSD/Robotaxi +25%, Manufacturing -15%", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=8)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=10)).isoformat(),
    },

    # -- SNOW signals --
    {
        "id": _id(),
        "type": "executive_move",
        "strength": "strong",
        "sentiment": "bearish",
        "ticker": "SNOW",
        "company_name": "Snowflake Inc",
        "headline": "Two VP-level departures from Snowflake in 10 days",
        "detail": "VP of Product (AI/ML) and VP of Enterprise Sales both departed within 10 days. Back-to-back senior departures historically signal internal strategic disagreements. Both roles remain unfilled.",
        "score": 75.0,
        "data": {
            "departures_count": 2,
            "departed_titles": ["VP of Product (AI/ML)", "VP of Enterprise Sales"],
            "timeframe_days": 10,
            "roles_filled": False,
            "source": "SEC Form 8-K + LinkedIn",
        },
        "evidence": [
            {"type": "sec_filing", "title": "Snowflake 8-K — Executive Departures", "detail": "Material event filing for VP-level departures", "source": "SEC EDGAR", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001640147&type=8-K", "timestamp": (now - timedelta(days=3)).isoformat()},
            {"type": "linkedin", "title": "VP profile updates", "detail": "Both VPs updated LinkedIn to show departure from Snowflake", "source": "LinkedIn public profiles", "timestamp": (now - timedelta(days=2)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=20)).isoformat(),
    },

    # -- CRM signals --
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "strong",
        "sentiment": "bullish",
        "ticker": "CRM",
        "company_name": "Salesforce Inc",
        "headline": "Salesforce Agentforce team triples headcount in Q1",
        "detail": "Salesforce's AI agent platform (Agentforce) team grew from ~200 to ~600 engineers. This is the fastest internal team ramp since the Slack integration in 2022. Signals massive investment in agentic AI.",
        "score": 85.0,
        "data": {
            "job_postings_14d": 280,
            "wow_change_pct": 55.0,
            "top_departments": ["Agentforce Engineering", "AI Platform", "Enterprise AI"],
            "headcount_change_pct": 15.8,
            "source": "Google Jobs via SerpAPI",
        },
        "evidence": [
            {"type": "job_data", "title": "Agentforce hiring explosion", "detail": "280 new Agentforce-related roles in 14 days", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=4)).isoformat()},
            {"type": "earnings_transcript", "title": "Q4 2025 earnings call mention", "detail": "CEO Marc Benioff: 'Agentforce is the biggest platform shift since cloud'", "source": "Financial Modeling Prep (transcript)", "url": "https://financialmodelingprep.com/api/v3/earning_call_transcript/CRM", "timestamp": (now - timedelta(days=45)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=2)).isoformat(),
    },

    # -- AMZN signals --
    {
        "id": _id(),
        "type": "growth_price_divergence",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "AMZN",
        "company_name": "Amazon.com Inc",
        "headline": "AWS hiring surges +18% while AMZN stock trades flat for 60 days",
        "detail": "AWS cloud division posted 500+ new roles in the past month while AMZN stock has been range-bound. AWS revenue is the key driver; hiring acceleration typically precedes segment revenue beats.",
        "score": 69.0,
        "data": {
            "headcount_change_pct": 18.0,
            "price_change_30d_pct": -1.2,
            "divergence_score": 19.2,
            "segment": "AWS",
            "source": "yfinance + Google Jobs",
        },
        "evidence": [
            {"type": "job_data", "title": "AWS hiring acceleration", "detail": "500+ new AWS roles in 30 days, +18% vs prior period", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=6)).isoformat()},
            {"type": "market_data", "title": "AMZN price stagnation", "detail": "Stock flat (-1.2%) for 60 days despite market rally", "source": "yfinance", "timestamp": now.isoformat()},
        ],
        "detected_at": (now - timedelta(hours=4)).isoformat(),
    },

    # -- GOOGL signals --
    {
        "id": _id(),
        "type": "hiring_surge",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "GOOGL",
        "company_name": "Alphabet Inc",
        "headline": "Google DeepMind headcount up 22% — aggressive AI talent acquisition",
        "detail": "DeepMind and Google AI teams posted 320+ roles. Notable emphasis on Gemini model training and AI infrastructure. Google appears to be matching NVIDIA and Meta's AI investment pace.",
        "score": 74.0,
        "data": {
            "job_postings_14d": 325,
            "wow_change_pct": 22.0,
            "top_departments": ["DeepMind", "Gemini Team", "AI Infrastructure"],
            "headcount_change_pct": 6.8,
            "source": "Google Jobs via SerpAPI",
        },
        "evidence": [
            {"type": "job_data", "title": "DeepMind hiring surge", "detail": "325 AI/ML roles posted, 22% WoW increase", "source": "SerpAPI / Google Jobs", "timestamp": (now - timedelta(hours=8)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=12)).isoformat(),
    },

    # -- MSFT signals --
    {
        "id": _id(),
        "type": "executive_move",
        "strength": "moderate",
        "sentiment": "bullish",
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "headline": "Microsoft hires Anthropic's former Head of Safety as VP of Responsible AI",
        "detail": "Key AI safety hire signals Microsoft is investing heavily in responsible AI positioning ahead of potential EU AI Act enforcement. Strategic move to differentiate Copilot in enterprise market.",
        "score": 66.0,
        "data": {
            "person_name": "Sarah Mitchell",
            "from_company": "Anthropic",
            "from_title": "Head of Safety",
            "to_title": "VP of Responsible AI",
            "seniority": "vp",
            "source": "SEC Form 8-K",
        },
        "evidence": [
            {"type": "sec_filing", "title": "Microsoft 8-K — Executive Appointment", "detail": "VP of Responsible AI appointed", "source": "SEC EDGAR", "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000789019&type=8-K", "timestamp": (now - timedelta(days=4)).isoformat()},
        ],
        "detected_at": (now - timedelta(days=2)).isoformat(),
    },

    # -- Sector signal --
    {
        "id": _id(),
        "type": "sector_pulse",
        "strength": "strong",
        "sentiment": "bullish",
        "ticker": "NVDA",
        "company_name": "Semiconductor Sector",
        "headline": "Semiconductor sector hiring at 18-month high — AI demand driving expansion",
        "detail": "Aggregate semiconductor hiring across NVDA, AMD, INTC, QCOM, and TSM is at the highest level since Q3 2024. GPU and AI accelerator roles account for 65% of all new postings.",
        "score": 80.0,
        "data": {
            "sector": "Semiconductors",
            "aggregate_postings": 1250,
            "ai_share_pct": 65.0,
            "companies_expanding": ["NVDA", "AMD", "QCOM"],
            "companies_flat": ["INTC", "TSM"],
            "source": "SerpAPI aggregate",
        },
        "evidence": [
            {"type": "job_data", "title": "Sector-wide hiring analysis", "detail": "1,250 new semiconductor roles across 5 major companies", "source": "SerpAPI / Google Jobs (aggregate)", "timestamp": (now - timedelta(hours=2)).isoformat()},
        ],
        "detected_at": (now - timedelta(hours=1)).isoformat(),
    },
]

SIGNAL_BY_ID = {s["id"]: s for s in SIGNALS}


# ── Risk text helper (must be defined before BRIEFS loop) ────────────────────

_RISK_MAP = {
    "hiring_surge": "Job postings don't always convert to actual hires. Companies sometimes post roles for competitive intelligence or to appear growth-oriented ahead of earnings. Verify with subsequent headcount data.",
    "executive_move": "Executive hires/departures have many causes (personal, compensation, relocation). A single move is noisy; clusters of moves in the same direction are more significant.",
    "growth_price_divergence": "Price declines may reflect information not yet visible in alternative data (regulatory risk, customer churn, macro headwinds). Divergence can persist longer than expected.",
    "competitor_shift": "Talent flow data has a lag — employees update LinkedIn weeks or months after moving. Competitor dynamics can shift quickly with M&A or layoffs.",
    "sector_pulse": "Sector-level trends may mask company-specific weakness. Not all companies in an expanding sector will benefit equally.",
}


def _get_risk_text(signal: dict) -> str:
    return _RISK_MAP.get(signal["type"], "Standard investment risk applies. Past signals do not guarantee future outcomes.")


# ── Pre-generated Briefs ─────────────────────────────────────────────────────

BRIEFS: dict[str, dict] = {}

for signal in SIGNALS:
    sid = signal["id"]
    ticker = signal["ticker"]
    BRIEFS[sid] = {
        "signal_id": sid,
        "ticker": ticker,
        "generated_at": signal["detected_at"],
        "prompt_version": "v1",
        "sections": {
            "what_happened": signal["headline"],
            "why_it_matters": signal["detail"],
            "supporting_evidence": signal.get("evidence", []),
            "risks": _get_risk_text(signal),
        },
    }


# ── Helper functions ──────────────────────────────────────────────────────────


def get_signals(
    ticker: str | None = None,
    signal_type: str | None = None,
    min_score: float = 0.0,
    limit: int = 50,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Filter and return seed signals."""
    results = SIGNALS

    if ticker:
        results = [s for s in results if s["ticker"] == ticker.upper()]
    if signal_type:
        results = [s for s in results if s["type"] == signal_type]
    if min_score > 0:
        results = [s for s in results if s["score"] >= min_score]
    if date_from:
        results = [s for s in results if s["detected_at"] >= date_from]
    if date_to:
        results = [s for s in results if s["detected_at"] <= date_to]

    results = sorted(results, key=lambda s: s["detected_at"], reverse=True)
    return [_decorate_signal(signal) for signal in results[:limit]]


def get_signal_by_id(signal_id: str) -> dict | None:
    """Get a single signal by ID."""
    signal = SIGNAL_BY_ID.get(signal_id)
    return _decorate_signal(signal) if signal else None


def get_brief_for_signal(signal_id: str) -> dict | None:
    """Get the brief for a given signal."""
    return BRIEFS.get(signal_id)


def get_company(ticker: str) -> dict | None:
    """Get company info by ticker."""
    return COMPANY_BY_TICKER.get(ticker.upper())


def get_feed(limit: int = 20, offset: int = 0) -> dict:
    """Get the signal feed with pagination."""
    sorted_signals = sorted(SIGNALS, key=lambda s: s["detected_at"], reverse=True)
    page = [_decorate_signal(signal) for signal in sorted_signals[offset : offset + limit]]
    return {
        "signals": page,
        "total": len(SIGNALS),
        "limit": limit,
        "offset": offset,
    }


def get_company_signals(ticker: str) -> dict:
    """Get all signals + brief for a company."""
    company = get_company(ticker)
    signals = get_signals(ticker=ticker)
    briefs = [BRIEFS[s["id"]] for s in signals if s["id"] in BRIEFS]
    trade_setup = get_trade_setup_for_ticker(ticker)

    return {
        "company": company,
        "signals": signals,
        "briefs": briefs,
        "signal_count": len(signals),
        "suggested_action": trade_setup,
    }


# ── Trade Setups (pre-computed per ticker) ────────────────────────────────────


def _compute_trade_setup(ticker: str) -> dict | None:
    """Compute a trade setup using the shared scorer logic."""
    signal_dicts = get_signals(ticker=ticker)
    if not signal_dicts:
        return None

    signal_models = [_seed_signal_to_model(signal) for signal in signal_dicts]
    attach_historical_signal_stats(signal_models)

    company = get_company(ticker)
    company_profile = None
    if company:
        company_profile = CompanyProfile(
            name=company["name"],
            ticker=company["ticker"],
            sector=company["sector"],
            industry=company["industry"],
        )

    insight = FusedInsight(
        ticker=ticker.upper(),
        company_name=company["name"] if company else ticker.upper(),
        signals=signal_models,
        company_profile=company_profile,
        sentiment=_seed_sentiment(signal_models),
    )
    insight.composite_score = score_insight(insight)
    insight.suggested_action = suggest_action(insight)
    return _serialize_trade_setup(insight.suggested_action)


def get_trade_setup_for_ticker(ticker: str) -> dict | None:
    """Get or compute the trade setup for a ticker."""
    return _compute_trade_setup(ticker.upper())


def _decorate_signal(signal: dict) -> dict:
    """Attach derived historical stats to a seed signal response."""
    enriched = dict(signal)
    stats = SIGNAL_HISTORICAL_STATS.get(enriched["type"])
    enriched["historical_win_rate"] = stats["win_rate"] if stats else None
    enriched["historical_avg_return"] = stats["avg_return_3m"] if stats else None
    enriched["historical_sample_size"] = int(stats["sample_size"]) if stats else None
    return enriched


def _seed_signal_to_model(signal: dict) -> Signal:
    """Convert a seed signal dict into the shared Signal model."""
    return Signal(
        id=signal["id"],
        type=SignalType(signal["type"]),
        strength=SignalStrength(signal["strength"]),
        sentiment=Sentiment(signal["sentiment"]),
        ticker=signal["ticker"],
        company_name=signal["company_name"],
        headline=signal["headline"],
        detail=signal["detail"],
        score=signal["score"],
        data=signal["data"],
        detected_at=datetime.fromisoformat(signal["detected_at"]),
    )


def _seed_sentiment(signals: list[Signal]) -> Sentiment:
    bullish = sum(1 for signal in signals if signal.sentiment == Sentiment.BULLISH)
    bearish = sum(1 for signal in signals if signal.sentiment == Sentiment.BEARISH)
    if bullish > bearish:
        return Sentiment.BULLISH
    if bearish > bullish:
        return Sentiment.BEARISH
    return Sentiment.NEUTRAL


def _serialize_trade_setup(setup) -> dict | None:
    if setup is None:
        return None
    return {
        "action": setup.action.value,
        "time_horizon": setup.time_horizon.value,
        "conviction": setup.conviction,
        "rationale": setup.rationale,
        "risk_note": setup.risk_note,
        "historical_win_rate": setup.historical_win_rate,
        "historical_avg_return": setup.historical_avg_return,
        "historical_sample_size": setup.historical_sample_size,
    }
