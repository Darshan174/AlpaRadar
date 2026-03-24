"""Tests for storage helpers — mocked Supabase client."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.models import (
    Brief,
    Company,
    FilingEvent,
    InsiderTrade,
    JobPosting,
    RawDocument,
    SourceRun,
    SourceRunStatus,
    TransactionType,
    TranscriptChunk,
)


def _mock_supabase_client():
    """Create a mock Supabase client that chains table().select/insert/upsert/etc."""
    client = MagicMock()

    def make_chain(return_data=None):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.insert.return_value = chain
        chain.upsert.return_value = chain
        chain.update.return_value = chain
        chain.delete.return_value = chain
        chain.eq.return_value = chain
        chain.gte.return_value = chain
        chain.order.return_value = chain
        chain.limit.return_value = chain
        result = MagicMock()
        result.data = return_data or []
        chain.execute.return_value = result
        return chain

    client._chains = {}

    def table_fn(name):
        if name not in client._chains:
            client._chains[name] = make_chain()
        return client._chains[name]

    client.table = MagicMock(side_effect=table_fn)
    return client


@pytest.fixture
def mock_client(monkeypatch):
    client = _mock_supabase_client()
    monkeypatch.setattr("src.storage.supabase._client", client)
    monkeypatch.setattr("src.storage.supabase.get_client", lambda: client)
    return client


def _set_return_data(client, table_name, data):
    """Configure mock to return specific data for a table."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.upsert.return_value = chain
    chain.update.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.gte.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    result = MagicMock()
    result.data = data
    chain.execute.return_value = result
    client._chains[table_name] = chain
    return chain


# ── Source Run Tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_source_run(mock_client):
    from src.storage.supabase import create_source_run

    _set_return_data(mock_client, "source_runs", [{"id": "run-123"}])

    run = SourceRun(source_name="sec_form4", ticker="AAPL")
    result = await create_source_run(run)
    assert result == "run-123"
    mock_client.table.assert_any_call("source_runs")


@pytest.mark.asyncio
async def test_complete_source_run(mock_client):
    from src.storage.supabase import complete_source_run

    _set_return_data(mock_client, "source_runs", [{}])

    await complete_source_run(
        "run-123",
        status=SourceRunStatus.COMPLETED,
        records_fetched=10,
        records_stored=8,
    )
    mock_client.table.assert_any_call("source_runs")


# ── Insider Trade Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_insider_trade(mock_client):
    from src.storage.supabase import upsert_insider_trade

    _set_return_data(mock_client, "insider_trades", [{"id": "trade-456"}])

    trade = InsiderTrade(
        ticker="AAPL",
        cik="0000320193",
        filer_name="Tim Cook",
        is_officer=True,
        transaction_type=TransactionType.BUY,
        shares=50000,
        price_per_share=178.50,
        total_value=8925000,
        filing_date=date(2025, 12, 15),
        source_url="https://sec.gov/...",
        idempotency_key="test:aapl:cook:20251215",
    )
    result = await upsert_insider_trade(trade)
    assert result == "trade-456"


@pytest.mark.asyncio
async def test_get_insider_trades(mock_client):
    from src.storage.supabase import get_insider_trades

    expected = [{"ticker": "AAPL", "filer_name": "Tim Cook", "transaction_type": "buy"}]
    _set_return_data(mock_client, "insider_trades", expected)

    result = await get_insider_trades("AAPL", days_back=90)
    assert result == expected


@pytest.mark.asyncio
async def test_get_insider_buy_cluster(mock_client):
    from src.storage.supabase import get_insider_buy_cluster

    expected = [{"ticker": "AAPL", "transaction_type": "buy"}]
    _set_return_data(mock_client, "insider_trades", expected)

    result = await get_insider_buy_cluster("AAPL")
    assert result == expected


# ── Job Posting Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_job_posting(mock_client):
    from src.storage.supabase import upsert_job_posting

    _set_return_data(mock_client, "job_postings", [{"id": "job-789"}])

    posting = JobPosting(
        ticker="NVDA",
        title="ML Engineer",
        source_name="fixture",
        idempotency_key="test:nvda:ml-eng",
    )
    result = await upsert_job_posting(posting)
    assert result == "job-789"


@pytest.mark.asyncio
async def test_get_job_posting_counts(mock_client):
    from src.storage.supabase import get_job_posting_counts

    _set_return_data(mock_client, "job_postings", [
        {"department": "engineering"},
        {"department": "engineering"},
        {"department": "sales"},
        {"department": "engineering"},
    ])

    result = await get_job_posting_counts("NVDA")
    assert result["engineering"] == 3
    assert result["sales"] == 1
    assert result["_total"] == 4


# ── Filing Event Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_filing_event(mock_client):
    from src.storage.supabase import upsert_filing_event

    _set_return_data(mock_client, "filing_events", [{"id": "filing-abc"}])

    event = FilingEvent(
        ticker="NVDA",
        cik="0001045810",
        filing_type="8-K",
        form_items=["1.01"],
        filing_date=date(2025, 12, 5),
        source_url="https://sec.gov/...",
        accession_number="test-accession",
        idempotency_key="test-accession",
    )
    result = await upsert_filing_event(event)
    assert result == "filing-abc"


@pytest.mark.asyncio
async def test_get_material_filings(mock_client):
    from src.storage.supabase import get_material_filings

    expected = [{"ticker": "NVDA", "filing_type": "8-K"}]
    _set_return_data(mock_client, "filing_events", expected)

    result = await get_material_filings("NVDA")
    assert result == expected


# ── Company Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_company(mock_client):
    from src.storage.supabase import upsert_company

    _set_return_data(mock_client, "companies", [{"ticker": "AAPL"}])

    company = Company(ticker="AAPL", name="Apple Inc.", cik="0000320193")
    result = await upsert_company(company)
    assert result == "AAPL"


@pytest.mark.asyncio
async def test_get_universe_tickers(mock_client):
    from src.storage.supabase import get_universe_tickers

    _set_return_data(mock_client, "companies", [
        {"ticker": "AAPL"},
        {"ticker": "NVDA"},
        {"ticker": "CRM"},
    ])

    result = await get_universe_tickers()
    assert result == ["AAPL", "NVDA", "CRM"]


# ── Brief Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_store_brief(mock_client):
    from src.storage.supabase import store_brief

    _set_return_data(mock_client, "briefs", [{"id": "brief-xyz"}])

    brief = Brief(
        ticker="AAPL",
        signal_id="sig-001",
        headline="Test Brief",
        body="Brief body text",
    )
    result = await store_brief(brief)
    assert result == "brief-xyz"


@pytest.mark.asyncio
async def test_get_briefs(mock_client):
    from src.storage.supabase import get_briefs

    expected = [{"id": "brief-xyz", "ticker": "AAPL"}]
    _set_return_data(mock_client, "briefs", expected)

    result = await get_briefs(ticker="AAPL")
    assert result == expected
