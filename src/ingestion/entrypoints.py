"""High-level ingestion entrypoints for schedulers and API routes.

These functions orchestrate the collector modules and are designed to be
called by cron jobs, API endpoints, or the background scheduler.
"""

from __future__ import annotations

from typing import Any

from src.logging_config import get_logger

from .base import NormalizedRecord
from .jobs.provider import FixtureJobProvider, JobPostingCollector
from .sec.filing8k import Filing8KCollector
from .sec.form4 import Form4Collector
from .transcripts.fmp import TranscriptCollector

log = get_logger(__name__)

# Ticker -> company name mapping for common lookups
# (The SEC CIK lookup provides names, but this helps for job searches)
TICKER_COMPANY_MAP: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PLTR": "Palantir Technologies",
    "SNOW": "Snowflake",
    "SNAP": "Snap",
    "AMD": "Advanced Micro Devices",
    "INTC": "Intel",
    "UBER": "Uber Technologies",
    "LYFT": "Lyft",
    "SQ": "Block",
    "SHOP": "Shopify",
    "ZM": "Zoom Video Communications",
    "CRWD": "CrowdStrike",
}


def _resolve_company_name(ticker: str) -> str:
    return TICKER_COMPANY_MAP.get(ticker.upper(), ticker)


async def sync_sec_activity(
    ticker: str,
    days_back: int = 90,
    max_filings: int = 20,
) -> dict[str, Any]:
    """Ingest SEC Form 4 and 8-K filings for a ticker.

    Returns summary of what was collected.
    """
    log.info("sync_sec_started", ticker=ticker, days_back=days_back)
    results: dict[str, Any] = {"ticker": ticker, "form4": [], "filing_8k": []}

    form4 = Form4Collector()
    filing8k = Filing8KCollector()

    try:
        form4_records = await form4.collect(
            ticker, days_back=days_back, max_filings=max_filings
        )
        results["form4"] = [
            {
                "filer": getattr(r, "filer_name", ""),
                "type": getattr(r, "transaction_type", ""),
                "shares": getattr(r, "shares", 0),
                "date": getattr(r, "transaction_date", ""),
            }
            for r in form4_records
        ]

        filing8k_records = await filing8k.collect(
            ticker, days_back=days_back, max_filings=max_filings
        )
        results["filing_8k"] = [
            {
                "date": getattr(r, "filing_date", ""),
                "items": getattr(r, "items", []),
                "description": getattr(r, "description", ""),
            }
            for r in filing8k_records
        ]
    finally:
        await form4.close()
        await filing8k.close()

    log.info(
        "sync_sec_completed",
        ticker=ticker,
        form4_count=len(results["form4"]),
        filing8k_count=len(results["filing_8k"]),
    )
    return results


async def sync_job_postings(
    ticker: str,
    provider: Any | None = None,
) -> dict[str, Any]:
    """Ingest job posting data for a company.

    Uses SerpAPI if configured, otherwise falls back to fixtures.
    """
    log.info("sync_jobs_started", ticker=ticker)
    company_name = _resolve_company_name(ticker)

    # Try SerpAPI first if available
    if provider is None:
        try:
            from .jobs.serpapi import SerpAPIJobProvider

            serp = SerpAPIJobProvider()
            if serp.is_configured:
                provider = serp
        except Exception:
            pass
        if provider is None:
            provider = FixtureJobProvider()

    collector = JobPostingCollector(provider=provider)
    records = await collector.collect(ticker, company_name=company_name)

    summary = {
        "ticker": ticker,
        "company_name": company_name,
        "total_postings": len(records),
        "engineering": sum(1 for r in records if getattr(r, "is_engineering", False)),
        "sales": sum(1 for r in records if getattr(r, "is_sales", False)),
        "departments": {},
    }

    # Count by department
    dept_counts: dict[str, int] = {}
    for r in records:
        dept = getattr(r, "department", "other")
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    summary["departments"] = dept_counts

    log.info("sync_jobs_completed", ticker=ticker, count=len(records))
    return summary


async def sync_transcripts(
    ticker: str,
    limit: int = 2,
) -> dict[str, Any]:
    """Ingest earnings call transcripts for a ticker.

    Uses FMP API if configured, otherwise falls back to fixtures.
    """
    log.info("sync_transcripts_started", ticker=ticker)

    collector = TranscriptCollector()
    records = await collector.collect(ticker, limit=limit)

    summary = {
        "ticker": ticker,
        "chunks": len(records),
        "quarters": list({getattr(r, "quarter", "") for r in records if getattr(r, "quarter", "")}),
    }

    log.info("sync_transcripts_completed", ticker=ticker, chunks=len(records))
    return summary


async def sync_company_alt_data(
    ticker: str,
    include_sec: bool = True,
    include_jobs: bool = True,
    include_transcripts: bool = True,
    days_back: int = 90,
) -> dict[str, Any]:
    """Full alternative data ingestion for a single company.

    Orchestrates all collectors and returns a combined summary.
    This is the main entrypoint for scheduled ingestion.
    """
    log.info("sync_alt_data_started", ticker=ticker)
    results: dict[str, Any] = {"ticker": ticker, "sec": {}, "jobs": {}, "transcripts": {}}

    if include_sec:
        try:
            results["sec"] = await sync_sec_activity(ticker, days_back=days_back)
        except Exception as e:
            log.error("sync_sec_failed", ticker=ticker, error=str(e))
            results["sec"] = {"error": str(e)}

    if include_jobs:
        try:
            results["jobs"] = await sync_job_postings(ticker)
        except Exception as e:
            log.error("sync_jobs_failed", ticker=ticker, error=str(e))
            results["jobs"] = {"error": str(e)}

    if include_transcripts:
        try:
            results["transcripts"] = await sync_transcripts(ticker)
        except Exception as e:
            log.error("sync_transcripts_failed", ticker=ticker, error=str(e))
            results["transcripts"] = {"error": str(e)}

    log.info("sync_alt_data_completed", ticker=ticker)
    return results


async def sync_universe(
    tickers: list[str],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Run full alt-data sync across a list of tickers.

    Processes sequentially to respect rate limits.
    """
    log.info("sync_universe_started", count=len(tickers))
    results = []

    for ticker in tickers:
        try:
            result = await sync_company_alt_data(ticker, **kwargs)
            results.append(result)
        except Exception as e:
            log.error("sync_universe_ticker_failed", ticker=ticker, error=str(e))
            results.append({"ticker": ticker, "error": str(e)})

    log.info("sync_universe_completed", total=len(results))
    return results
