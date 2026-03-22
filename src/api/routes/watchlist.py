"""Watchlist routes — add/remove tickers, get alerts."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.schemas import WatchlistAddRequest, WatchlistResponse
from src.core.models import SignalType, WatchlistItem
from src.logging_config import get_logger
from src.storage import supabase as db

log = get_logger(__name__)

router = APIRouter(prefix="/v1/watchlist", tags=["watchlist"])


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    user_id: str = Query(..., description="User identifier"),
):
    """Get user's watchlist."""
    items = await db.get_watchlist(user_id)
    return WatchlistResponse(items=items)


@router.post("")
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """Add a ticker to the watchlist with alert preferences."""
    alert_types = []
    for t in request.alert_on:
        try:
            alert_types.append(SignalType(t))
        except ValueError:
            pass

    item = WatchlistItem(
        user_id=user_id,
        ticker=request.ticker.upper(),
        company_name=request.company_name,
        alert_on=alert_types or list(SignalType),
    )
    await db.add_to_watchlist(item)
    return {"status": "added", "ticker": item.ticker}


@router.delete("/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    user_id: str = Query(..., description="User identifier"),
):
    """Remove a ticker from the watchlist."""
    await db.remove_from_watchlist(user_id, ticker.upper())
    return {"status": "removed", "ticker": ticker.upper()}
