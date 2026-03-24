"""Tests for SEC 8-K filing event parsing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.sec.filing8k import Filing8KCollector, FilingEventRecord, MATERIAL_ITEMS
from src.ingestion.storage_adapter import clear_memory_store, get_memory_store

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sec"


@pytest.fixture(autouse=True)
def _clean_store():
    clear_memory_store()
    yield
    clear_memory_store()


class TestFiling8KParsing:
    """Test 8-K filing event normalization."""

    def setup_method(self):
        self.collector = Filing8KCollector()

    def test_to_filing_event_basic(self):
        filing = {
            "form_type": "8-K",
            "filing_date": "2025-03-10",
            "accession_number": "0001234567-25-000100",
            "primary_document": "filing.htm",
            "items": "2.02,7.01",
            "doc_url": "https://www.sec.gov/Archives/edgar/data/320193/test/filing.htm",
        }

        record = self.collector._to_filing_event(filing, "AAPL", "Apple Inc.", "320193")

        assert record.ticker == "AAPL"
        assert record.company_name == "Apple Inc."
        assert record.form_type == "8-K"
        assert record.filing_date == "2025-03-10"
        assert "2.02" in record.items
        assert "7.01" in record.items
        assert record.is_material is True
        assert record.source_name == "sec_8k"

    def test_to_filing_event_item_descriptions(self):
        filing = {
            "form_type": "8-K",
            "filing_date": "2025-02-15",
            "accession_number": "0001234567-25-000080",
            "primary_document": "filing.htm",
            "items": "5.02",
            "doc_url": "",
        }

        record = self.collector._to_filing_event(filing, "AAPL", "Apple Inc.", "320193")

        assert "5.02" in record.items
        assert "Departure/Election of Directors" in record.item_descriptions[0]
        assert record.is_material is True

    def test_to_filing_event_no_items(self):
        filing = {
            "form_type": "8-K",
            "filing_date": "2025-01-20",
            "accession_number": "0001234567-25-000050",
            "primary_document": "filing.htm",
            "items": "",
            "doc_url": "",
        }

        record = self.collector._to_filing_event(filing, "AAPL", "Apple Inc.", "320193")
        assert record.items == []
        assert record.is_material is False

    def test_idempotency_key_deterministic(self):
        filing = {
            "form_type": "8-K",
            "filing_date": "2025-03-10",
            "accession_number": "0001234567-25-000100",
            "primary_document": "filing.htm",
            "items": "2.02",
            "doc_url": "",
        }

        r1 = self.collector._to_filing_event(filing, "AAPL", "Apple Inc.", "320193")
        r2 = self.collector._to_filing_event(filing, "AAPL", "Apple Inc.", "320193")
        assert r1.idempotency_key == r2.idempotency_key

    def test_material_items_coverage(self):
        """Verify key 8-K items are classified as material."""
        material_codes = ["1.01", "1.02", "1.03", "2.01", "2.02", "5.02", "4.02"]
        for code in material_codes:
            assert code in MATERIAL_ITEMS, f"{code} should be in MATERIAL_ITEMS"


class TestFiling8KCollectorIntegration:
    """Test the full 8-K collector with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_collect_with_mocked_edgar(self):
        collector = Filing8KCollector()
        submissions = json.loads((FIXTURES_DIR / "submissions_sample.json").read_text())

        with patch("src.ingestion.sec.filing8k.lookup_cik") as mock_cik:
            mock_cik.return_value = {
                "cik": "320193",
                "cik_padded": "0000320193",
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
            }

            mock_resp = MagicMock()
            mock_resp.json.return_value = submissions
            mock_resp.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            collector._client = mock_client

            records = await collector.collect("AAPL", days_back=365)

            # Fixture has 2 8-K filings
            assert len(records) == 2
            assert all(isinstance(r, FilingEventRecord) for r in records)

            store = get_memory_store()
            assert len(store["filing_events"]) == 2
            assert len(store["source_runs"]) == 1
            assert store["source_runs"][0]["status"] == "completed"

        await collector.close()

    @pytest.mark.asyncio
    async def test_collect_no_cik(self):
        collector = Filing8KCollector()

        with patch("src.ingestion.sec.filing8k.lookup_cik", return_value=None):
            records = await collector.collect("FAKEXYZ")
            assert records == []

        await collector.close()

    @pytest.mark.asyncio
    async def test_deduplication(self):
        collector = Filing8KCollector()
        submissions = json.loads((FIXTURES_DIR / "submissions_sample.json").read_text())

        with patch("src.ingestion.sec.filing8k.lookup_cik") as mock_cik:
            mock_cik.return_value = {
                "cik": "320193",
                "cik_padded": "0000320193",
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
            }

            mock_resp = MagicMock()
            mock_resp.json.return_value = submissions
            mock_resp.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            collector._client = mock_client

            # Collect twice
            await collector.collect("AAPL", days_back=365)
            await collector.collect("AAPL", days_back=365)

            store = get_memory_store()
            # Should still only have 2 unique filing events
            assert len(store["filing_events"]) == 2

        await collector.close()
