"""Tests for feed API routes."""

import sys
sys.path.insert(0, "src")

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_feed_returns_signals():
    resp = client.get("/v1/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert "signals" in data
    assert "total" in data
    assert len(data["signals"]) > 0
    assert "historical_win_rate" in data["signals"][0]


def test_feed_filter_by_ticker():
    resp = client.get("/v1/feed?ticker=NVDA")
    assert resp.status_code == 200
    data = resp.json()
    assert all(s["ticker"] == "NVDA" for s in data["signals"])


def test_feed_filter_by_type():
    resp = client.get("/v1/feed?type=hiring_surge")
    assert resp.status_code == 200
    data = resp.json()
    assert all(s["type"] == "hiring_surge" for s in data["signals"])


def test_feed_filter_by_min_score():
    resp = client.get("/v1/feed?min_score=80")
    assert resp.status_code == 200
    data = resp.json()
    assert all(s["score"] >= 80 for s in data["signals"])


def test_signal_detail():
    # Get a signal ID from the feed first
    feed = client.get("/v1/feed").json()
    signal_id = feed["signals"][0]["id"]

    resp = client.get(f"/v1/signal/{signal_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "signal" in data
    assert "brief" in data
    assert data["signal"]["id"] == signal_id


def test_signal_detail_not_found():
    resp = client.get("/v1/signal/nonexistent")
    assert resp.status_code == 404


def test_company_detail():
    resp = client.get("/v1/company/NVDA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company"]["ticker"] == "NVDA"
    assert len(data["signals"]) >= 1
    assert data["suggested_action"] is not None
    assert data["signals"][0]["historical_win_rate"] is not None


def test_company_detail_case_insensitive():
    resp = client.get("/v1/company/nvda")
    assert resp.status_code == 200


def test_company_not_found():
    resp = client.get("/v1/company/ZZZZZ")
    assert resp.status_code == 404


def test_list_companies():
    resp = client.get("/v1/companies")
    assert resp.status_code == 200
    data = resp.json()
    assert "companies" in data
    assert len(data["companies"]) >= 10


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
