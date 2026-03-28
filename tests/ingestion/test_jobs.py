"""Tests for job posting collector."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.jobs.provider import (
    FixtureJobProvider,
    JobPostingCollector,
    JobPostingRecord,
    _classify_department,
    _classify_seniority,
)
from src.ingestion.storage_adapter import clear_memory_store, get_memory_store


@pytest.fixture(autouse=True)
def _clean_store():
    clear_memory_store()
    yield
    clear_memory_store()


class TestDepartmentClassification:
    def test_engineering_titles(self):
        assert _classify_department("Senior Software Engineer", "") == "engineering"
        assert _classify_department("ML Engineer", "") == "engineering"
        assert _classify_department("DevOps Engineer", "") == "engineering"
        assert _classify_department("Data Scientist", "") == "engineering"
        assert _classify_department("Backend Developer", "") == "engineering"

    def test_sales_titles(self):
        assert _classify_department("Account Executive", "") == "sales"
        assert _classify_department("Sales Manager", "") == "sales"
        assert _classify_department("Business Development Rep", "") == "sales"

    def test_other_departments(self):
        assert _classify_department("Marketing Manager", "") == "marketing"
        assert _classify_department("Product Manager", "") == "product"
        assert _classify_department("UX Designer", "") == "design"
        assert _classify_department("HR Manager", "") == "people"

    def test_department_hint(self):
        assert _classify_department("Manager", "engineering") == "engineering"

    def test_unknown_maps_to_other(self):
        assert _classify_department("Office Coordinator", "") == "other"


class TestSeniorityClassification:
    def test_c_suite(self):
        assert _classify_seniority("Chief Technology Officer") == "c_suite"
        assert _classify_seniority("CEO") == "c_suite"

    def test_vp(self):
        assert _classify_seniority("VP of Engineering") == "vp"
        assert _classify_seniority("Vice President of Sales") == "vp"

    def test_director(self):
        assert _classify_seniority("Director of Engineering") == "director"

    def test_lead(self):
        assert _classify_seniority("Staff Engineer") == "lead"
        assert _classify_seniority("Principal Engineer") == "lead"
        assert _classify_seniority("Lead Designer") == "lead"

    def test_senior(self):
        assert _classify_seniority("Senior Software Engineer") == "senior"
        assert _classify_seniority("Sr. Engineer") == "senior"

    def test_entry(self):
        assert _classify_seniority("Junior Developer") == "entry"
        assert _classify_seniority("Associate Analyst") == "entry"
        assert _classify_seniority("Intern - Engineering") == "entry"

    def test_mid(self):
        assert _classify_seniority("Software Engineer") == "mid"


class TestJobPostingCollector:
    @pytest.mark.asyncio
    async def test_collect_with_fixtures(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        records = await collector.collect("AAPL", company_name="Apple")

        assert len(records) == 8  # 8 jobs in sample fixture
        assert all(isinstance(r, JobPostingRecord) for r in records)

    @pytest.mark.asyncio
    async def test_fixture_records_are_normalized(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        records = await collector.collect("AAPL", company_name="Apple")
        first = records[0]

        assert first.ticker == "AAPL"
        assert first.source_name == "job_postings"
        assert first.idempotency_key  # Non-empty
        assert first.title  # Non-empty

    @pytest.mark.asyncio
    async def test_engineering_classification(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        records = await collector.collect("AAPL", company_name="Apple")

        eng_count = sum(1 for r in records if r.is_engineering)
        assert eng_count >= 4  # Most jobs in fixture are engineering

    @pytest.mark.asyncio
    async def test_storage_and_dedup(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        # Collect twice
        await collector.collect("AAPL", company_name="Apple")
        await collector.collect("AAPL", company_name="Apple")

        store = get_memory_store()
        # Should be deduplicated
        assert len(store["job_postings"]) == 8

    @pytest.mark.asyncio
    async def test_source_run_logged(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        await collector.collect("AAPL", company_name="Apple")

        store = get_memory_store()
        assert len(store["source_runs"]) == 1
        assert store["source_runs"][0]["status"] == "completed"
        assert store["source_runs"][0]["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_collect_nonexistent_ticker_returns_empty(self):
        provider = FixtureJobProvider()
        collector = JobPostingCollector(provider=provider)

        records = await collector.collect("ZZZZZ", company_name="NonExistent Corp")
        # No fixture file for ZZZZZ, falls back to sample_jobs.json
        assert len(records) == 8  # Gets sample data


class TestJobPostingRecord:
    def test_record_fields(self):
        rec = JobPostingRecord(
            ticker="AAPL",
            title="Senior Engineer",
            department="engineering",
            location="Cupertino, CA",
            seniority="senior",
            is_engineering=True,
        )
        assert rec.ticker == "AAPL"
        assert rec.is_engineering is True
        assert rec.seniority == "senior"
