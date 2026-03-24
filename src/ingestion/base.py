"""Base provider interface with source-run logging, retry, and rate-limit support."""

from __future__ import annotations

import abc
import hashlib
import time
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.logging_config import get_logger

log = get_logger(__name__)


class SourceRun(BaseModel):
    """Tracks a single collection run for audit and debugging."""

    id: str = ""
    source_name: str
    ticker: str
    status: str = "started"  # started, completed, failed
    records_fetched: int = 0
    records_stored: int = 0
    error_message: str = ""
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRecord(BaseModel):
    """Base for all normalized ingestion records."""

    idempotency_key: str = ""
    source_name: str = ""
    source_url: str = ""
    source_timestamp: datetime | None = None
    ticker: str = ""
    company_name: str = ""
    cik: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


def make_idempotency_key(*parts: str) -> str:
    """Create a deterministic dedupe key from component parts."""
    combined = "|".join(str(p) for p in parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:20]


class RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, requests_per_second: float = 10.0):
        self._interval = 1.0 / requests_per_second
        self._last_request = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
        self._last_request = time.monotonic()


class BaseProvider(abc.ABC):
    """Abstract base for all data providers."""

    source_name: str = "unknown"
    rate_limiter: RateLimiter | None = None

    @abc.abstractmethod
    async def collect(self, ticker: str, **kwargs: Any) -> list[NormalizedRecord]:
        """Collect and normalize records for a ticker."""
        ...

    def _throttle(self) -> None:
        if self.rate_limiter:
            self.rate_limiter.wait()

    def start_run(self, ticker: str) -> SourceRun:
        run = SourceRun(
            id=make_idempotency_key(self.source_name, ticker, datetime.utcnow().isoformat()),
            source_name=self.source_name,
            ticker=ticker,
        )
        log.info("source_run_started", source=self.source_name, ticker=ticker, run_id=run.id)
        return run

    def complete_run(self, run: SourceRun, records_fetched: int, records_stored: int) -> SourceRun:
        run.status = "completed"
        run.records_fetched = records_fetched
        run.records_stored = records_stored
        run.completed_at = datetime.utcnow()
        log.info(
            "source_run_completed",
            source=run.source_name,
            ticker=run.ticker,
            fetched=records_fetched,
            stored=records_stored,
        )
        return run

    def fail_run(self, run: SourceRun, error: str) -> SourceRun:
        run.status = "failed"
        run.error_message = error
        run.completed_at = datetime.utcnow()
        log.error("source_run_failed", source=run.source_name, ticker=run.ticker, error=error)
        return run
