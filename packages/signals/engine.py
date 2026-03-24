"""Signal Engine — orchestrates all MVP detectors.

Runs the three core detectors on normalized input data and produces
signal records ready for insertion into the `signals` table.

Architecture contract:
- Reads normalized records (InsiderTransaction, JobPostingSnapshot, etc.)
- Writes signal dicts compatible with the signals table schema
- Each signal includes type, severity, why it fired, evidence, and timestamp
"""

from __future__ import annotations

from datetime import datetime

from packages.signals.config import SignalEngineConfig, default_config
from packages.signals.detectors import insider_cluster, hiring_momentum, material_event
from packages.signals.models import (
    InsiderTransaction,
    JobPostingSnapshot,
    MaterialFiling,
    TranscriptSentiment,
)


def run_all(
    ticker: str,
    company_name: str = "",
    insider_transactions: list[InsiderTransaction] | None = None,
    job_snapshots: list[JobPostingSnapshot] | None = None,
    filings: list[MaterialFiling] | None = None,
    transcripts: list[TranscriptSentiment] | None = None,
    as_of: datetime | None = None,
    config: SignalEngineConfig | None = None,
) -> list[dict]:
    """Run all signal detectors for a single ticker.

    Args:
        ticker: Stock ticker symbol.
        company_name: Human-readable company name.
        insider_transactions: SEC Form 4 data.
        job_snapshots: Job posting time-series.
        filings: 8-K filings.
        transcripts: Earnings transcript sentiment records.
        as_of: Reference date for all detectors.
        config: Override all thresholds.

    Returns:
        List of signal dicts (may be empty). Each dict matches the
        signals table schema with full evidence payloads.
    """
    cfg = config or default_config
    as_of = as_of or datetime.utcnow()
    signals: list[dict] = []

    # 1. Insider Buy Cluster
    if insider_transactions:
        result = insider_cluster.detect(
            transactions=insider_transactions,
            ticker=ticker,
            company_name=company_name,
            as_of=as_of,
            config=cfg.insider_cluster,
        )
        if result:
            signals.append(result)

    # 2. Hiring Momentum
    if job_snapshots:
        result = hiring_momentum.detect(
            snapshots=job_snapshots,
            ticker=ticker,
            company_name=company_name,
            as_of=as_of,
            config=cfg.hiring_momentum,
        )
        if result:
            signals.append(result)

    # 3. Material Events (may return multiple signals)
    if filings or transcripts:
        results = material_event.detect(
            filings=filings,
            transcripts=transcripts,
            ticker=ticker,
            company_name=company_name,
            as_of=as_of,
            config=cfg.material_event,
        )
        signals.extend(results)

    return signals


def run_universe(
    tickers: dict[str, dict],
    as_of: datetime | None = None,
    config: SignalEngineConfig | None = None,
) -> dict[str, list[dict]]:
    """Run all detectors across a universe of tickers.

    Args:
        tickers: Mapping of ticker -> data dict with keys:
            - company_name (str)
            - insider_transactions (list[InsiderTransaction])
            - job_snapshots (list[JobPostingSnapshot])
            - filings (list[MaterialFiling])
            - transcripts (list[TranscriptSentiment])
        as_of: Reference date.
        config: Override thresholds.

    Returns:
        Mapping of ticker -> list of signal dicts.
    """
    cfg = config or default_config
    as_of = as_of or datetime.utcnow()
    results: dict[str, list[dict]] = {}

    for ticker, data in tickers.items():
        signals = run_all(
            ticker=ticker,
            company_name=data.get("company_name", ""),
            insider_transactions=data.get("insider_transactions"),
            job_snapshots=data.get("job_snapshots"),
            filings=data.get("filings"),
            transcripts=data.get("transcripts"),
            as_of=as_of,
            config=cfg,
        )
        if signals:
            results[ticker] = signals

    return results
