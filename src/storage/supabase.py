"""Supabase storage layer — signals, company profiles, watchlists, and vector embeddings."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from supabase import Client, create_client

from src.config import settings
from src.core.exceptions import StorageError
from src.core.models import (
    CompanyProfile,
    FusedInsight,
    Signal,
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
        "updated_at": datetime.utcnow().isoformat(),
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
