"""Tests for the Hiring Momentum Spike detector."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.signals.config import HiringMomentumConfig
from packages.signals.detectors.hiring_momentum import detect
from packages.signals.models import JobPostingSnapshot


def _snap(
    days_ago: int,
    total: int,
    eng: int = 0,
    sales: int = 0,
    ticker: str = "TEST",
) -> JobPostingSnapshot:
    return JobPostingSnapshot(
        date=datetime(2025, 10, 1) - timedelta(days=days_ago),
        ticker=ticker,
        company_name="Test Corp",
        total_postings=total,
        engineering_postings=eng,
        sales_postings=sales,
        department_breakdown={"engineering": eng, "sales": sales},
    )


AS_OF = datetime(2025, 10, 1)


class TestHiringMomentumDetection:
    def test_fires_on_clear_spike(self):
        snaps = [
            _snap(60, 100, 40, 30),
            _snap(45, 105, 42, 32),
            _snap(30, 100, 40, 30),
            _snap(15, 110, 44, 33),
            _snap(0, 200, 90, 50),  # 2x spike
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert result["type"] == "hiring_momentum"
        assert result["sentiment"] == "bullish"
        assert result["data"]["total_spike_ratio"] >= 1.5

    def test_returns_none_flat_postings(self):
        snaps = [
            _snap(60, 100, 40, 30),
            _snap(45, 102, 41, 30),
            _snap(30, 99, 40, 29),
            _snap(15, 101, 40, 30),
            _snap(0, 103, 41, 31),
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_returns_none_below_min_posting_count(self):
        snaps = [
            _snap(60, 3, 2, 1),
            _snap(45, 3, 2, 1),
            _snap(30, 3, 2, 1),
            _snap(0, 8, 5, 3),  # 2.7x but only 8 postings
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_returns_none_insufficient_data(self):
        snaps = [_snap(0, 200, 80, 50)]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_strong_signal_on_large_spike(self):
        cfg = HiringMomentumConfig(strong_spike_ratio=2.5)
        snaps = [
            _snap(60, 100, 40, 30),
            _snap(45, 100, 40, 30),
            _snap(30, 100, 40, 30),
            _snap(0, 300, 140, 70),  # 3x spike
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF, config=cfg)
        assert result is not None
        assert result["strength"] == "strong"

    def test_engineering_boost_increases_score(self):
        # Same total spike, but one has engineering-heavy spike
        base_snaps = [
            _snap(60, 100, 30, 30),
            _snap(45, 100, 30, 30),
            _snap(30, 100, 30, 30),
        ]
        # Spike with engineering boost
        eng_heavy = base_snaps + [_snap(0, 170, 90, 40)]
        # Spike without engineering
        eng_flat = base_snaps + [_snap(0, 170, 30, 70)]

        result_eng = detect(eng_heavy, "TEST", "Test Corp", as_of=AS_OF)
        result_flat = detect(eng_flat, "TEST", "Test Corp", as_of=AS_OF)

        assert result_eng is not None
        assert result_flat is not None
        assert result_eng["score"] > result_flat["score"]

    def test_ignores_wrong_ticker(self):
        snaps = [
            _snap(60, 100, 40, 30, ticker="OTHER"),
            _snap(45, 100, 40, 30, ticker="OTHER"),
            _snap(30, 100, 40, 30, ticker="OTHER"),
            _snap(0, 300, 140, 70, ticker="OTHER"),
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_evidence_contains_trend(self):
        snaps = [
            _snap(60, 100, 40, 30),
            _snap(45, 105, 42, 32),
            _snap(30, 100, 40, 30),
            _snap(0, 200, 90, 50),
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert "evidence" in result["data"]
        assert "trend" in result["data"]["evidence"]
        assert len(result["data"]["evidence"]["trend"]) > 0

    def test_score_bounded_0_100(self):
        snaps = [
            _snap(60, 10, 5, 3),
            _snap(45, 10, 5, 3),
            _snap(30, 10, 5, 3),
            _snap(0, 500, 300, 100),  # Massive spike
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert 0 <= result["score"] <= 100

    def test_custom_config(self):
        cfg = HiringMomentumConfig(min_spike_ratio=3.0)
        snaps = [
            _snap(60, 100, 40, 30),
            _snap(45, 100, 40, 30),
            _snap(30, 100, 40, 30),
            _snap(0, 200, 90, 50),  # 2x — below 3.0 threshold
        ]
        result = detect(snaps, "TEST", "Test Corp", as_of=AS_OF, config=cfg)
        assert result is None
