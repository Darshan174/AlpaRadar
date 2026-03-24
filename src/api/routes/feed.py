"""Feed and detail routes — signal feed, signal detail, briefs.

Uses seed data when Supabase is unavailable (MVP mode).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.briefing.service import generate_brief
from src.logging_config import get_logger
from src.seed.data import (
    get_brief_for_signal,
    get_company,
    get_company_signals,
    get_feed,
    get_signal_by_id,
    get_signals,
    COMPANIES,
)

log = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["feed"])


# ── Signal Feed ───────────────────────────────────────────────────────────────


@router.get("/feed")
async def signal_feed(
    ticker: str | None = Query(None, description="Filter by ticker"),
    type: str | None = Query(None, description="Filter by signal type"),
    min_score: float = Query(0, ge=0, le=100),
    date_from: str | None = Query(None, description="ISO date string lower bound"),
    date_to: str | None = Query(None, description="ISO date string upper bound"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Paginated signal feed with filters."""
    if ticker or type or min_score > 0 or date_from or date_to:
        signals = get_signals(
            ticker=ticker,
            signal_type=type,
            min_score=min_score,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )
        return {"signals": signals, "total": len(signals), "limit": limit, "offset": offset}

    return get_feed(limit=limit, offset=offset)


# ── Signal Detail ─────────────────────────────────────────────────────────────


@router.get("/signal/{signal_id}")
async def signal_detail(signal_id: str):
    """Get full signal detail with evidence and brief."""
    signal = get_signal_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    brief = get_brief_for_signal(signal_id)

    return {
        "signal": signal,
        "brief": brief,
        "company": get_company(signal["ticker"]),
    }


# ── Brief Generation ─────────────────────────────────────────────────────────


@router.post("/signal/{signal_id}/brief")
async def generate_signal_brief(
    signal_id: str,
    prompt_version: str = Query("v1", description="Prompt version to use"),
):
    """Generate (or regenerate) an AI brief for a signal."""
    signal = get_signal_by_id(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    brief = await generate_brief(signal, prompt_version=prompt_version)
    return brief


# ── Company Detail ────────────────────────────────────────────────────────────


@router.get("/company/{ticker}")
async def company_detail(ticker: str):
    """Get company data with all associated signals and briefs."""
    ticker = ticker.upper()
    result = get_company_signals(ticker)

    if not result["company"]:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found in tracked universe")

    return result


# ── Company List ──────────────────────────────────────────────────────────────


@router.get("/companies")
async def list_companies():
    """List all tracked companies."""
    return {"companies": COMPANIES, "total": len(COMPANIES)}
