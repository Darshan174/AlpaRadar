"""Intelligence routes — analyze tickers, screen sectors, pre-earnings intel."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.analysis.analyzer import analyze_signals
from src.api.schemas import (
    AnalyzeRequest,
    InsightResponse,
    SectorPulseResponse,
    SectorScreenRequest,
    SignalResponse,
)
from src.core.models import FusedInsight, Signal
from src.ingestion.crustdata.client import CrustdataClient
from src.ingestion.crustdata.transforms import to_company_profile, to_executive_profile
from src.ingestion.market.price import fetch_market_data, ticker_to_domain
from src.intelligence.fusion import generate_insight, generate_sector_insight
from src.intelligence.scorer import score_insight
from src.logging_config import get_logger
from src.storage import supabase as db

log = get_logger(__name__)

router = APIRouter(prefix="/v1/analyze", tags=["intelligence"])


@router.post("", response_model=InsightResponse)
async def analyze_ticker(request: AnalyzeRequest):
    """Full alternative data analysis for a ticker.

    Pipeline:
    1. Fetch market data (yfinance — free)
    2. Enrich company via Crustdata (headcount, hiring, competitors)
    3. Find executives (optional)
    4. Run signal detectors (hiring surge, exec moves, divergence, competitor)
    5. Score and fuse signals
    6. LLM analysis (Groq — free)
    7. Store results
    """
    ticker = request.ticker.upper()

    # 1. Market data
    try:
        market = await fetch_market_data(ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch market data for {ticker}: {e}")

    # 2. Crustdata company enrichment
    domain = ticker_to_domain(ticker)
    company = None
    executives = None
    competitor_profiles = None

    if domain:
        async with CrustdataClient() as crustdata:
            try:
                raw_company = await crustdata.enrich_company(domain=domain)
                company = to_company_profile(raw_company)
                company.ticker = ticker

                # 3. Executives
                if request.include_executives:
                    raw_execs = await crustdata.find_executives(domain)
                    executives = [to_executive_profile(e, ticker) for e in raw_execs]

                # 4. Competitors
                if request.include_competitors and raw_company.company_id:
                    raw_comps = await crustdata.get_company_competitors(raw_company.company_id)
                    competitor_profiles = {}
                    for comp in raw_comps[:5]:
                        try:
                            comp_enriched = await crustdata.enrich_company(domain=comp.domain)
                            competitor_profiles[comp.name] = to_company_profile(comp_enriched)
                        except Exception:
                            pass

            except Exception as e:
                log.warning("crustdata_enrichment_failed", ticker=ticker, error=str(e))

    if not company:
        # Fallback: create minimal company profile from market data
        from src.core.models import CompanyProfile

        company = CompanyProfile(
            name=market.company_name or ticker,
            ticker=ticker,
            sector=market.sector,
            industry=market.industry,
        )

    # 5. Run signal detection + fusion
    insight = await generate_insight(
        company=company,
        market=market,
        executives=executives,
        competitor_profiles=competitor_profiles,
    )

    # 6. Score
    insight.composite_score = score_insight(insight)

    # 7. LLM analysis
    if insight.signals:
        try:
            insight.llm_analysis = await analyze_signals(insight)
            insight.summary = insight.llm_analysis[:300]
        except Exception as e:
            log.warning("llm_analysis_failed", ticker=ticker, error=str(e))
            insight.summary = f"{len(insight.signals)} signals detected for {ticker}"

    # 8. Store
    try:
        await db.store_insight(insight)
        for signal in insight.signals:
            await db.store_signal(signal)
        if company:
            await db.store_company_profile(company)
    except Exception as e:
        log.warning("storage_failed", ticker=ticker, error=str(e))

    return _to_insight_response(insight)


@router.post("/sector", response_model=SectorPulseResponse)
async def analyze_sector(request: SectorScreenRequest):
    """Analyze sector-wide alternative data pulse."""
    from src.core.models import CompanyProfile

    async with CrustdataClient() as crustdata:
        try:
            search_result = await crustdata.search_companies(
                industry=request.sector,
                country=request.country,
                min_headcount_growth_pct=request.min_headcount_growth_pct,
                limit=request.limit,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Crustdata search failed: {e}")

        companies = []
        for comp in search_result.results:
            try:
                raw = await crustdata.enrich_company(domain=comp.domain)
                companies.append(to_company_profile(raw))
            except Exception:
                pass

    signal = await generate_sector_insight(companies, request.sector)

    return SectorPulseResponse(
        sector=request.sector,
        signal=_to_signal_response(signal) if signal else None,
        companies_tracked=len(companies),
    )


def _to_insight_response(insight: FusedInsight) -> InsightResponse:
    return InsightResponse(
        ticker=insight.ticker,
        company_name=insight.company_name,
        composite_score=insight.composite_score,
        sentiment=insight.sentiment.value,
        signal_count=insight.signal_count,
        signals=[_to_signal_response(s) for s in insight.signals],
        llm_analysis=insight.llm_analysis,
        summary=insight.summary,
        generated_at=insight.generated_at,
    )


def _to_signal_response(signal: Signal) -> SignalResponse:
    return SignalResponse(
        id=signal.id,
        type=signal.type.value,
        strength=signal.strength.value,
        sentiment=signal.sentiment.value,
        ticker=signal.ticker,
        company_name=signal.company_name,
        headline=signal.headline,
        detail=signal.detail,
        score=signal.score,
        data=signal.data,
        detected_at=signal.detected_at,
    )
