"""Production-grade Crustdata API client with retry, rate-limit handling, and structured logging."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings
from src.core.exceptions import CrustdataAPIError, CrustdataRateLimitError
from src.logging_config import get_logger

from .models import (
    CrustdataCompanyEnrichment,
    CrustdataCompanySearchResponse,
    CrustdataCompanySearchResult,
    CrustdataPersonResult,
    CrustdataPersonSearchResponse,
    CrustdataSocialPost,
)

log = get_logger(__name__)

_RETRY_POLICY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, CrustdataRateLimitError)),
    reraise=True,
)


class CrustdataClient:
    """Async client for the Crustdata API.

    Endpoints used:
    - POST /company/enrich   — headcount, funding, hiring trends, competitors
    - POST /company/search   — filter companies by industry, growth, geography
    - POST /person/search    — find executives by title, company, location
    - POST /person/enrich    — full profile from LinkedIn URL or email
    - GET  /person/{id}/social-posts — recent social posts by a person
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self._api_key = api_key or settings.crustdata_api_key
        self._base_url = (base_url or settings.crustdata_base_url).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "X-API-Version": settings.crustdata_api_version,
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> CrustdataClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ── Internal ───────────────────────────────────────────────────────────────

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        log.debug("crustdata_request", method=method, path=path)
        resp = await self._client.request(method, path, **kwargs)

        if resp.status_code == 429:
            raise CrustdataRateLimitError(429, "Rate limit exceeded")
        if resp.status_code >= 400:
            raise CrustdataAPIError(resp.status_code, resp.text[:500])

        return resp.json()

    @retry(**_RETRY_POLICY)
    async def _post(self, path: str, payload: dict) -> dict:
        return await self._request("POST", path, json=payload)

    @retry(**_RETRY_POLICY)
    async def _get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    # ── Company Endpoints ──────────────────────────────────────────────────────

    async def enrich_company(
        self,
        *,
        domain: str | None = None,
        name: str | None = None,
        linkedin_url: str | None = None,
    ) -> CrustdataCompanyEnrichment:
        """Enrich a company profile — headcount, funding, trends, competitors."""
        payload: dict[str, Any] = {}
        if domain:
            payload["domain"] = domain
        if name:
            payload["company_name"] = name
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url

        raw = await self._post("/company/enrich", payload)
        log.info("company_enriched", company=domain or name, keys=list(raw.keys()))
        return CrustdataCompanyEnrichment.model_validate(raw)

    async def search_companies(
        self,
        *,
        industry: str | None = None,
        country: str | None = None,
        min_headcount: int | None = None,
        max_headcount: int | None = None,
        min_headcount_growth_pct: float | None = None,
        min_funding_usd: float | None = None,
        limit: int = 50,
    ) -> CrustdataCompanySearchResponse:
        """Screen companies by industry, headcount growth, funding, geography."""
        filters: dict[str, Any] = {}
        if industry:
            filters["industry"] = industry
        if country:
            filters["country"] = country
        if min_headcount is not None:
            filters["min_headcount"] = min_headcount
        if max_headcount is not None:
            filters["max_headcount"] = max_headcount
        if min_headcount_growth_pct is not None:
            filters["min_headcount_growth_pct"] = min_headcount_growth_pct
        if min_funding_usd is not None:
            filters["min_funding_usd"] = min_funding_usd

        raw = await self._post("/company/search", {"filters": filters, "limit": limit})
        return CrustdataCompanySearchResponse.model_validate(raw)

    async def get_company_headcount_history(
        self,
        company_id: str,
    ) -> list[dict]:
        """Get historical headcount snapshots for a company."""
        raw = await self._get(f"/company/{company_id}/headcount-history")
        return raw.get("history", [])

    async def get_company_competitors(
        self,
        company_id: str,
    ) -> list[CrustdataCompanySearchResult]:
        """Get competitors for a company."""
        raw = await self._get(f"/company/{company_id}/competitors")
        return [CrustdataCompanySearchResult.model_validate(c) for c in raw.get("competitors", [])]

    # ── Person Endpoints ───────────────────────────────────────────────────────

    async def search_people(
        self,
        *,
        company_name: str | None = None,
        company_domain: str | None = None,
        title: str | None = None,
        seniority: str | None = None,
        location: str | None = None,
        limit: int = 50,
    ) -> CrustdataPersonSearchResponse:
        """Search for people by company, title, seniority, or location."""
        filters: dict[str, Any] = {}
        if company_name:
            filters["company_name"] = company_name
        if company_domain:
            filters["company_domain"] = company_domain
        if title:
            filters["title"] = title
        if seniority:
            filters["seniority"] = seniority
        if location:
            filters["location"] = location

        raw = await self._post("/person/search", {"filters": filters, "limit": limit})
        return CrustdataPersonSearchResponse.model_validate(raw)

    async def enrich_person(
        self,
        *,
        linkedin_url: str | None = None,
        email: str | None = None,
    ) -> CrustdataPersonResult:
        """Enrich a person profile from LinkedIn URL or email."""
        payload: dict[str, Any] = {}
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url
        if email:
            payload["email"] = email

        raw = await self._post("/person/enrich", payload)
        return CrustdataPersonResult.model_validate(raw)

    async def get_social_posts(
        self,
        person_id: str,
        limit: int = 20,
    ) -> list[CrustdataSocialPost]:
        """Get recent social posts by a person (for sentiment analysis)."""
        raw = await self._get(f"/person/{person_id}/social-posts", params={"limit": limit})
        return [CrustdataSocialPost.model_validate(p) for p in raw.get("posts", [])]

    # ── Batch Operations ───────────────────────────────────────────────────────

    async def batch_enrich_companies(
        self,
        domains: list[str],
    ) -> list[CrustdataCompanyEnrichment]:
        """Enrich multiple companies by domain. Handles individually to respect rate limits."""
        results = []
        for domain in domains:
            try:
                result = await self.enrich_company(domain=domain)
                results.append(result)
            except CrustdataAPIError as e:
                log.warning("batch_enrich_failed", domain=domain, error=str(e))
        return results

    async def find_executives(
        self,
        company_domain: str,
    ) -> list[CrustdataPersonResult]:
        """Find C-suite and VP-level executives at a company."""
        results = []
        for seniority in ["c_suite", "vp"]:
            try:
                resp = await self.search_people(
                    company_domain=company_domain,
                    seniority=seniority,
                    limit=20,
                )
                results.extend(resp.results)
            except CrustdataAPIError as e:
                log.warning("exec_search_failed", domain=company_domain, seniority=seniority, error=str(e))
        return results
