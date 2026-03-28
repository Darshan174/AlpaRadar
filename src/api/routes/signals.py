"""Signal discovery and retrieval routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.schemas import SignalResponse
from src.intelligence.scorer import get_signal_historical_stats
from src.storage import supabase as db

router = APIRouter(prefix="/v1/signals", tags=["signals"])


@router.get("", response_model=list[SignalResponse])
async def list_signals(
    ticker: str | None = Query(None, description="Filter by ticker symbol"),
    type: str | None = Query(None, description="Filter by signal type"),
    min_score: float = Query(0, ge=0, le=100, description="Minimum signal score"),
    limit: int = Query(50, ge=1, le=200),
):
    """List recent signals with optional filters."""
    rows = await db.get_signals(
        ticker=ticker,
        signal_type=type,
        min_score=min_score,
        limit=limit,
    )
    return [_hydrate_signal_row(row) for row in rows]


@router.get("/search")
async def search_signals(
    q: str = Query(..., description="Natural language search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Semantic search over signals using RAG."""
    results = await db.search_similar_signals(q, limit=limit)
    return {"query": q, "results": results}


def _hydrate_signal_row(row: dict) -> dict:
    enriched = dict(row)
    stats = get_signal_historical_stats(enriched["type"])
    if not stats:
        return enriched
    enriched["historical_win_rate"] = stats["win_rate"]
    enriched["historical_avg_return"] = stats["avg_return_3m"]
    enriched["historical_sample_size"] = int(stats["sample_size"])
    return enriched
