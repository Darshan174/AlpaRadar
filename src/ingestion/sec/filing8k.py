"""SEC 8-K filing event collector.

Fetches recent 8-K filings from EDGAR and extracts filing events with
item types, descriptions, and source URLs. Free API, no key required.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from src.logging_config import get_logger

from ..base import BaseProvider, NormalizedRecord, RateLimiter, make_idempotency_key
from ..storage_adapter import store_filing_event, store_raw_document, store_source_run
from .cik_lookup import SEC_USER_AGENT, lookup_cik

log = get_logger(__name__)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

# 8-K item types that are material for investment signals
MATERIAL_ITEMS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy Listing Rule",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Election of Directors or Officers; Appointment of Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
}


class FilingEventRecord(NormalizedRecord):
    """Normalized 8-K filing event."""

    form_type: str = "8-K"
    filing_date: str = ""
    accession_number: str = ""
    items: list[str] = []
    item_descriptions: list[str] = []
    description: str = ""
    is_material: bool = False


class Filing8KCollector(BaseProvider):
    """Collects SEC 8-K filing events."""

    source_name = "sec_8k"

    def __init__(self) -> None:
        self.rate_limiter = RateLimiter(requests_per_second=8.0)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=20.0,
                headers={"User-Agent": SEC_USER_AGENT},
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def collect(self, ticker: str, **kwargs: Any) -> list[NormalizedRecord]:
        """Fetch recent 8-K filings for a ticker."""
        run = self.start_run(ticker)
        days_back = kwargs.get("days_back", 90)
        max_filings = kwargs.get("max_filings", 30)

        try:
            cik_info = await lookup_cik(ticker)
            if not cik_info:
                self.fail_run(run, f"CIK not found for {ticker}")
                await store_source_run(run)
                return []

            filings = await self._fetch_recent_8ks(
                cik_info["cik_padded"], cik_info["cik"], days_back, max_filings
            )

            records = []
            for filing in filings:
                record = self._to_filing_event(
                    filing, ticker, cik_info["company_name"], cik_info["cik"]
                )
                records.append(record)

            stored = 0
            for rec in records:
                event_data = self._to_storage_dict(rec)
                was_new = await store_filing_event(event_data)
                if was_new:
                    stored += 1

            self.complete_run(run, len(records), stored)
            await store_source_run(run)
            return records

        except Exception as e:
            self.fail_run(run, str(e))
            await store_source_run(run)
            log.error("filing8k_collect_failed", ticker=ticker, error=str(e))
            return []

    async def _fetch_recent_8ks(
        self, cik_padded: str, cik: str, days_back: int, max_filings: int
    ) -> list[dict[str, Any]]:
        """Fetch recent 8-K filing metadata from EDGAR submissions."""
        self._throttle()
        client = await self._get_client()

        url = SUBMISSIONS_URL.format(cik_padded=cik_padded)
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        recent = data.get("filings", {}).get("recent", {})
        if not recent:
            return []

        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        items_list = recent.get("items", [])

        cutoff_date = (datetime.utcnow().date() - timedelta(days=days_back)).isoformat()

        filings = []
        for i, form_type in enumerate(forms):
            if form_type not in ("8-K", "8-K/A"):
                continue
            filing_date = dates[i] if i < len(dates) else ""
            if filing_date and filing_date < cutoff_date:
                continue
            if len(filings) >= max_filings:
                break

            accession = accessions[i] if i < len(accessions) else ""
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            items = items_list[i] if i < len(items_list) else ""

            accession_path = accession.replace("-", "")
            doc_url = f"{ARCHIVES_BASE}/{cik}/{accession_path}/{primary_doc}" if primary_doc else ""

            filings.append(
                {
                    "form_type": form_type,
                    "filing_date": filing_date,
                    "accession_number": accession,
                    "primary_document": primary_doc,
                    "items": items,
                    "doc_url": doc_url,
                }
            )

        log.info("filing8k_found", cik=cik, count=len(filings))
        return filings

    def _to_filing_event(
        self,
        filing: dict[str, Any],
        ticker: str,
        company_name: str,
        cik: str,
    ) -> FilingEventRecord:
        """Convert raw filing metadata to a normalized record."""
        items_str = filing.get("items", "")
        items = [i.strip() for i in items_str.split(",") if i.strip()] if items_str else []

        item_descs = [MATERIAL_ITEMS.get(item, "Unknown Item") for item in items]
        is_material = any(item in MATERIAL_ITEMS for item in items)

        description = f"8-K filed {filing['filing_date']}"
        if item_descs:
            description += f": {'; '.join(item_descs)}"

        return FilingEventRecord(
            idempotency_key=make_idempotency_key("8k", filing["accession_number"]),
            source_name="sec_8k",
            source_url=filing.get("doc_url", ""),
            source_timestamp=_parse_date(filing["filing_date"]),
            ticker=ticker.upper(),
            company_name=company_name,
            cik=cik,
            form_type=filing["form_type"],
            filing_date=filing["filing_date"],
            accession_number=filing["accession_number"],
            items=items,
            item_descriptions=item_descs,
            description=description,
            is_material=is_material,
            raw_payload=filing,
        )

    def _to_storage_dict(self, record: FilingEventRecord) -> dict[str, Any]:
        """Convert to a dict suitable for storage."""
        return {
            "idempotency_key": record.idempotency_key,
            "source_name": record.source_name,
            "source_url": record.source_url,
            "source_timestamp": record.source_timestamp.isoformat() if record.source_timestamp else None,
            "ticker": record.ticker,
            "company_name": record.company_name,
            "cik": record.cik,
            "form_type": record.form_type,
            "filing_date": record.filing_date,
            "accession_number": record.accession_number,
            "items": record.items,
            "item_descriptions": record.item_descriptions,
            "description": record.description,
            "is_material": record.is_material,
            "raw_payload": record.raw_payload,
            "ingested_at": record.ingested_at.isoformat(),
        }


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
