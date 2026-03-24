"""Job posting provider interface and fixture-backed fallback."""

from __future__ import annotations

import abc
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.logging_config import get_logger

from ..base import BaseProvider, NormalizedRecord, make_idempotency_key
from ..storage_adapter import store_job_posting, store_source_run

log = get_logger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "jobs"


class JobPostingRecord(NormalizedRecord):
    """Normalized job posting record."""

    title: str = ""
    department: str = ""
    location: str = ""
    seniority: str = ""  # entry, mid, senior, lead, director, vp, c_suite
    posted_date: str = ""
    job_url: str = ""
    description_snippet: str = ""
    is_engineering: bool = False
    is_sales: bool = False


class JobPostingProvider(abc.ABC):
    """Abstract interface for job posting data sources."""

    @abc.abstractmethod
    async def search_jobs(
        self, company_name: str, ticker: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Return raw job posting results for a company."""
        ...


class FixtureJobProvider(JobPostingProvider):
    """Fixture-backed job provider for testing without live API keys."""

    async def search_jobs(
        self, company_name: str, ticker: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        fixture_file = FIXTURES_DIR / f"{ticker.lower()}_jobs.json"
        if not fixture_file.exists():
            fixture_file = FIXTURES_DIR / "sample_jobs.json"
        if not fixture_file.exists():
            log.warning("no_job_fixtures", ticker=ticker)
            return []

        data = json.loads(fixture_file.read_text())
        log.info("fixture_jobs_loaded", ticker=ticker, count=len(data))
        return data


class JobPostingCollector(BaseProvider):
    """Collects job posting data and normalizes into records."""

    source_name = "job_postings"

    def __init__(self, provider: JobPostingProvider | None = None) -> None:
        self._provider = provider or FixtureJobProvider()

    async def collect(self, ticker: str, **kwargs: Any) -> list[NormalizedRecord]:
        """Collect job postings for a company."""
        run = self.start_run(ticker)
        company_name = kwargs.pop("company_name", ticker)

        try:
            raw_jobs = await self._provider.search_jobs(company_name, ticker, **kwargs)
            records = [self._normalize(job, ticker, company_name) for job in raw_jobs]

            stored = 0
            for rec in records:
                job_data = self._to_storage_dict(rec)
                was_new = await store_job_posting(job_data)
                if was_new:
                    stored += 1

            self.complete_run(run, len(records), stored)
            await store_source_run(run)
            return records

        except Exception as e:
            self.fail_run(run, str(e))
            await store_source_run(run)
            log.error("job_collect_failed", ticker=ticker, error=str(e))
            return []

    def _normalize(
        self, raw: dict[str, Any], ticker: str, company_name: str
    ) -> JobPostingRecord:
        """Normalize a raw job posting into a standard record."""
        title = raw.get("title", "")
        department = _classify_department(title, raw.get("department", ""))
        seniority = _classify_seniority(title)

        return JobPostingRecord(
            idempotency_key=make_idempotency_key(
                "job", ticker, title, raw.get("location", ""), raw.get("posted_date", "")
            ),
            source_name=self.source_name,
            source_url=raw.get("job_url", raw.get("link", "")),
            source_timestamp=_parse_date(raw.get("posted_date", raw.get("date", ""))),
            ticker=ticker.upper(),
            company_name=company_name,
            title=title,
            department=department,
            location=raw.get("location", ""),
            seniority=seniority,
            posted_date=raw.get("posted_date", raw.get("date", "")),
            job_url=raw.get("job_url", raw.get("link", "")),
            description_snippet=raw.get("snippet", raw.get("description", ""))[:500],
            is_engineering=department == "engineering",
            is_sales=department == "sales",
            raw_payload=raw,
        )

    def _to_storage_dict(self, record: JobPostingRecord) -> dict[str, Any]:
        return {
            "idempotency_key": record.idempotency_key,
            "source_name": record.source_name,
            "source_url": record.source_url,
            "source_timestamp": record.source_timestamp.isoformat() if record.source_timestamp else None,
            "ticker": record.ticker,
            "company_name": record.company_name,
            "title": record.title,
            "department": record.department,
            "location": record.location,
            "seniority": record.seniority,
            "posted_date": record.posted_date,
            "job_url": record.job_url,
            "description_snippet": record.description_snippet,
            "is_engineering": record.is_engineering,
            "is_sales": record.is_sales,
            "raw_payload": record.raw_payload,
            "ingested_at": record.ingested_at.isoformat(),
        }


def _classify_department(title: str, dept_hint: str) -> str:
    """Best-effort department classification from job title."""
    t = (title + " " + dept_hint).lower()
    if any(kw in t for kw in ["engineer", "developer", "devops", "sre", "data scientist", "ml ", "machine learning", "software", "backend", "frontend", "fullstack", "platform"]):
        return "engineering"
    if any(kw in t for kw in ["sales", "account executive", "business development", "revenue"]):
        return "sales"
    if any(kw in t for kw in ["marketing", "growth", "brand", "content"]):
        return "marketing"
    if any(kw in t for kw in ["product manager", "product lead", "product director"]):
        return "product"
    if any(kw in t for kw in ["design", "ux", "ui "]):
        return "design"
    if any(kw in t for kw in ["hr ", "human resources", "people", "talent", "recruiter"]):
        return "people"
    if any(kw in t for kw in ["finance", "accounting", "controller", "fp&a"]):
        return "finance"
    if any(kw in t for kw in ["legal", "counsel", "compliance"]):
        return "legal"
    return "other"


def _classify_seniority(title: str) -> str:
    import re
    t = title.lower()
    # Check director before c-suite to avoid "director" matching "cto" substring
    if "director" in t:
        return "director"
    if any(re.search(rf"\b{kw}\b", t) for kw in ["chief", "ceo", "cto", "cfo", "coo", "cpo"]):
        return "c_suite"
    if any(kw in t for kw in ["vp ", "vice president"]):
        return "vp"
    if any(kw in t for kw in ["lead", "principal", "staff"]):
        return "lead"
    if "senior" in t or "sr " in t or "sr." in t:
        return "senior"
    if any(kw in t for kw in ["junior", "jr ", "jr.", "associate", "intern"]):
        return "entry"
    return "mid"


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%b %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
