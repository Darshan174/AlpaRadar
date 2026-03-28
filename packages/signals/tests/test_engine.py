"""Tests for the Signal Engine orchestrator."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.signals.config import SignalEngineConfig
from packages.signals.engine import run_all, run_universe
from packages.signals.models import (
    InsiderTransaction,
    JobPostingSnapshot,
    MaterialFiling,
    TranscriptSentiment,
)


AS_OF = datetime(2025, 10, 1)


def _make_insider_cluster(ticker: str = "TEST") -> list[InsiderTransaction]:
    return [
        InsiderTransaction(
            filing_date=AS_OF - timedelta(days=i * 5),
            ticker=ticker,
            company_name="Test Corp",
            insider_name=f"Person{i}",
            insider_title="VP",
            transaction_type="P",
            shares=1000,
            price_per_share=200.0,
        )
        for i in range(4)
    ]


def _make_job_spike(ticker: str = "TEST") -> list[JobPostingSnapshot]:
    baseline = [
        JobPostingSnapshot(
            date=AS_OF - timedelta(days=d),
            ticker=ticker,
            company_name="Test Corp",
            total_postings=100,
            engineering_postings=40,
        )
        for d in [60, 45, 30]
    ]
    spike = JobPostingSnapshot(
        date=AS_OF,
        ticker=ticker,
        company_name="Test Corp",
        total_postings=250,
        engineering_postings=120,
    )
    return baseline + [spike]


def _make_material_event(ticker: str = "TEST") -> list[MaterialFiling]:
    return [
        MaterialFiling(
            filing_date=AS_OF - timedelta(days=5),
            ticker=ticker,
            company_name="Test Corp",
            items=["5.02", "2.06"],
        )
    ]


def _make_transcripts(ticker: str = "TEST") -> list[TranscriptSentiment]:
    return [
        TranscriptSentiment(
            date=AS_OF - timedelta(days=90),
            ticker=ticker,
            company_name="Test Corp",
            quarter="Q2 2025",
            overall_sentiment=0.3,
            guidance_sentiment=0.2,
            positive_keyword_hits=12,
            negative_keyword_hits=5,
            risk_keyword_hits=2,
        ),
        TranscriptSentiment(
            date=AS_OF,
            ticker=ticker,
            company_name="Test Corp",
            quarter="Q3 2025",
            overall_sentiment=-0.3,
            guidance_sentiment=-0.5,
            positive_keyword_hits=3,
            negative_keyword_hits=18,
            risk_keyword_hits=9,
        ),
    ]


class TestRunAll:
    def test_runs_all_detectors(self):
        signals = run_all(
            ticker="TEST",
            company_name="Test Corp",
            insider_transactions=_make_insider_cluster(),
            job_snapshots=_make_job_spike(),
            filings=_make_material_event(),
            transcripts=_make_transcripts(),
            as_of=AS_OF,
        )
        types = {s["type"] for s in signals}
        assert "insider_buy_cluster" in types
        assert "hiring_momentum" in types
        assert "material_event" in types

    def test_returns_empty_with_no_data(self):
        signals = run_all(ticker="TEST", as_of=AS_OF)
        assert signals == []

    def test_runs_only_available_data(self):
        signals = run_all(
            ticker="TEST",
            insider_transactions=_make_insider_cluster(),
            as_of=AS_OF,
        )
        assert len(signals) == 1
        assert signals[0]["type"] == "insider_buy_cluster"

    def test_all_signals_have_required_fields(self):
        signals = run_all(
            ticker="TEST",
            company_name="Test Corp",
            insider_transactions=_make_insider_cluster(),
            job_snapshots=_make_job_spike(),
            filings=_make_material_event(),
            as_of=AS_OF,
        )
        required = {"id", "type", "strength", "sentiment", "ticker", "headline", "detail", "score", "data", "detected_at"}
        for sig in signals:
            assert required.issubset(sig.keys()), f"Missing fields: {required - sig.keys()}"

    def test_custom_config_propagates(self):
        cfg = SignalEngineConfig()
        cfg.insider_cluster.min_insiders = 10  # Impossible threshold
        signals = run_all(
            ticker="TEST",
            insider_transactions=_make_insider_cluster(),
            as_of=AS_OF,
            config=cfg,
        )
        # Insider signal should not fire with min_insiders=10
        insider_signals = [s for s in signals if s["type"] == "insider_buy_cluster"]
        assert len(insider_signals) == 0


class TestRunUniverse:
    def test_runs_across_multiple_tickers(self):
        universe = {
            "AAPL": {
                "company_name": "Apple Inc.",
                "insider_transactions": _make_insider_cluster("AAPL"),
            },
            "TSLA": {
                "company_name": "Tesla Inc.",
                "job_snapshots": _make_job_spike("TSLA"),
            },
        }
        results = run_universe(universe, as_of=AS_OF)
        assert "AAPL" in results
        assert "TSLA" in results
        assert results["AAPL"][0]["type"] == "insider_buy_cluster"
        assert results["TSLA"][0]["type"] == "hiring_momentum"

    def test_skips_tickers_with_no_signals(self):
        universe = {
            "AAPL": {
                "company_name": "Apple Inc.",
                "insider_transactions": _make_insider_cluster("AAPL"),
            },
            "BORING": {
                "company_name": "Nothing Corp",
                # No data at all
            },
        }
        results = run_universe(universe, as_of=AS_OF)
        assert "AAPL" in results
        assert "BORING" not in results

    def test_empty_universe(self):
        results = run_universe({}, as_of=AS_OF)
        assert results == {}
