"""Tests for core models — validation, properties, and new alt-data types."""

from datetime import date, datetime

import pytest

from src.core.models import (
    Brief,
    Company,
    FilingEvent,
    InsiderTrade,
    JobPosting,
    RawDocument,
    Signal,
    SignalStrength,
    SignalType,
    Sentiment,
    SourceRun,
    SourceRunStatus,
    TransactionType,
    TranscriptChunk,
)


# ── SignalType enum ───────────────────────────────────────────────────────────


class TestSignalType:
    def test_legacy_types_preserved(self):
        assert SignalType.HIRING_SURGE == "hiring_surge"
        assert SignalType.EXECUTIVE_MOVE == "executive_move"
        assert SignalType.GROWTH_PRICE_DIVERGENCE == "growth_price_divergence"

    def test_mvp_types_exist(self):
        assert SignalType.INSIDER_BUY_CLUSTER == "insider_buy_cluster"
        assert SignalType.HIRING_MOMENTUM == "hiring_momentum"
        assert SignalType.FILING_CATALYST == "filing_catalyst"
        assert SignalType.TRANSCRIPT_TONE_SHIFT == "transcript_tone_shift"

    def test_all_types_are_strings(self):
        for t in SignalType:
            assert isinstance(t.value, str)


# ── Signal model ──────────────────────────────────────────────────────────────


class TestSignal:
    def test_signal_is_actionable(self):
        sig = Signal(
            type=SignalType.INSIDER_BUY_CLUSTER,
            strength=SignalStrength.STRONG,
            sentiment=Sentiment.BULLISH,
            ticker="AAPL",
            headline="Test",
            detail="",
            score=80,
        )
        assert sig.is_actionable is True

    def test_signal_not_actionable_low_score(self):
        sig = Signal(
            type=SignalType.INSIDER_BUY_CLUSTER,
            strength=SignalStrength.STRONG,
            sentiment=Sentiment.BULLISH,
            ticker="AAPL",
            headline="Test",
            detail="",
            score=40,
        )
        assert sig.is_actionable is False

    def test_signal_not_actionable_weak(self):
        sig = Signal(
            type=SignalType.INSIDER_BUY_CLUSTER,
            strength=SignalStrength.WEAK,
            sentiment=Sentiment.BULLISH,
            ticker="AAPL",
            headline="Test",
            detail="",
            score=90,
        )
        assert sig.is_actionable is False


# ── InsiderTrade model ────────────────────────────────────────────────────────


class TestInsiderTrade:
    @pytest.fixture
    def buy_trade(self):
        return InsiderTrade(
            ticker="AAPL",
            cik="0000320193",
            filer_name="Tim Cook",
            filer_title="CEO",
            is_officer=True,
            is_director=True,
            transaction_type=TransactionType.BUY,
            shares=50000,
            price_per_share=178.50,
            total_value=8_925_000,
            filing_date=date(2025, 12, 15),
            source_url="https://sec.gov/...",
            idempotency_key="test:aapl:cook:20251215",
        )

    def test_is_buy(self, buy_trade):
        assert buy_trade.is_buy is True

    def test_is_notable(self, buy_trade):
        assert buy_trade.is_notable is True

    def test_not_notable_sell(self):
        trade = InsiderTrade(
            ticker="NVDA",
            cik="0001045810",
            filer_name="Jensen Huang",
            is_officer=True,
            transaction_type=TransactionType.SELL,
            shares=100000,
            total_value=48_000_000,
            filing_date=date(2025, 12, 10),
            source_url="https://sec.gov/...",
            idempotency_key="test:nvda:huang:sell",
        )
        assert trade.is_buy is False
        assert trade.is_notable is False

    def test_not_notable_small_value(self):
        trade = InsiderTrade(
            ticker="AAPL",
            cik="0000320193",
            filer_name="Someone",
            is_officer=True,
            transaction_type=TransactionType.BUY,
            shares=10,
            total_value=500,
            filing_date=date(2025, 12, 15),
            source_url="https://sec.gov/...",
            idempotency_key="test:aapl:small",
        )
        assert trade.is_notable is False


# ── FilingEvent model ─────────────────────────────────────────────────────────


class TestFilingEvent:
    def test_material_event(self):
        event = FilingEvent(
            ticker="NVDA",
            cik="0001045810",
            filing_type="8-K",
            form_items=["1.01", "9.01"],
            filing_date=date(2025, 12, 5),
            source_url="https://sec.gov/...",
            accession_number="0001045810-25-000456",
            idempotency_key="0001045810-25-000456",
        )
        assert event.is_material is True

    def test_non_material_event(self):
        event = FilingEvent(
            ticker="AAPL",
            cik="0000320193",
            filing_type="8-K",
            form_items=["9.01"],
            filing_date=date(2025, 12, 1),
            source_url="https://sec.gov/...",
            accession_number="test-accession",
            idempotency_key="test-accession",
        )
        assert event.is_material is False


# ── SourceRun model ───────────────────────────────────────────────────────────


class TestSourceRun:
    def test_defaults(self):
        run = SourceRun(source_name="sec_form4", ticker="AAPL")
        assert run.status == SourceRunStatus.RUNNING
        assert run.records_fetched == 0
        assert run.records_stored == 0
        assert run.completed_at is None


# ── Company model ─────────────────────────────────────────────────────────────


class TestCompany:
    def test_basic(self):
        company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
        assert company.in_universe is True
        assert company.ticker == "AAPL"


# ── Brief model ──────────────────────────────────────────────────────────────


class TestBrief:
    def test_basic(self):
        brief = Brief(
            ticker="AAPL",
            signal_id="seed-sig-001",
            headline="Test brief",
            body="Body text",
        )
        assert brief.brief_type == "signal"
        assert brief.model_used == ""


# ── JobPosting model ──────────────────────────────────────────────────────────


class TestJobPosting:
    def test_defaults(self):
        posting = JobPosting(
            ticker="NVDA",
            title="ML Engineer",
            source_name="fixture",
            idempotency_key="test:nvda:ml-eng",
        )
        assert posting.is_active is True
        assert posting.is_remote is False
        assert posting.department == ""


# ── TranscriptChunk model ────────────────────────────────────────────────────


class TestTranscriptChunk:
    def test_basic(self):
        chunk = TranscriptChunk(
            ticker="AAPL",
            fiscal_quarter="Q4 2025",
            call_date=date(2025, 12, 1),
            content="Revenue was strong this quarter.",
            word_count=5,
            idempotency_key="test:aapl:q42025:0",
        )
        assert chunk.section == ""
        assert chunk.chunk_index == 0
