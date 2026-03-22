"""RAG retriever — provides context for LLM analysis from stored signals and insights."""

from __future__ import annotations

from src.core.models import CompanyProfile, RAGContext, Signal
from src.logging_config import get_logger
from src.storage import supabase as db

log = get_logger(__name__)


async def retrieve_context(
    query: str,
    ticker: str | None = None,
    max_signals: int = 10,
    max_insights: int = 5,
) -> RAGContext:
    """Retrieve relevant context for a query from stored data.

    Combines:
    1. Semantic search over signals (pgvector)
    2. Semantic search over insights
    3. Company profile lookup
    """
    context = RAGContext(query=query)

    # 1. Semantic search over signals
    try:
        similar_signals = await db.search_similar_signals(query, limit=max_signals)
        for row in similar_signals:
            chunk = f"[{row.get('type', '')}] {row.get('headline', '')} — {row.get('detail', '')}"
            context.retrieved_chunks.append(chunk)
            if "similarity" in row:
                context.relevance_scores.append(row["similarity"])
    except Exception as e:
        log.warning("rag_signal_search_failed", error=str(e))

    # 2. Semantic search over insights
    try:
        similar_insights = await db.search_insights(query, limit=max_insights)
        for row in similar_insights:
            chunk = (
                f"[Insight] {row.get('company_name', '')} ({row.get('ticker', '')}): "
                f"Score {row.get('composite_score', 0)} — {row.get('summary', '')}"
            )
            context.retrieved_chunks.append(chunk)
    except Exception as e:
        log.warning("rag_insight_search_failed", error=str(e))

    # 3. Company profile
    if ticker:
        try:
            from src.ingestion.market.price import ticker_to_domain

            domain = ticker_to_domain(ticker)
            if domain:
                profile_data = await db.get_company_profile(domain)
                if profile_data and "profile_json" in profile_data:
                    context.company_profile = CompanyProfile.model_validate(
                        profile_data["profile_json"]
                    )
        except Exception as e:
            log.warning("rag_company_lookup_failed", ticker=ticker, error=str(e))

    log.info(
        "rag_context_retrieved",
        query_len=len(query),
        chunks=len(context.retrieved_chunks),
        has_company=context.company_profile is not None,
    )
    return context


def format_context_for_llm(context: RAGContext) -> str:
    """Format RAG context into a string for LLM prompt injection."""
    parts: list[str] = []

    if context.company_profile:
        cp = context.company_profile
        parts.append(f"## Company: {cp.name}")
        parts.append(f"Industry: {cp.industry} | Sector: {cp.sector}")
        if cp.total_headcount:
            parts.append(f"Headcount: {cp.total_headcount:,}")
        if cp.headcount_trend:
            parts.append(
                f"Headcount trend: {cp.headcount_trend.change_pct:+.1f}% "
                f"over {cp.headcount_trend.period_days}d"
            )
        if cp.funding_total_usd:
            parts.append(f"Total funding: ${cp.funding_total_usd:,.0f}")
        if cp.competitors:
            parts.append(f"Competitors: {', '.join(cp.competitors[:5])}")
        parts.append("")

    if context.retrieved_chunks:
        parts.append("## Related Signals & Insights")
        for i, chunk in enumerate(context.retrieved_chunks, 1):
            parts.append(f"{i}. {chunk}")
        parts.append("")

    return "\n".join(parts)
