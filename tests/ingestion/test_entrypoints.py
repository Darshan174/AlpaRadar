"""Tests for ingestion entrypoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.entrypoints import (
    sync_company_alt_data,
    sync_job_postings,
    sync_transcripts,
)
from src.ingestion.jobs.provider import FixtureJobProvider
from src.ingestion.storage_adapter import clear_memory_store, get_memory_store


@pytest.fixture(autouse=True)
def _clean_store():
    clear_memory_store()
    yield
    clear_memory_store()


class TestSyncJobPostings:
    @pytest.mark.asyncio
    async def test_sync_with_fixture_provider(self):
        result = await sync_job_postings("AAPL", provider=FixtureJobProvider())

        assert result["ticker"] == "AAPL"
        assert result["total_postings"] == 8
        assert result["engineering"] >= 4
        assert "departments" in result

    @pytest.mark.asyncio
    async def test_sync_returns_department_breakdown(self):
        result = await sync_job_postings("AAPL", provider=FixtureJobProvider())

        assert "engineering" in result["departments"]
        assert result["departments"]["engineering"] >= 4


class TestSyncTranscripts:
    @pytest.mark.asyncio
    async def test_sync_transcripts_with_fixtures(self):
        result = await sync_transcripts("AAPL")

        assert result["ticker"] == "AAPL"
        assert result["chunks"] >= 1


class TestSyncCompanyAltData:
    @pytest.mark.asyncio
    async def test_full_sync_jobs_only(self):
        """Test sync with only jobs enabled (no SEC mocking needed)."""
        result = await sync_company_alt_data(
            "AAPL",
            include_sec=False,
            include_jobs=True,
            include_transcripts=False,
        )

        assert result["ticker"] == "AAPL"
        assert "jobs" in result
        assert result["jobs"]["total_postings"] >= 1

    @pytest.mark.asyncio
    async def test_full_sync_handles_sec_failure(self):
        """Test that SEC failure doesn't block other collectors."""
        with patch(
            "src.ingestion.entrypoints.sync_sec_activity",
            side_effect=Exception("SEC down"),
        ):
            result = await sync_company_alt_data(
                "AAPL",
                include_sec=True,
                include_jobs=True,
                include_transcripts=False,
            )

            assert "error" in result["sec"]
            assert result["jobs"]["total_postings"] >= 1
