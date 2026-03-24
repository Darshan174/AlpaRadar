"""Thin storage adapter for ingestion records.

Wraps Agent 1's storage helpers if available, otherwise provides local stubs
that log records without persisting to Supabase. This lets ingestion development
proceed independently of the storage layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.logging_config import get_logger

from .base import NormalizedRecord, SourceRun

log = get_logger(__name__)

# In-memory store for development/testing when Supabase isn't available
_memory_store: dict[str, list[dict[str, Any]]] = {
    "source_runs": [],
    "insider_trades": [],
    "job_postings": [],
    "filing_events": [],
    "transcript_chunks": [],
    "raw_documents": [],
}


def _try_supabase():
    """Try to get the Supabase client; return None if not configured."""
    try:
        from src.storage.supabase import get_client

        return get_client()
    except Exception:
        return None


async def store_source_run(run: SourceRun) -> None:
    """Persist a source run record."""
    data = {
        "id": run.id,
        "source_name": run.source_name,
        "ticker": run.ticker,
        "status": run.status,
        "records_fetched": run.records_fetched,
        "records_stored": run.records_stored,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "metadata": run.metadata,
    }
    client = _try_supabase()
    if client:
        try:
            client.table("source_runs").upsert(data).execute()
            return
        except Exception as e:
            log.warning("source_run_store_fallback", error=str(e))
    _memory_store["source_runs"].append(data)
    log.debug("source_run_stored_memory", run_id=run.id)


async def store_insider_trade(record: dict[str, Any]) -> bool:
    """Store an insider trade record. Returns True if new, False if duplicate."""
    client = _try_supabase()
    if client:
        try:
            client.table("insider_trades").upsert(
                record, on_conflict="idempotency_key"
            ).execute()
            return True
        except Exception as e:
            log.warning("insider_trade_store_fallback", error=str(e))

    key = record.get("idempotency_key", "")
    existing_keys = {r.get("idempotency_key") for r in _memory_store["insider_trades"]}
    if key in existing_keys:
        return False
    _memory_store["insider_trades"].append(record)
    return True


async def store_filing_event(record: dict[str, Any]) -> bool:
    """Store a filing event record. Returns True if new, False if duplicate."""
    client = _try_supabase()
    if client:
        try:
            client.table("filing_events").upsert(
                record, on_conflict="idempotency_key"
            ).execute()
            return True
        except Exception as e:
            log.warning("filing_event_store_fallback", error=str(e))

    key = record.get("idempotency_key", "")
    existing_keys = {r.get("idempotency_key") for r in _memory_store["filing_events"]}
    if key in existing_keys:
        return False
    _memory_store["filing_events"].append(record)
    return True


async def store_job_posting(record: dict[str, Any]) -> bool:
    """Store a job posting record. Returns True if new, False if duplicate."""
    client = _try_supabase()
    if client:
        try:
            client.table("job_postings").upsert(
                record, on_conflict="idempotency_key"
            ).execute()
            return True
        except Exception as e:
            log.warning("job_posting_store_fallback", error=str(e))

    key = record.get("idempotency_key", "")
    existing_keys = {r.get("idempotency_key") for r in _memory_store["job_postings"]}
    if key in existing_keys:
        return False
    _memory_store["job_postings"].append(record)
    return True


async def store_transcript_chunk(record: dict[str, Any]) -> bool:
    """Store a transcript chunk. Returns True if new, False if duplicate."""
    client = _try_supabase()
    if client:
        try:
            client.table("transcript_chunks").upsert(
                record, on_conflict="idempotency_key"
            ).execute()
            return True
        except Exception as e:
            log.warning("transcript_store_fallback", error=str(e))

    key = record.get("idempotency_key", "")
    existing_keys = {r.get("idempotency_key") for r in _memory_store["transcript_chunks"]}
    if key in existing_keys:
        return False
    _memory_store["transcript_chunks"].append(record)
    return True


async def store_raw_document(record: dict[str, Any]) -> None:
    """Store a raw document payload for audit trail."""
    client = _try_supabase()
    if client:
        try:
            client.table("raw_documents").upsert(
                record, on_conflict="idempotency_key"
            ).execute()
            return
        except Exception as e:
            log.warning("raw_doc_store_fallback", error=str(e))
    _memory_store["raw_documents"].append(record)


def get_memory_store() -> dict[str, list[dict[str, Any]]]:
    """Access the in-memory store (for testing)."""
    return _memory_store


def clear_memory_store() -> None:
    """Reset the in-memory store (for testing)."""
    for v in _memory_store.values():
        v.clear()
