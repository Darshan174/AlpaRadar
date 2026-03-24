"""Tests for SEC Form 4 insider trade parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.sec.form4 import Form4Collector, InsiderTradeRecord
from src.ingestion.storage_adapter import clear_memory_store, get_memory_store

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sec"


@pytest.fixture(autouse=True)
def _clean_store():
    clear_memory_store()
    yield
    clear_memory_store()


class TestForm4XMLParsing:
    """Test Form 4 XML parsing with fixture data."""

    def setup_method(self):
        self.collector = Form4Collector()
        self.xml_content = (FIXTURES_DIR / "form4_sample.xml").read_text()

    def test_parse_form4_xml_extracts_transactions(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/Archives/edgar/data/320193/test/doc.xml",
        )

        assert len(records) == 2

    def test_parse_form4_xml_extracts_filer_info(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        first = records[0]
        assert first.filer_name == "DOE JOHN"
        assert first.filer_title == "Senior Vice President"
        assert first.is_director is True
        assert first.is_officer is True
        assert first.is_ten_percent_owner is False

    def test_parse_form4_xml_extracts_transaction_details(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        first = records[0]
        assert first.transaction_type == "P"  # Purchase
        assert first.shares == 5000.0
        assert first.price_per_share == 172.50
        assert first.total_value == 862500.0
        assert first.shares_owned_after == 150000.0
        assert first.is_direct is True
        assert first.transaction_date == "2025-03-15"

    def test_parse_form4_xml_second_transaction(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        second = records[1]
        assert second.shares == 3000.0
        assert second.price_per_share == 170.00
        assert second.total_value == 510000.0
        assert second.transaction_date == "2025-03-14"

    def test_parse_form4_xml_sets_metadata(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        first = records[0]
        assert first.ticker == "AAPL"
        assert first.company_name == "Apple Inc."
        assert first.cik == "320193"
        assert first.source_name == "sec_form4"
        assert first.idempotency_key  # Should be non-empty

    def test_idempotency_keys_are_unique(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        keys = [r.idempotency_key for r in records]
        assert len(keys) == len(set(keys))

    def test_parse_invalid_xml_returns_empty(self):
        records = self.collector._parse_form4_xml(
            "<not>valid form4</not>",
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "test", "filing_date": "2025-01-01"},
            source_url="https://www.sec.gov/test",
        )
        assert records == []

    def test_to_storage_dict(self):
        records = self.collector._parse_form4_xml(
            self.xml_content,
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            filing={"accession_number": "0001234567-25-000123", "filing_date": "2025-03-15"},
            source_url="https://www.sec.gov/test",
        )

        storage = self.collector._to_storage_dict(records[0])
        assert storage["ticker"] == "AAPL"
        assert storage["filer_name"] == "DOE JOHN"
        assert storage["shares"] == 5000.0
        assert "idempotency_key" in storage
        assert "ingested_at" in storage


class TestForm4CollectorIntegration:
    """Test the full Form 4 collector with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_collect_with_mocked_edgar(self):
        collector = Form4Collector()
        submissions = json.loads((FIXTURES_DIR / "submissions_sample.json").read_text())
        form4_xml = (FIXTURES_DIR / "form4_sample.xml").read_text()

        with patch("src.ingestion.sec.form4.lookup_cik") as mock_cik:
            mock_cik.return_value = {
                "cik": "320193",
                "cik_padded": "0000320193",
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
            }

            # Use MagicMock for responses (raise_for_status is sync)
            submissions_resp = MagicMock()
            submissions_resp.json.return_value = submissions
            submissions_resp.raise_for_status = MagicMock()

            xml_resp = MagicMock()
            xml_resp.text = form4_xml
            xml_resp.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[submissions_resp, xml_resp])
            collector._client = mock_client

            records = await collector.collect("AAPL", days_back=365)

            # Should have parsed the form4 XML (2 transactions in fixture)
            assert len(records) == 2
            assert all(isinstance(r, InsiderTradeRecord) for r in records)

            # Check storage
            store = get_memory_store()
            assert len(store["insider_trades"]) == 2
            assert len(store["source_runs"]) == 1
            assert store["source_runs"][0]["status"] == "completed"

        await collector.close()

    @pytest.mark.asyncio
    async def test_collect_no_cik(self):
        collector = Form4Collector()

        with patch("src.ingestion.sec.form4.lookup_cik", return_value=None):
            records = await collector.collect("FAKEXYZ")
            assert records == []

            store = get_memory_store()
            assert len(store["source_runs"]) == 1
            assert store["source_runs"][0]["status"] == "failed"

        await collector.close()
