"""Tests for the Insider Buy Cluster detector."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.signals.config import InsiderClusterConfig
from packages.signals.detectors.insider_cluster import detect
from packages.signals.models import InsiderTransaction


def _txn(
    name: str,
    title: str = "VP",
    txn_type: str = "P",
    shares: float = 1000,
    price: float = 100.0,
    days_ago: int = 10,
    ticker: str = "TEST",
) -> InsiderTransaction:
    return InsiderTransaction(
        filing_date=datetime(2025, 10, 1) - timedelta(days=days_ago),
        ticker=ticker,
        company_name="Test Corp",
        insider_name=name,
        insider_title=title,
        transaction_type=txn_type,
        shares=shares,
        price_per_share=price,
    )


AS_OF = datetime(2025, 10, 1)


class TestInsiderClusterDetection:
    def test_fires_on_valid_cluster(self):
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200),
            _txn("Bob", days_ago=10, shares=300, price=200),
            _txn("Carol", days_ago=15, shares=400, price=200),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert result["type"] == "insider_buy_cluster"
        assert result["sentiment"] == "bullish"
        assert result["ticker"] == "TEST"
        assert result["score"] > 0

    def test_returns_none_below_min_insiders(self):
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200),
            _txn("Bob", days_ago=10, shares=300, price=200),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_returns_none_below_min_value(self):
        txns = [
            _txn("Alice", days_ago=5, shares=10, price=1),
            _txn("Bob", days_ago=10, shares=10, price=1),
            _txn("Carol", days_ago=15, shares=10, price=1),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_returns_none_when_sells_dominate(self):
        txns = [
            _txn("Alice", days_ago=5, shares=100, price=200),
            _txn("Bob", days_ago=10, shares=100, price=200),
            _txn("Carol", days_ago=15, shares=100, price=200),
            # Massive sell drowns buy/sell ratio
            _txn("Dan", txn_type="S", days_ago=8, shares=10000, price=200),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_ignores_transactions_outside_window(self):
        cfg = InsiderClusterConfig(window_days=30)
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200),
            _txn("Bob", days_ago=10, shares=300, price=200),
            _txn("Carol", days_ago=60, shares=400, price=200),  # Outside 30d window
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF, config=cfg)
        assert result is None  # Only 2 insiders in window

    def test_ignores_wrong_ticker(self):
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200, ticker="OTHER"),
            _txn("Bob", days_ago=10, shares=300, price=200, ticker="OTHER"),
            _txn("Carol", days_ago=15, shares=400, price=200, ticker="OTHER"),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_strong_signal_with_many_insiders(self):
        txns = [
            _txn(f"Person{i}", days_ago=i * 5, shares=2000, price=250)
            for i in range(6)
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert result["strength"] in ("strong", "moderate")
        assert result["score"] >= 60

    def test_evidence_contains_all_buyers(self):
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200),
            _txn("Bob", days_ago=10, shares=300, price=200),
            _txn("Carol", days_ago=15, shares=400, price=200),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        evidence = result["data"]["evidence"]
        assert len(evidence) == 3
        names = {e["insider_name"] for e in evidence}
        assert names == {"Alice", "Bob", "Carol"}

    def test_multiple_buys_same_insider_counted_once(self):
        txns = [
            _txn("Alice", days_ago=5, shares=500, price=200),
            _txn("Alice", days_ago=8, shares=300, price=200),  # Same person
            _txn("Bob", days_ago=10, shares=300, price=200),
            _txn("Carol", days_ago=15, shares=400, price=200),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert result["data"]["num_unique_insiders"] == 3

    def test_empty_transactions(self):
        result = detect([], "TEST", "Test Corp", as_of=AS_OF)
        assert result is None

    def test_score_bounded_0_100(self):
        txns = [
            _txn(f"P{i}", days_ago=1, shares=100000, price=500)
            for i in range(10)
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF)
        assert result is not None
        assert 0 <= result["score"] <= 100

    def test_custom_config_thresholds(self):
        cfg = InsiderClusterConfig(min_insiders=2, min_total_value_usd=50)
        txns = [
            _txn("Alice", days_ago=5, shares=10, price=100),
            _txn("Bob", days_ago=10, shares=10, price=100),
        ]
        result = detect(txns, "TEST", "Test Corp", as_of=AS_OF, config=cfg)
        assert result is not None
