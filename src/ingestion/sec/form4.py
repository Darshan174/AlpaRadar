"""SEC Form 4 (insider trading) collector.

Fetches recent Form 4 filings from EDGAR and parses them into normalized
insider trade records. The EDGAR API is free with no key required.

Rate limit: 10 requests/second. Must include User-Agent header.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import httpx

from src.logging_config import get_logger

from ..base import BaseProvider, NormalizedRecord, RateLimiter, make_idempotency_key
from ..storage_adapter import store_insider_trade, store_raw_document, store_source_run
from .cik_lookup import SEC_USER_AGENT, lookup_cik

log = get_logger(__name__)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"


class InsiderTradeRecord(NormalizedRecord):
    """Normalized insider trade from SEC Form 4."""

    form_type: str = "4"
    filer_name: str = ""
    filer_title: str = ""
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    transaction_date: str = ""
    transaction_type: str = ""  # P=Purchase, S=Sale, A=Grant, etc.
    shares: float = 0.0
    price_per_share: float | None = None
    total_value: float | None = None
    shares_owned_after: float | None = None
    is_direct: bool = True
    accession_number: str = ""
    filing_date: str = ""


class Form4Collector(BaseProvider):
    """Collects and parses SEC Form 4 insider trading filings."""

    source_name = "sec_form4"

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
        """Fetch recent Form 4 filings for a ticker and return normalized records."""
        run = self.start_run(ticker)
        days_back = kwargs.get("days_back", 90)
        max_filings = kwargs.get("max_filings", 20)

        try:
            cik_info = await lookup_cik(ticker)
            if not cik_info:
                self.fail_run(run, f"CIK not found for {ticker}")
                await store_source_run(run)
                return []

            filings = await self._fetch_recent_form4s(
                cik_info["cik_padded"], cik_info["cik"], days_back, max_filings
            )
            records = []
            for filing in filings:
                parsed = await self._parse_form4_filing(
                    filing, ticker, cik_info["company_name"], cik_info["cik"]
                )
                records.extend(parsed)

            stored = 0
            for rec in records:
                trade_data = self._to_storage_dict(rec)
                was_new = await store_insider_trade(trade_data)
                if was_new:
                    stored += 1

            self.complete_run(run, len(records), stored)
            await store_source_run(run)
            return records

        except Exception as e:
            self.fail_run(run, str(e))
            await store_source_run(run)
            log.error("form4_collect_failed", ticker=ticker, error=str(e))
            return []

    async def _fetch_recent_form4s(
        self, cik_padded: str, cik: str, days_back: int, max_filings: int
    ) -> list[dict[str, Any]]:
        """Fetch recent Form 4 filing metadata from EDGAR submissions."""
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

        cutoff = datetime.utcnow().date()
        from datetime import timedelta

        cutoff_date = cutoff - timedelta(days=days_back)

        filings = []
        for i, form_type in enumerate(forms):
            if form_type not in ("4", "4/A"):
                continue
            filing_date = dates[i] if i < len(dates) else ""
            if filing_date and filing_date < cutoff_date.isoformat():
                continue
            if len(filings) >= max_filings:
                break

            accession = accessions[i] if i < len(accessions) else ""
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""

            filings.append(
                {
                    "form_type": form_type,
                    "filing_date": filing_date,
                    "accession_number": accession,
                    "primary_document": primary_doc,
                    "cik": cik,
                    "accession_path": accession.replace("-", ""),
                }
            )

        log.info("form4_filings_found", cik=cik, count=len(filings))
        return filings

    async def _parse_form4_filing(
        self,
        filing: dict[str, Any],
        ticker: str,
        company_name: str,
        cik: str,
    ) -> list[InsiderTradeRecord]:
        """Fetch and parse a single Form 4 XML filing."""
        accession_path = filing["accession_path"]
        primary_doc = filing["primary_document"]
        if not primary_doc:
            return []

        doc_url = f"{ARCHIVES_BASE}/{cik}/{accession_path}/{primary_doc}"

        self._throttle()
        client = await self._get_client()

        try:
            resp = await client.get(doc_url)
            resp.raise_for_status()
            content = resp.text
        except Exception as e:
            log.warning("form4_doc_fetch_failed", url=doc_url, error=str(e))
            return []

        # Store raw document
        await store_raw_document(
            {
                "idempotency_key": make_idempotency_key("form4_raw", filing["accession_number"]),
                "source_name": "sec_form4",
                "source_url": doc_url,
                "ticker": ticker,
                "doc_type": "form4_xml",
                "content": content[:50000],  # Truncate large documents
                "fetched_at": datetime.utcnow().isoformat(),
            }
        )

        return self._parse_form4_xml(content, ticker, company_name, cik, filing, doc_url)

    def _parse_form4_xml(
        self,
        xml_content: str,
        ticker: str,
        company_name: str,
        cik: str,
        filing: dict[str, Any],
        source_url: str,
    ) -> list[InsiderTradeRecord]:
        """Parse Form 4 XML into normalized records."""
        records = []
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            log.warning("form4_xml_parse_error", error=str(e), ticker=ticker)
            return []

        # Namespace handling — Form 4 XML may or may not use namespaces
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Get reporting owner info
        owner_el = root.find(f".//{ns}reportingOwner")
        filer_name = ""
        filer_title = ""
        is_director = False
        is_officer = False
        is_ten_pct = False

        if owner_el is not None:
            owner_id = owner_el.find(f"{ns}reportingOwnerId")
            if owner_id is not None:
                name_el = owner_id.find(f"{ns}rptOwnerName")
                filer_name = name_el.text if name_el is not None and name_el.text else ""

            relationship = owner_el.find(f"{ns}reportingOwnerRelationship")
            if relationship is not None:
                is_director = _bool_text(relationship.find(f"{ns}isDirector"))
                is_officer = _bool_text(relationship.find(f"{ns}isOfficer"))
                is_ten_pct = _bool_text(relationship.find(f"{ns}isTenPercentOwner"))
                title_el = relationship.find(f"{ns}officerTitle")
                filer_title = title_el.text if title_el is not None and title_el.text else ""

        # Parse non-derivative transactions
        for txn in root.findall(f".//{ns}nonDerivativeTransaction"):
            record = self._parse_transaction(
                txn, ns, ticker, company_name, cik, filing, source_url,
                filer_name, filer_title, is_director, is_officer, is_ten_pct,
                is_derivative=False,
            )
            if record:
                records.append(record)

        # Parse derivative transactions
        for txn in root.findall(f".//{ns}derivativeTransaction"):
            record = self._parse_transaction(
                txn, ns, ticker, company_name, cik, filing, source_url,
                filer_name, filer_title, is_director, is_officer, is_ten_pct,
                is_derivative=True,
            )
            if record:
                records.append(record)

        log.debug("form4_parsed", ticker=ticker, transactions=len(records))
        return records

    def _parse_transaction(
        self,
        txn_el: ET.Element,
        ns: str,
        ticker: str,
        company_name: str,
        cik: str,
        filing: dict[str, Any],
        source_url: str,
        filer_name: str,
        filer_title: str,
        is_director: bool,
        is_officer: bool,
        is_ten_pct: bool,
        is_derivative: bool,
    ) -> InsiderTradeRecord | None:
        """Parse a single transaction element from Form 4 XML."""
        # Transaction date
        date_el = txn_el.find(f".//{ns}transactionDate/{ns}value")
        txn_date = date_el.text if date_el is not None and date_el.text else filing.get("filing_date", "")

        # Transaction coding
        coding_el = txn_el.find(f".//{ns}transactionCoding")
        txn_code = ""
        if coding_el is not None:
            code_el = coding_el.find(f"{ns}transactionCode")
            txn_code = code_el.text if code_el is not None and code_el.text else ""

        # Shares
        shares_el = txn_el.find(f".//{ns}transactionAmounts/{ns}transactionShares/{ns}value")
        shares = _float_text(shares_el)

        # Price
        price_el = txn_el.find(f".//{ns}transactionAmounts/{ns}transactionPricePerShare/{ns}value")
        price = _float_text(price_el)

        # Acquired/disposed
        ad_el = txn_el.find(
            f".//{ns}transactionAmounts/{ns}transactionAcquiredDisposedCode/{ns}value"
        )
        acquired_disposed = ad_el.text if ad_el is not None and ad_el.text else ""

        # Post-transaction holdings
        holdings_el = txn_el.find(
            f".//{ns}postTransactionAmounts/{ns}sharesOwnedFollowingTransaction/{ns}value"
        )
        shares_after = _float_text(holdings_el)

        # Direct/indirect
        ownership_el = txn_el.find(f".//{ns}ownershipNature/{ns}directOrIndirectOwnership/{ns}value")
        is_direct = True
        if ownership_el is not None and ownership_el.text:
            is_direct = ownership_el.text.upper() == "D"

        total_value = None
        if shares and price:
            total_value = round(shares * price, 2)

        idempotency = make_idempotency_key(
            "form4", filing["accession_number"], filer_name, txn_date, txn_code, str(shares)
        )

        return InsiderTradeRecord(
            idempotency_key=idempotency,
            source_name="sec_form4",
            source_url=source_url,
            source_timestamp=_parse_date(txn_date),
            ticker=ticker.upper(),
            company_name=company_name,
            cik=cik,
            filer_name=filer_name,
            filer_title=filer_title,
            is_director=is_director,
            is_officer=is_officer,
            is_ten_percent_owner=is_ten_pct,
            transaction_date=txn_date,
            transaction_type=txn_code,
            shares=shares or 0.0,
            price_per_share=price,
            total_value=total_value,
            shares_owned_after=shares_after,
            is_direct=is_direct,
            accession_number=filing["accession_number"],
            filing_date=filing.get("filing_date", ""),
            raw_payload={
                "acquired_disposed": acquired_disposed,
                "is_derivative": is_derivative,
                "filing_date": filing.get("filing_date", ""),
            },
        )

    def _to_storage_dict(self, record: InsiderTradeRecord) -> dict[str, Any]:
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
            "filer_name": record.filer_name,
            "filer_title": record.filer_title,
            "is_director": record.is_director,
            "is_officer": record.is_officer,
            "is_ten_percent_owner": record.is_ten_percent_owner,
            "transaction_date": record.transaction_date,
            "transaction_type": record.transaction_type,
            "shares": record.shares,
            "price_per_share": record.price_per_share,
            "total_value": record.total_value,
            "shares_owned_after": record.shares_owned_after,
            "is_direct": record.is_direct,
            "accession_number": record.accession_number,
            "filing_date": record.filing_date,
            "raw_payload": record.raw_payload,
            "ingested_at": record.ingested_at.isoformat(),
        }


def _bool_text(el: ET.Element | None) -> bool:
    if el is None or el.text is None:
        return False
    return el.text.strip() in ("1", "true", "True")


def _float_text(el: ET.Element | None) -> float | None:
    if el is None or el.text is None:
        return None
    try:
        return float(el.text.strip())
    except ValueError:
        return None


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
