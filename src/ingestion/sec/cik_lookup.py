"""CIK resolution from SEC EDGAR company_tickers.json.

SEC provides a free JSON file mapping tickers to CIK numbers.
No API key required. Rate limit: 10 req/s with User-Agent header.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from src.logging_config import get_logger

log = get_logger(__name__)

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_USER_AGENT = "AlphaRadar research@alpharadar.dev"

# Cache ticker->CIK mapping in memory after first load
_ticker_cik_cache: dict[str, dict[str, Any]] | None = None

# Path for fixture fallback
FIXTURE_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "sec" / "company_tickers.json"


async def _fetch_tickers_json() -> dict[str, dict[str, Any]]:
    """Fetch the SEC company tickers mapping."""
    global _ticker_cik_cache
    if _ticker_cik_cache is not None:
        return _ticker_cik_cache

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                COMPANY_TICKERS_URL,
                headers={"User-Agent": SEC_USER_AGENT},
            )
            resp.raise_for_status()
            raw = resp.json()
    except Exception as e:
        log.warning("sec_tickers_fetch_failed_using_fixture", error=str(e))
        if FIXTURE_PATH.exists():
            raw = json.loads(FIXTURE_PATH.read_text())
        else:
            raise

    # Raw format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    mapping: dict[str, dict[str, Any]] = {}
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).upper()
        if ticker:
            mapping[ticker] = {
                "cik": str(entry["cik_str"]),
                "cik_padded": str(entry["cik_str"]).zfill(10),
                "ticker": ticker,
                "company_name": entry.get("title", ""),
            }

    _ticker_cik_cache = mapping
    log.info("sec_tickers_loaded", count=len(mapping))
    return mapping


async def lookup_cik(ticker: str) -> dict[str, Any] | None:
    """Resolve a ticker to its CIK info.

    Returns dict with keys: cik, cik_padded, ticker, company_name
    or None if ticker not found.
    """
    mapping = await _fetch_tickers_json()
    result = mapping.get(ticker.upper())
    if result:
        log.debug("cik_resolved", ticker=ticker, cik=result["cik"])
    else:
        log.warning("cik_not_found", ticker=ticker)
    return result


async def lookup_cik_batch(tickers: list[str]) -> dict[str, dict[str, Any]]:
    """Resolve multiple tickers to CIK info."""
    mapping = await _fetch_tickers_json()
    results = {}
    for ticker in tickers:
        info = mapping.get(ticker.upper())
        if info:
            results[ticker.upper()] = info
    return results


def clear_cache() -> None:
    """Clear the cached ticker mapping (for testing)."""
    global _ticker_cik_cache
    _ticker_cik_cache = None
