"""Backtest / Evaluation harness for the signal engine.

Loads historical fixture data, runs all detectors, and prints a
summary of which signals fired, their scores, and evidence.

Usage:
    python3 -m packages.signals.backtests.run_backtest
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.signals.config import default_config
from packages.signals.detectors import insider_cluster, hiring_momentum, material_event
from packages.signals.models import (
    InsiderTransaction,
    JobPostingSnapshot,
    MaterialFiling,
    TranscriptSentiment,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_insider_fixtures() -> list[InsiderTransaction]:
    with open(FIXTURES_DIR / "insider_buys.json") as f:
        raw = json.load(f)
    return [InsiderTransaction(**{k: v for k, v in r.items() if k != "_comment"}) for r in raw]


def load_job_fixtures() -> list[JobPostingSnapshot]:
    with open(FIXTURES_DIR / "job_postings.json") as f:
        raw = json.load(f)
    return [JobPostingSnapshot(**{k: v for k, v in r.items() if k != "_comment"}) for r in raw]


def load_material_fixtures() -> tuple[list[MaterialFiling], list[TranscriptSentiment]]:
    with open(FIXTURES_DIR / "material_events.json") as f:
        raw = json.load(f)
    filings = [MaterialFiling(**{k: v for k, v in r.items() if k != "_comment"}) for r in raw["filings"]]
    transcripts = [TranscriptSentiment(**{k: v for k, v in r.items() if k != "_comment"}) for r in raw["transcripts"]]
    return filings, transcripts


def print_signal(sig: dict, indent: int = 2) -> None:
    pad = " " * indent
    print(f"{pad}Signal: {sig['type']}")
    print(f"{pad}  Ticker:    {sig['ticker']}")
    print(f"{pad}  Strength:  {sig['strength']}")
    print(f"{pad}  Sentiment: {sig['sentiment']}")
    print(f"{pad}  Score:     {sig['score']}")
    print(f"{pad}  Headline:  {sig['headline']}")
    print(f"{pad}  Detail:    {sig['detail']}")
    evidence = sig.get("data", {}).get("evidence")
    if evidence:
        if isinstance(evidence, list):
            print(f"{pad}  Evidence rows: {len(evidence)}")
            for i, row in enumerate(evidence[:3]):
                print(f"{pad}    [{i}] {json.dumps(row, default=str)[:120]}")
        elif isinstance(evidence, dict):
            print(f"{pad}  Evidence: {json.dumps(evidence, default=str)[:200]}")
    print()


def run_insider_backtest(transactions: list[InsiderTransaction]) -> list[dict]:
    print("=" * 70)
    print("INSIDER BUY CLUSTER BACKTEST")
    print("=" * 70)

    tickers = sorted(set(t.ticker.upper() for t in transactions))
    signals = []

    for ticker in tickers:
        # Use a reference date after all fixture transactions
        as_of = datetime(2025, 11, 1)
        result = insider_cluster.detect(
            transactions=transactions,
            ticker=ticker,
            company_name=transactions[0].company_name,
            as_of=as_of,
        )
        if result:
            print(f"\n  [HIT] {ticker}")
            print_signal(result)
            signals.append(result)
        else:
            print(f"\n  [---] {ticker}: No cluster detected")

    return signals


def run_hiring_backtest(snapshots: list[JobPostingSnapshot]) -> list[dict]:
    print("\n" + "=" * 70)
    print("HIRING MOMENTUM SPIKE BACKTEST")
    print("=" * 70)

    tickers = sorted(set(s.ticker.upper() for s in snapshots))
    signals = []

    for ticker in tickers:
        ticker_snaps = [s for s in snapshots if s.ticker.upper() == ticker]
        as_of = max(s.date for s in ticker_snaps)
        result = hiring_momentum.detect(
            snapshots=snapshots,
            ticker=ticker,
            company_name=ticker_snaps[0].company_name,
            as_of=as_of,
        )
        if result:
            print(f"\n  [HIT] {ticker}")
            print_signal(result)
            signals.append(result)
        else:
            print(f"\n  [---] {ticker}: No momentum spike detected")

    return signals


def run_material_backtest(
    filings: list[MaterialFiling],
    transcripts: list[TranscriptSentiment],
) -> list[dict]:
    print("\n" + "=" * 70)
    print("MATERIAL EVENT / TONE CHANGE BACKTEST")
    print("=" * 70)

    tickers = sorted(set(
        [f.ticker.upper() for f in filings] + [t.ticker.upper() for t in transcripts]
    ))
    all_signals = []

    for ticker in tickers:
        as_of = datetime(2025, 12, 1)
        ticker_filings = [f for f in filings if f.ticker.upper() == ticker]
        ticker_transcripts = [t for t in transcripts if t.ticker.upper() == ticker]

        results = material_event.detect(
            filings=ticker_filings or None,
            transcripts=ticker_transcripts or None,
            ticker=ticker,
            company_name=(ticker_filings[0].company_name if ticker_filings
                          else ticker_transcripts[0].company_name if ticker_transcripts
                          else ticker),
            as_of=as_of,
        )
        if results:
            print(f"\n  [HIT] {ticker} — {len(results)} signal(s)")
            for sig in results:
                print_signal(sig)
            all_signals.extend(results)
        else:
            print(f"\n  [---] {ticker}: No material events detected")

    return all_signals


def main() -> None:
    print("\nAlphaRadar Signal Engine — Backtest Report")
    print(f"Config: min_insiders={default_config.insider_cluster.min_insiders}, "
          f"min_spike_ratio={default_config.hiring_momentum.min_spike_ratio}, "
          f"min_sentiment_delta={default_config.material_event.min_sentiment_delta}")
    print(f"Run at: {datetime.utcnow().isoformat()}")

    # Load fixtures
    transactions = load_insider_fixtures()
    snapshots = load_job_fixtures()
    filings, transcripts = load_material_fixtures()

    # Run backtests
    insider_signals = run_insider_backtest(transactions)
    hiring_signals = run_hiring_backtest(snapshots)
    material_signals = run_material_backtest(filings, transcripts)

    # Summary
    all_signals = insider_signals + hiring_signals + material_signals
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total signals fired:    {len(all_signals)}")
    print(f"  Insider clusters:       {len(insider_signals)}")
    print(f"  Hiring momentum:        {len(hiring_signals)}")
    print(f"  Material events:        {len(material_signals)}")
    print()

    by_strength = {}
    for s in all_signals:
        by_strength.setdefault(s["strength"], []).append(s)
    for strength in ["strong", "moderate", "weak"]:
        sigs = by_strength.get(strength, [])
        if sigs:
            print(f"  {strength.upper()} signals:")
            for s in sigs:
                print(f"    - [{s['ticker']}] {s['type']}: score={s['score']} {s['sentiment']}")
    print()

    # Expected results check
    expected_hits = {"AAPL", "META", "TSLA", "AMZN", "INTC", "CRM"}
    expected_misses = {"MSFT", "NVDA", "GOOG", "NFLX", "TINY"}
    actual_hits = {s["ticker"] for s in all_signals}
    actual_misses = (set(t.ticker.upper() for t in transactions)
                     | set(s.ticker.upper() for s in snapshots)
                     | set(f.ticker.upper() for f in filings)
                     | set(t.ticker.upper() for t in transcripts)) - actual_hits

    print("  Expected hits matched:  ", expected_hits & actual_hits)
    print("  Expected misses held:   ", expected_misses & actual_misses)
    unexpected_hits = actual_hits - expected_hits
    missed_expected = expected_hits - actual_hits
    if unexpected_hits:
        print(f"  WARNING: Unexpected hits: {unexpected_hits}")
    if missed_expected:
        print(f"  WARNING: Expected but missed: {missed_expected}")
    print()


if __name__ == "__main__":
    main()
