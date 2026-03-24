"""FMP (Financial Modeling Prep) earnings transcript adapter.

This is a stub provider for MVP. FMP free tier allows 250 calls/day.
Requires FMP_API_KEY env var. Falls back to fixtures when unavailable.

Next steps for full implementation:
- Parse transcript text into speaker-attributed chunks
- Store chunks with speaker role metadata (CEO, CFO, analyst, etc.)
- Index sentence-level embeddings for RAG retrieval
- Add quarterly comparison (tone shift detection)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from src.logging_config import get_logger

from ..base import BaseProvider, NormalizedRecord, make_idempotency_key
from ..storage_adapter import store_source_run, store_transcript_chunk

log = get_logger(__name__)

FMP_BASE = "https://financialmodelingprep.com/api/v3"
FIXTURES_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "transcripts"


class TranscriptChunkRecord(NormalizedRecord):
    """A chunk of an earnings call transcript."""

    quarter: str = ""  # e.g. "Q4 2024"
    fiscal_year: int | None = None
    speaker_name: str = ""
    speaker_role: str = ""  # ceo, cfo, analyst, other
    chunk_index: int = 0
    text: str = ""
    earnings_date: str = ""


class TranscriptCollector(BaseProvider):
    """Collects earnings call transcripts from FMP or fixtures."""

    source_name = "fmp_transcripts"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("FMP_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def collect(self, ticker: str, **kwargs: Any) -> list[NormalizedRecord]:
        """Fetch recent earnings transcripts for a ticker."""
        run = self.start_run(ticker)
        limit = kwargs.get("limit", 2)

        try:
            raw_transcripts = await self._fetch_transcripts(ticker, limit)
            records = []
            for transcript in raw_transcripts:
                chunks = self._parse_into_chunks(transcript, ticker)
                records.extend(chunks)

            stored = 0
            for rec in records:
                chunk_data = self._to_storage_dict(rec)
                was_new = await store_transcript_chunk(chunk_data)
                if was_new:
                    stored += 1

            self.complete_run(run, len(records), stored)
            await store_source_run(run)
            return records

        except Exception as e:
            self.fail_run(run, str(e))
            await store_source_run(run)
            log.error("transcript_collect_failed", ticker=ticker, error=str(e))
            return []

    async def _fetch_transcripts(
        self, ticker: str, limit: int
    ) -> list[dict[str, Any]]:
        """Fetch transcripts from FMP API or fixture fallback."""
        if self._api_key:
            try:
                return await self._fetch_from_fmp(ticker, limit)
            except Exception as e:
                log.warning("fmp_fetch_failed_using_fixture", ticker=ticker, error=str(e))

        return self._load_fixture(ticker)

    async def _fetch_from_fmp(
        self, ticker: str, limit: int
    ) -> list[dict[str, Any]]:
        """Fetch from FMP API."""
        url = f"{FMP_BASE}/earning_call_transcript/{ticker.upper()}"
        params = {"apikey": self._api_key, "limit": limit}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, list):
            log.info("fmp_transcripts_fetched", ticker=ticker, count=len(data))
            return data
        return []

    def _load_fixture(self, ticker: str) -> list[dict[str, Any]]:
        """Load fixture transcript data."""
        fixture_file = FIXTURES_DIR / f"{ticker.lower()}_transcript.json"
        if not fixture_file.exists():
            fixture_file = FIXTURES_DIR / "sample_transcript.json"
        if not fixture_file.exists():
            log.warning("no_transcript_fixtures", ticker=ticker)
            return []

        data = json.loads(fixture_file.read_text())
        return data if isinstance(data, list) else [data]

    def _parse_into_chunks(
        self, transcript: dict[str, Any], ticker: str
    ) -> list[TranscriptChunkRecord]:
        """Parse a transcript into speaker-attributed chunks.

        For MVP, we do basic paragraph-level chunking. Full implementation
        would parse speaker labels and segment by dialogue turns.
        """
        content = transcript.get("content", "")
        quarter = transcript.get("quarter", "")
        year = transcript.get("year")
        date_str = transcript.get("date", "")

        if not content:
            return []

        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content]

        # Chunk into ~500 char segments
        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > 500 and current_chunk:
                chunks.append(
                    TranscriptChunkRecord(
                        idempotency_key=make_idempotency_key(
                            "transcript", ticker, str(quarter), str(year), str(chunk_idx)
                        ),
                        source_name=self.source_name,
                        source_url=f"fmp://transcript/{ticker}/{quarter}/{year}",
                        source_timestamp=_parse_date(date_str),
                        ticker=ticker.upper(),
                        quarter=f"Q{quarter} {year}" if quarter and year else "",
                        fiscal_year=int(year) if year else None,
                        chunk_index=chunk_idx,
                        text=current_chunk,
                        earnings_date=date_str,
                        raw_payload={"quarter": quarter, "year": year},
                    )
                )
                chunk_idx += 1
                current_chunk = para
            else:
                current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para

        if current_chunk:
            chunks.append(
                TranscriptChunkRecord(
                    idempotency_key=make_idempotency_key(
                        "transcript", ticker, str(quarter), str(year), str(chunk_idx)
                    ),
                    source_name=self.source_name,
                    source_url=f"fmp://transcript/{ticker}/{quarter}/{year}",
                    source_timestamp=_parse_date(date_str),
                    ticker=ticker.upper(),
                    quarter=f"Q{quarter} {year}" if quarter and year else "",
                    fiscal_year=int(year) if year else None,
                    chunk_index=chunk_idx,
                    text=current_chunk,
                    earnings_date=date_str,
                    raw_payload={"quarter": quarter, "year": year},
                )
            )

        return chunks

    def _to_storage_dict(self, record: TranscriptChunkRecord) -> dict[str, Any]:
        return {
            "idempotency_key": record.idempotency_key,
            "source_name": record.source_name,
            "source_url": record.source_url,
            "source_timestamp": record.source_timestamp.isoformat() if record.source_timestamp else None,
            "ticker": record.ticker,
            "quarter": record.quarter,
            "fiscal_year": record.fiscal_year,
            "speaker_name": record.speaker_name,
            "speaker_role": record.speaker_role,
            "chunk_index": record.chunk_index,
            "text": record.text,
            "earnings_date": record.earnings_date,
            "raw_payload": record.raw_payload,
            "ingested_at": record.ingested_at.isoformat(),
        }


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
