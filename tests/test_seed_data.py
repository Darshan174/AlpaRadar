"""Tests for seed data layer."""

import sys
sys.path.insert(0, "src")

from src.seed.data import (
    SIGNALS,
    COMPANIES,
    BRIEFS,
    get_signals,
    get_signal_by_id,
    get_brief_for_signal,
    get_company,
    get_feed,
    get_company_signals,
)


def test_all_signals_have_required_fields():
    required = {"id", "type", "strength", "sentiment", "ticker", "company_name", "headline", "detail", "score", "detected_at"}
    for signal in SIGNALS:
        missing = required - signal.keys()
        assert not missing, f"Signal {signal['id']} missing fields: {missing}"


def test_all_signals_have_evidence():
    for signal in SIGNALS:
        assert "evidence" in signal, f"Signal {signal['id']} missing evidence"
        assert len(signal["evidence"]) > 0, f"Signal {signal['id']} has empty evidence"


def test_evidence_has_required_fields():
    required = {"type", "title", "source", "timestamp"}
    for signal in SIGNALS:
        for ev in signal.get("evidence", []):
            missing = required - ev.keys()
            assert not missing, f"Evidence in signal {signal['id']} missing: {missing}"


def test_all_signals_have_briefs():
    for signal in SIGNALS:
        brief = get_brief_for_signal(signal["id"])
        assert brief is not None, f"No brief for signal {signal['id']}"
        assert "sections" in brief
        assert "what_happened" in brief["sections"]
        assert "risks" in brief["sections"]


def test_signal_types_are_valid():
    valid_types = {"hiring_surge", "executive_move", "growth_price_divergence", "competitor_shift", "sector_pulse"}
    for signal in SIGNALS:
        assert signal["type"] in valid_types, f"Invalid type: {signal['type']}"


def test_signal_scores_in_range():
    for signal in SIGNALS:
        assert 0 <= signal["score"] <= 100, f"Score out of range: {signal['score']}"


def test_get_signals_filter_by_ticker():
    nvda = get_signals(ticker="NVDA")
    assert all(s["ticker"] == "NVDA" for s in nvda)
    assert len(nvda) >= 2


def test_get_signals_filter_by_type():
    hiring = get_signals(signal_type="hiring_surge")
    assert all(s["type"] == "hiring_surge" for s in hiring)


def test_get_signals_filter_by_min_score():
    high = get_signals(min_score=80)
    assert all(s["score"] >= 80 for s in high)


def test_get_signals_sorted_by_detected_at():
    signals = get_signals()
    dates = [s["detected_at"] for s in signals]
    assert dates == sorted(dates, reverse=True)


def test_get_signal_by_id():
    signal = SIGNALS[0]
    result = get_signal_by_id(signal["id"])
    assert result is not None
    assert result["id"] == signal["id"]


def test_get_signal_by_id_not_found():
    result = get_signal_by_id("nonexistent")
    assert result is None


def test_get_company():
    nvda = get_company("NVDA")
    assert nvda is not None
    assert nvda["name"] == "NVIDIA Corporation"


def test_get_company_case_insensitive():
    nvda = get_company("nvda")
    assert nvda is not None


def test_get_feed_pagination():
    feed = get_feed(limit=5, offset=0)
    assert len(feed["signals"]) <= 5
    assert feed["total"] == len(SIGNALS)


def test_get_company_signals():
    result = get_company_signals("NVDA")
    assert result["company"] is not None
    assert len(result["signals"]) >= 1
    assert result["signal_count"] == len(result["signals"])


def test_companies_have_required_fields():
    required = {"ticker", "name", "sector", "industry", "market_cap"}
    for company in COMPANIES:
        missing = required - company.keys()
        assert not missing, f"Company {company['ticker']} missing: {missing}"
