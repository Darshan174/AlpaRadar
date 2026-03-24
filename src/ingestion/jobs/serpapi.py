"""SerpAPI-based job posting provider.

Requires SERPAPI_KEY env var. Falls back to fixture provider if unavailable.
Free tier: 100 searches/month.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from src.logging_config import get_logger

from .provider import JobPostingProvider

log = get_logger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


class SerpAPIJobProvider(JobPostingProvider):
    """SerpAPI Google Jobs search provider."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("SERPAPI_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def search_jobs(
        self, company_name: str, ticker: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            log.warning("serpapi_not_configured", ticker=ticker)
            return []

        query = f"{company_name} jobs"
        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": self._api_key,
            "hl": "en",
            "num": kwargs.get("limit", 20),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(SERPAPI_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.error("serpapi_request_failed", ticker=ticker, error=str(e))
            return []

        raw_jobs = data.get("jobs_results", [])
        normalized = []
        for job in raw_jobs:
            normalized.append(
                {
                    "title": job.get("title", ""),
                    "company_name": job.get("company_name", company_name),
                    "location": job.get("location", ""),
                    "posted_date": _extract_date(job.get("detected_extensions", {})),
                    "description": job.get("description", ""),
                    "snippet": job.get("description", "")[:500],
                    "job_url": job.get("share_link", job.get("job_id", "")),
                    "via": job.get("via", ""),
                    "source": "serpapi",
                }
            )

        log.info("serpapi_jobs_fetched", ticker=ticker, count=len(normalized))
        return normalized


def _extract_date(extensions: dict) -> str:
    """Try to extract a posted date from SerpAPI extensions."""
    posted = extensions.get("posted_at", "")
    if posted:
        return posted
    return ""
