"""Supabase storage layer — signals, company profiles, watchlists, and vector embeddings."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client, create_client

from src.config import settings
from src.core.exceptions import StorageError
from src.core.models import (
    Brief,
    Company,
    CompanyProfile,
    FilingEvent,
    FusedInsight,
    InsiderTrade,
    JobPosting,
    RawDocument,
    Signal,
    SourceRun,
    SourceRunStatus,
    TranscriptChunk,
    WatchlistAlert,
    WatchlistItem,
)
from src.logging_config import get_logger
from src.storage.embeddings import embed_text

log = get_logger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise StorageError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ── Signals ────────────────────────────────────────────────────────────────────


async def store_signal(signal: Signal) -> str:
    """Store a detected signal with its embedding for RAG retrieval."""
    client = get_client()
    embedding = embed_text(f"{signal.headline} {signal.detail}")

    data = {
        "id": signal.id,
        "type": signal.type.value,
        "strength": signal.strength.value,
        "sentiment": signal.sentiment.value,
        "ticker": signal.ticker,
        "company_name": signal.company_name,
        "headline": signal.headline,
        "detail": signal.detail,
        "score": signal.score,
        "data": signal.data,
        "embedding": embedding,
        "detected_at": signal.detected_at.isoformat(),
    }

    result = client.table("signals").upsert(data).execute()
    log.info("signal_stored", signal_id=signal.id, ticker=signal.ticker)
    return signal.id


async def get_signals(
    ticker: str | None = None,
    signal_type: str | None = None,
    min_score: float = 0.0,
    limit: int = 50,
) -> list[dict]:
    """Retrieve stored signals with optional filters."""
    client = get_client()
    query = client.table("signals").select("*")

    if ticker:
        query = query.eq("ticker", ticker.upper())
    if signal_type:
        query = query.eq("type", signal_type)
    if min_score > 0:
        query = query.gte("score", min_score)

    result = query.order("detected_at", desc=True).limit(limit).execute()
    return result.data


async def search_similar_signals(query_text: str, limit: int = 10) -> list[dict]:
    """Semantic search over stored signals using pgvector."""
    client = get_client()
    embedding = embed_text(query_text)

    result = client.rpc(
        "match_signals",
        {"query_embedding": embedding, "match_count": limit},
    ).execute()
    return result.data


# ── Company Profiles ───────────────────────────────────────────────────────────


async def store_company_profile(company: CompanyProfile) -> None:
    """Store or update a company profile."""
    client = get_client()
    data = {
        "domain": company.domain,
        "name": company.name,
        "ticker": company.ticker,
        "industry": company.industry,
        "sector": company.sector,
        "country": company.country,
        "total_headcount": company.total_headcount,
        "headcount_trend_pct": company.headcount_trend.change_pct if company.headcount_trend else None,
        "funding_total_usd": company.funding_total_usd,
        "competitors": company.competitors,
        "profile_json": company.model_dump(mode="json"),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    client.table("company_profiles").upsert(data, on_conflict="domain").execute()
    log.info("company_stored", domain=company.domain)


async def get_company_profile(domain: str) -> dict | None:
    """Retrieve a stored company profile."""
    client = get_client()
    result = (
        client.table("company_profiles")
        .select("*")
        .eq("domain", domain)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Fused Insights ─────────────────────────────────────────────────────────────


async def store_insight(insight: FusedInsight) -> None:
    """Store a complete fused insight."""
    client = get_client()
    summary_text = (
        f"{insight.company_name} ({insight.ticker}): "
        f"{insight.sentiment.value} — score {insight.composite_score}. "
        f"{len(insight.signals)} signals detected. {insight.summary}"
    )
    embedding = embed_text(summary_text)

    data = {
        "ticker": insight.ticker,
        "company_name": insight.company_name,
        "composite_score": insight.composite_score,
        "sentiment": insight.sentiment.value,
        "signal_count": insight.signal_count,
        "signal_ids": [s.id for s in insight.signals],
        "summary": insight.summary,
        "llm_analysis": insight.llm_analysis,
        "insight_json": insight.model_dump(mode="json"),
        "embedding": embedding,
        "generated_at": insight.generated_at.isoformat(),
    }
    client.table("insights").upsert(data, on_conflict="ticker").execute()
    log.info("insight_stored", ticker=insight.ticker, score=insight.composite_score)


async def search_insights(query_text: str, limit: int = 5) -> list[dict]:
    """Semantic search over stored insights."""
    client = get_client()
    embedding = embed_text(query_text)

    result = client.rpc(
        "match_insights",
        {"query_embedding": embedding, "match_count": limit},
    ).execute()
    return result.data


# ── Watchlist ──────────────────────────────────────────────────────────────────


async def add_to_watchlist(item: WatchlistItem) -> None:
    client = get_client()
    data = {
        "user_id": item.user_id,
        "ticker": item.ticker,
        "company_name": item.company_name,
        "alert_on": [t.value for t in item.alert_on],
        "added_at": item.added_at.isoformat(),
    }
    client.table("watchlist").upsert(data, on_conflict="user_id,ticker").execute()


async def get_watchlist(user_id: str) -> list[dict]:
    client = get_client()
    result = (
        client.table("watchlist")
        .select("*")
        .eq("user_id", user_id)
        .order("added_at", desc=True)
        .execute()
    )
    return result.data


async def remove_from_watchlist(user_id: str, ticker: str) -> None:
    client = get_client()
    client.table("watchlist").delete().eq("user_id", user_id).eq("ticker", ticker).execute()


async def get_all_watched_tickers() -> list[str]:
    """Get all unique tickers across all watchlists (for scheduled ingestion)."""
    client = get_client()
    result = client.table("watchlist").select("ticker").execute()
    return list({row["ticker"] for row in result.data})


# ── Source Runs ───────────────────────────────────────────────────────────────


async def create_source_run(run: SourceRun) -> str:
    """Create a source run record, returns the run ID."""
    client = get_client()
    data = {
        "source_name": run.source_name,
        "ticker": run.ticker,
        "status": run.status.value,
        "metadata": run.metadata,
        "started_at": run.started_at.isoformat(),
    }
    result = client.table("source_runs").insert(data).execute()
    run_id = result.data[0]["id"]
    log.info("source_run_created", run_id=run_id, source=run.source_name, ticker=run.ticker)
    return run_id


async def complete_source_run(
    run_id: str,
    status: SourceRunStatus,
    records_fetched: int = 0,
    records_stored: int = 0,
    error_message: str | None = None,
) -> None:
    """Mark a source run as completed or failed."""
    client = get_client()
    data: dict[str, Any] = {
        "status": status.value,
        "records_fetched": records_fetched,
        "records_stored": records_stored,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    if error_message:
        data["error_message"] = error_message
    client.table("source_runs").update(data).eq("id", run_id).execute()
    log.info("source_run_completed", run_id=run_id, status=status.value)


# ── Raw Documents ─────────────────────────────────────────────────────────────


async def store_raw_document(doc: RawDocument) -> str | None:
    """Store a raw document. Returns ID, or None if duplicate (content_hash conflict)."""
    client = get_client()
    data = {
        "source_name": doc.source_name,
        "source_url": doc.source_url,
        "ticker": doc.ticker,
        "doc_type": doc.doc_type,
        "content_hash": doc.content_hash,
        "raw_payload": doc.raw_payload,
        "fetched_at": doc.fetched_at.isoformat(),
        "source_run_id": str(doc.source_run_id) if doc.source_run_id else None,
    }
    result = (
        client.table("raw_documents")
        .upsert(data, on_conflict="source_name,content_hash")
        .execute()
    )
    doc_id = result.data[0]["id"]
    return doc_id


# ── Insider Trades ────────────────────────────────────────────────────────────


async def upsert_insider_trade(trade: InsiderTrade) -> str:
    """Upsert an insider trade record. Returns the record ID."""
    client = get_client()
    data = {
        "ticker": trade.ticker,
        "company_name": trade.company_name,
        "cik": trade.cik,
        "filer_name": trade.filer_name,
        "filer_title": trade.filer_title,
        "is_officer": trade.is_officer,
        "is_director": trade.is_director,
        "is_ten_pct_owner": trade.is_ten_pct_owner,
        "transaction_type": trade.transaction_type.value,
        "transaction_code": trade.transaction_code,
        "shares": trade.shares,
        "price_per_share": trade.price_per_share,
        "total_value": trade.total_value,
        "shares_owned_after": trade.shares_owned_after,
        "filing_date": trade.filing_date.isoformat(),
        "transaction_date": trade.transaction_date.isoformat() if trade.transaction_date else None,
        "source_url": trade.source_url,
        "source_timestamp": trade.source_timestamp.isoformat() if trade.source_timestamp else None,
        "idempotency_key": trade.idempotency_key,
        "raw_document_id": str(trade.raw_document_id) if trade.raw_document_id else None,
    }
    result = (
        client.table("insider_trades")
        .upsert(data, on_conflict="idempotency_key")
        .execute()
    )
    trade_id = result.data[0]["id"]
    log.info("insider_trade_upserted", ticker=trade.ticker, filer=trade.filer_name)
    return trade_id


async def get_insider_trades(
    ticker: str,
    days_back: int = 90,
    transaction_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch insider trades for a ticker within a lookback window."""
    client = get_client()
    cutoff = (datetime.now(UTC) - timedelta(days=days_back)).date().isoformat()
    query = (
        client.table("insider_trades")
        .select("*")
        .eq("ticker", ticker.upper())
        .gte("filing_date", cutoff)
    )
    if transaction_type:
        query = query.eq("transaction_type", transaction_type)
    result = query.order("filing_date", desc=True).limit(limit).execute()
    return result.data


async def get_insider_buy_cluster(ticker: str, days_back: int = 90) -> list[dict]:
    """Fetch recent insider buys — primary query for insider_buy_cluster detector."""
    return await get_insider_trades(ticker, days_back=days_back, transaction_type="buy")


# ── Job Postings ──────────────────────────────────────────────────────────────


async def upsert_job_posting(posting: JobPosting) -> str:
    """Upsert a job posting. Returns the record ID."""
    client = get_client()
    data = {
        "ticker": posting.ticker,
        "company_name": posting.company_name,
        "title": posting.title,
        "department": posting.department,
        "seniority": posting.seniority,
        "location": posting.location,
        "is_remote": posting.is_remote,
        "description_snippet": posting.description_snippet,
        "source_name": posting.source_name,
        "source_url": posting.source_url,
        "posted_date": posting.posted_date.isoformat() if posting.posted_date else None,
        "first_seen_at": posting.first_seen_at.isoformat(),
        "last_seen_at": posting.last_seen_at.isoformat(),
        "is_active": posting.is_active,
        "idempotency_key": posting.idempotency_key,
        "raw_document_id": str(posting.raw_document_id) if posting.raw_document_id else None,
    }
    result = (
        client.table("job_postings")
        .upsert(data, on_conflict="idempotency_key")
        .execute()
    )
    posting_id = result.data[0]["id"]
    log.info("job_posting_upserted", ticker=posting.ticker, title=posting.title)
    return posting_id


async def get_job_postings(
    ticker: str,
    days_back: int = 90,
    active_only: bool = True,
    department: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Fetch job postings for a ticker within a lookback window."""
    client = get_client()
    cutoff = (datetime.now(UTC) - timedelta(days=days_back)).isoformat()
    query = (
        client.table("job_postings")
        .select("*")
        .eq("ticker", ticker.upper())
        .gte("first_seen_at", cutoff)
    )
    if active_only:
        query = query.eq("is_active", True)
    if department:
        query = query.eq("department", department)
    result = query.order("first_seen_at", desc=True).limit(limit).execute()
    return result.data


async def get_job_posting_counts(ticker: str, days_back: int = 90) -> dict[str, int]:
    """Count active job postings per department — primary query for hiring_momentum detector."""
    rows = await get_job_postings(ticker, days_back=days_back, active_only=True, limit=500)
    counts: dict[str, int] = {}
    for row in rows:
        dept = row.get("department", "unknown") or "unknown"
        counts[dept] = counts.get(dept, 0) + 1
    counts["_total"] = len(rows)
    return counts


# ── Filing Events ─────────────────────────────────────────────────────────────


async def upsert_filing_event(event: FilingEvent) -> str:
    """Upsert a filing event. Returns the record ID."""
    client = get_client()
    data = {
        "ticker": event.ticker,
        "company_name": event.company_name,
        "cik": event.cik,
        "filing_type": event.filing_type,
        "form_items": event.form_items,
        "filing_date": event.filing_date.isoformat(),
        "period_of_report": event.period_of_report.isoformat() if event.period_of_report else None,
        "headline": event.headline,
        "summary": event.summary,
        "source_url": event.source_url,
        "accession_number": event.accession_number,
        "source_timestamp": event.source_timestamp.isoformat() if event.source_timestamp else None,
        "idempotency_key": event.idempotency_key,
        "raw_document_id": str(event.raw_document_id) if event.raw_document_id else None,
    }
    result = (
        client.table("filing_events")
        .upsert(data, on_conflict="idempotency_key")
        .execute()
    )
    event_id = result.data[0]["id"]
    log.info("filing_event_upserted", ticker=event.ticker, filing_type=event.filing_type)
    return event_id


async def get_filing_events(
    ticker: str,
    days_back: int = 90,
    filing_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch filing events for a ticker within a lookback window."""
    client = get_client()
    cutoff = (datetime.now(UTC) - timedelta(days=days_back)).date().isoformat()
    query = (
        client.table("filing_events")
        .select("*")
        .eq("ticker", ticker.upper())
        .gte("filing_date", cutoff)
    )
    if filing_type:
        query = query.eq("filing_type", filing_type)
    result = query.order("filing_date", desc=True).limit(limit).execute()
    return result.data


async def get_material_filings(ticker: str, days_back: int = 90) -> list[dict]:
    """Fetch 8-K filings — primary query for filing_catalyst detector."""
    return await get_filing_events(ticker, days_back=days_back, filing_type="8-K")


# ── Transcript Chunks ─────────────────────────────────────────────────────────


async def upsert_transcript_chunk(chunk: TranscriptChunk) -> str:
    """Upsert a transcript chunk. Returns the record ID."""
    client = get_client()
    data = {
        "ticker": chunk.ticker,
        "company_name": chunk.company_name,
        "fiscal_quarter": chunk.fiscal_quarter,
        "call_date": chunk.call_date.isoformat(),
        "speaker_name": chunk.speaker_name,
        "speaker_role": chunk.speaker_role,
        "section": chunk.section,
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "word_count": chunk.word_count,
        "source_name": chunk.source_name,
        "source_url": chunk.source_url,
        "source_timestamp": chunk.source_timestamp.isoformat() if chunk.source_timestamp else None,
        "idempotency_key": chunk.idempotency_key,
        "raw_document_id": str(chunk.raw_document_id) if chunk.raw_document_id else None,
    }
    result = (
        client.table("transcript_chunks")
        .upsert(data, on_conflict="idempotency_key")
        .execute()
    )
    chunk_id = result.data[0]["id"]
    return chunk_id


async def get_transcript_chunks(
    ticker: str,
    fiscal_quarter: str | None = None,
    section: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Fetch transcript chunks for a ticker, optionally filtered by quarter/section."""
    client = get_client()
    query = client.table("transcript_chunks").select("*").eq("ticker", ticker.upper())
    if fiscal_quarter:
        query = query.eq("fiscal_quarter", fiscal_quarter)
    if section:
        query = query.eq("section", section)
    result = query.order("call_date", desc=True).order("chunk_index").limit(limit).execute()
    return result.data


# ── Companies ─────────────────────────────────────────────────────────────────


async def upsert_company(company: Company) -> str:
    """Upsert a company in the universe. Returns ticker."""
    client = get_client()
    data = {
        "ticker": company.ticker,
        "name": company.name,
        "cik": company.cik,
        "sector": company.sector,
        "industry": company.industry,
        "domain": company.domain,
        "market_cap_bucket": company.market_cap_bucket,
        "in_universe": company.in_universe,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    client.table("companies").upsert(data, on_conflict="ticker").execute()
    log.info("company_upserted", ticker=company.ticker)
    return company.ticker


async def get_universe_tickers() -> list[str]:
    """Get all tickers in the tracked MVP universe."""
    client = get_client()
    result = (
        client.table("companies")
        .select("ticker")
        .eq("in_universe", True)
        .execute()
    )
    return [row["ticker"] for row in result.data]


async def get_company(ticker: str) -> dict | None:
    """Get company details by ticker."""
    client = get_client()
    result = (
        client.table("companies")
        .select("*")
        .eq("ticker", ticker.upper())
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Briefs ────────────────────────────────────────────────────────────────────


async def store_brief(brief: Brief) -> str:
    """Store an AI-generated brief. Returns brief ID."""
    client = get_client()
    data = {
        "ticker": brief.ticker,
        "signal_id": brief.signal_id,
        "brief_type": brief.brief_type,
        "headline": brief.headline,
        "body": brief.body,
        "evidence_summary": brief.evidence_summary,
        "model_used": brief.model_used,
        "prompt_tokens": brief.prompt_tokens,
        "completion_tokens": brief.completion_tokens,
        "generated_at": brief.generated_at.isoformat(),
    }
    result = client.table("briefs").insert(data).execute()
    brief_id = result.data[0]["id"]
    log.info("brief_stored", ticker=brief.ticker, brief_id=brief_id)
    return brief_id


async def get_briefs(
    ticker: str | None = None,
    signal_id: str | None = None,
    brief_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Fetch briefs with optional filters."""
    client = get_client()
    query = client.table("briefs").select("*")
    if ticker:
        query = query.eq("ticker", ticker.upper())
    if signal_id:
        query = query.eq("signal_id", signal_id)
    if brief_type:
        query = query.eq("brief_type", brief_type)
    result = query.order("generated_at", desc=True).limit(limit).execute()
    return result.data


# ── Signal Detail / Company Detail (composite queries) ────────────────────────


async def get_signal_detail(signal_id: str) -> dict | None:
    """Get a signal with its associated brief and evidence context."""
    client = get_client()
    signal_result = (
        client.table("signals").select("*").eq("id", signal_id).limit(1).execute()
    )
    if not signal_result.data:
        return None

    signal = signal_result.data[0]
    briefs = await get_briefs(signal_id=signal_id, limit=1)
    signal["brief"] = briefs[0] if briefs else None
    return signal


async def get_company_detail(ticker: str) -> dict:
    """Get company overview with recent signals, briefs, and data counts."""
    ticker = ticker.upper()
    company = await get_company(ticker)
    profile = await get_company_profile_by_ticker(ticker)
    signals = await get_signals(ticker=ticker, limit=10)
    briefs_data = await get_briefs(ticker=ticker, limit=5)

    return {
        "company": company,
        "profile": profile,
        "recent_signals": signals,
        "recent_briefs": briefs_data,
    }


async def get_company_profile_by_ticker(ticker: str) -> dict | None:
    """Retrieve a company profile by ticker (not domain)."""
    client = get_client()
    result = (
        client.table("company_profiles")
        .select("*")
        .eq("ticker", ticker.upper())
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
