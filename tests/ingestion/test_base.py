"""Tests for base provider utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.base import (
    NormalizedRecord,
    RateLimiter,
    SourceRun,
    make_idempotency_key,
)


class TestIdempotencyKey:
    def test_deterministic(self):
        key1 = make_idempotency_key("form4", "AAPL", "2025-03-15")
        key2 = make_idempotency_key("form4", "AAPL", "2025-03-15")
        assert key1 == key2

    def test_different_inputs_different_keys(self):
        key1 = make_idempotency_key("form4", "AAPL", "2025-03-15")
        key2 = make_idempotency_key("form4", "MSFT", "2025-03-15")
        assert key1 != key2

    def test_key_length(self):
        key = make_idempotency_key("test", "data")
        assert len(key) == 20


class TestSourceRun:
    def test_default_status(self):
        run = SourceRun(source_name="test", ticker="AAPL")
        assert run.status == "started"
        assert run.records_fetched == 0

    def test_fields(self):
        run = SourceRun(source_name="sec_form4", ticker="MSFT")
        assert run.source_name == "sec_form4"
        assert run.ticker == "MSFT"


class TestNormalizedRecord:
    def test_default_fields(self):
        rec = NormalizedRecord(ticker="AAPL", source_name="test")
        assert rec.ticker == "AAPL"
        assert rec.raw_payload == {}
        assert rec.idempotency_key == ""


class TestRateLimiter:
    def test_creates_without_error(self):
        limiter = RateLimiter(requests_per_second=10.0)
        assert limiter._interval == 0.1
