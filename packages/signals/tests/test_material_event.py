"""Tests for the Material Event / Tone Change detector."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.signals.config import MaterialEventConfig
from packages.signals.detectors.material_event import detect
from packages.signals.models import MaterialFiling, TranscriptSentiment


AS_OF = datetime(2025, 10, 15)


def _filing(
    items: list[str],
    days_ago: int = 5,
    ticker: str = "TEST",
    desc: str = "Test filing",
) -> MaterialFiling:
    return MaterialFiling(
        filing_date=AS_OF - timedelta(days=days_ago),
        ticker=ticker,
        company_name="Test Corp",
        items=items,
        description=desc,
    )


def _transcript(
    quarter: str,
    overall: float,
    guidance: float,
    pos_kw: int = 10,
    neg_kw: int = 5,
    risk_kw: int = 2,
    growth_kw: int = 5,
    days_ago: int = 0,
    ticker: str = "TEST",
    phrases: list[str] | None = None,
) -> TranscriptSentiment:
    return TranscriptSentiment(
        date=AS_OF - timedelta(days=days_ago),
        ticker=ticker,
        company_name="Test Corp",
        quarter=quarter,
        overall_sentiment=overall,
        guidance_sentiment=guidance,
        positive_keyword_hits=pos_kw,
        negative_keyword_hits=neg_kw,
        risk_keyword_hits=risk_kw,
        growth_keyword_hits=growth_kw,
        notable_phrases=phrases or [],
    )


class TestMaterialFilingDetection:
    def test_fires_on_high_severity_items(self):
        filings = [_filing(items=["4.01", "2.06"])]  # Auditor change + impairment
        result = detect(filings=filings, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 1
        sig = result[0]
        assert sig["type"] == "material_event"
        assert sig["data"]["sub_type"] == "8k_material_filing"
        assert sig["sentiment"] == "bearish"

    def test_bullish_acquisition(self):
        filings = [_filing(items=["2.01", "1.01"])]  # Acquisition + material agreement
        result = detect(filings=filings, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 1
        assert result[0]["sentiment"] == "bullish"

    def test_returns_empty_on_routine_items(self):
        filings = [_filing(items=["7.01", "9.01"])]  # Reg FD + exhibits only
        result = detect(filings=filings, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 0

    def test_ignores_old_filings(self):
        filings = [_filing(items=["4.01", "2.06"], days_ago=45)]  # >30d ago
        result = detect(filings=filings, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 0

    def test_ignores_wrong_ticker(self):
        filings = [_filing(items=["4.01"], ticker="OTHER")]
        result = detect(filings=filings, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 0

    def test_multiple_filings_increase_score(self):
        single = [_filing(items=["5.02"], days_ago=5)]
        double = [
            _filing(items=["5.02"], days_ago=5),
            _filing(items=["2.05"], days_ago=10),
        ]
        result_single = detect(filings=single, ticker="TEST", as_of=AS_OF)
        result_double = detect(filings=double, ticker="TEST", as_of=AS_OF)
        assert len(result_single) == 1
        assert len(result_double) == 1
        assert result_double[0]["score"] >= result_single[0]["score"]

    def test_evidence_contains_item_descriptions(self):
        filings = [_filing(items=["4.01"])]
        result = detect(filings=filings, ticker="TEST", as_of=AS_OF)
        assert len(result) == 1
        evidence = result[0]["data"]["evidence"]
        assert len(evidence) == 1
        assert "Changes in Certifying Accountant" in str(evidence[0]["item_descriptions"])


class TestToneChangeDetection:
    def test_fires_on_large_negative_shift(self):
        transcripts = [
            _transcript("Q2 2025", overall=0.3, guidance=0.2, days_ago=90),
            _transcript("Q3 2025", overall=-0.2, guidance=-0.4, days_ago=0),
        ]
        result = detect(transcripts=transcripts, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 1
        sig = result[0]
        assert sig["sentiment"] == "bearish"
        assert sig["data"]["sub_type"] == "transcript_tone_change"
        assert sig["data"]["weighted_delta"] < 0

    def test_fires_on_large_positive_shift(self):
        transcripts = [
            _transcript("Q2 2025", overall=0.1, guidance=0.0, days_ago=90),
            _transcript("Q3 2025", overall=0.5, guidance=0.6, days_ago=0),
        ]
        result = detect(transcripts=transcripts, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 1
        assert result[0]["sentiment"] == "bullish"

    def test_returns_empty_on_small_change(self):
        transcripts = [
            _transcript("Q2 2025", overall=0.3, guidance=0.3, days_ago=90),
            _transcript("Q3 2025", overall=0.35, guidance=0.32, days_ago=0),
        ]
        result = detect(transcripts=transcripts, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 0

    def test_returns_empty_on_single_transcript(self):
        transcripts = [_transcript("Q3 2025", overall=0.5, guidance=0.5)]
        result = detect(transcripts=transcripts, ticker="TEST", company_name="Test Corp", as_of=AS_OF)
        assert len(result) == 0

    def test_risk_keyword_spike_boosts_score(self):
        base = [
            _transcript("Q2 2025", overall=0.2, guidance=0.1, risk_kw=2, days_ago=90),
        ]
        # Same delta but one with risk keyword spike
        no_risk = base + [_transcript("Q3 2025", overall=-0.2, guidance=-0.3, risk_kw=2)]
        with_risk = base + [_transcript("Q3 2025", overall=-0.2, guidance=-0.3, risk_kw=8)]

        result_no = detect(transcripts=no_risk, ticker="TEST", as_of=AS_OF)
        result_risk = detect(transcripts=with_risk, ticker="TEST", as_of=AS_OF)
        assert len(result_no) == 1
        assert len(result_risk) == 1
        assert result_risk[0]["score"] > result_no[0]["score"]

    def test_strong_signal_on_large_delta(self):
        cfg = MaterialEventConfig(strong_sentiment_delta=0.50)
        transcripts = [
            _transcript("Q2 2025", overall=0.4, guidance=0.3, days_ago=90),
            _transcript("Q3 2025", overall=-0.3, guidance=-0.5, days_ago=0),
        ]
        result = detect(transcripts=transcripts, ticker="TEST", as_of=AS_OF, config=cfg)
        assert len(result) == 1
        assert result[0]["strength"] == "strong"

    def test_evidence_contains_quarters(self):
        transcripts = [
            _transcript("Q2 2025", overall=0.1, guidance=0.0, days_ago=90),
            _transcript("Q3 2025", overall=0.5, guidance=0.6, days_ago=0,
                        phrases=["record revenue", "strong pipeline"]),
        ]
        result = detect(transcripts=transcripts, ticker="TEST", as_of=AS_OF)
        assert len(result) == 1
        evidence = result[0]["data"]["evidence"]
        assert evidence["current"]["quarter"] == "Q3 2025"
        assert evidence["previous"]["quarter"] == "Q2 2025"
        assert "record revenue" in evidence["current"]["notable_phrases"]


class TestCombinedDetection:
    def test_both_filing_and_tone_fire_together(self):
        filings = [_filing(items=["5.02"], days_ago=5)]
        transcripts = [
            _transcript("Q2 2025", overall=0.3, guidance=0.2, days_ago=90),
            _transcript("Q3 2025", overall=-0.2, guidance=-0.4, days_ago=0),
        ]
        result = detect(
            filings=filings, transcripts=transcripts,
            ticker="TEST", company_name="Test Corp", as_of=AS_OF,
        )
        assert len(result) == 2
        sub_types = {r["data"]["sub_type"] for r in result}
        assert sub_types == {"8k_material_filing", "transcript_tone_change"}

    def test_score_bounded_0_100(self):
        filings = [
            _filing(items=["4.01", "2.06", "5.02", "2.05", "1.02"], days_ago=1),
            _filing(items=["4.02", "2.04", "5.01"], days_ago=2),
        ]
        transcripts = [
            _transcript("Q2 2025", overall=0.8, guidance=0.9, days_ago=90,
                        pos_kw=30, neg_kw=1, risk_kw=0, growth_kw=20),
            _transcript("Q3 2025", overall=-0.8, guidance=-0.9, days_ago=0,
                        pos_kw=1, neg_kw=30, risk_kw=15, growth_kw=0),
        ]
        results = detect(
            filings=filings, transcripts=transcripts,
            ticker="TEST", as_of=AS_OF,
        )
        for r in results:
            assert 0 <= r["score"] <= 100
