"""LLM Analyzer — generates natural language intelligence briefs from signals.

Uses Groq free tier (Llama 3.3 70B) via LiteLLM with fallback to Llama 3.1 8B.
"""

from __future__ import annotations

import os
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.core.exceptions import LLMError
from src.core.models import (
    EarningsIntel,
    FusedInsight,
    LLMStructuredThesis,
    MarketData,
    RAGContext,
    Sentiment,
    Signal,
)
from src.intelligence.rag import format_context_for_llm, retrieve_context
from src.logging_config import get_logger

from .prompts import CHAT_SYSTEM_V1, PRE_EARNINGS_V1, SIGNAL_ANALYSIS_V1

log = get_logger(__name__)


def _ensure_api_key() -> None:
    """Set Groq API key for LiteLLM."""
    if settings.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=10), reraise=True)
async def _call_llm(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Call LLM with fallback chain: primary → fallback model."""
    import litellm

    _ensure_api_key()

    model = model or settings.llm_model
    temperature = temperature if temperature is not None else settings.llm_temperature
    max_tokens = max_tokens or settings.llm_max_tokens

    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        log.warning("llm_primary_failed", model=model, error=str(e))
        # Fallback to smaller model
        if model != settings.llm_fallback_model:
            response = await litellm.acompletion(
                model=settings.llm_fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        raise LLMError(f"LLM call failed: {e}") from e


async def analyze_signals(insight: FusedInsight) -> str:
    """Generate a natural language analysis of a fused insight."""
    signals_text = _format_signals(insight.signals)
    market_context = _format_market(insight.market_data)

    # Retrieve RAG context
    rag_context_obj = await retrieve_context(
        query=f"{insight.company_name} {insight.ticker} alternative data signals",
        ticker=insight.ticker,
    )
    rag_context = format_context_for_llm(rag_context_obj)

    prompt = SIGNAL_ANALYSIS_V1.format(
        ticker=insight.ticker,
        company_name=insight.company_name,
        signals_text=signals_text,
        market_context=market_context,
        rag_context=rag_context or "No historical context available.",
    )

    result = await _call_llm([{"role": "user", "content": prompt}])
    log.info("signal_analysis_complete", ticker=insight.ticker, length=len(result))
    return result


async def analyze_pre_earnings(intel: EarningsIntel) -> str:
    """Generate pre-earnings intelligence report."""
    prompt = PRE_EARNINGS_V1.format(
        ticker=intel.ticker,
        company_name=intel.company_name,
        company_intel=f"Earnings date: {intel.earnings_date}",
        hiring_data=f"Trend: {intel.hiring_trend.change_pct:+.1f}%" if intel.hiring_trend else "N/A",
        exec_sentiment=intel.exec_sentiment.value,
        competitor_data=f"Competitor momentum: {intel.competitor_momentum:.1f}",
        technical_data=intel.technical_setup.value,
    )

    result = await _call_llm([{"role": "user", "content": prompt}])
    return result


async def chat(
    user_message: str,
    history: list[dict[str, str]] | None = None,
    ticker: str | None = None,
) -> str:
    """Handle a chat message with RAG-enhanced context."""
    rag_context_obj = await retrieve_context(query=user_message, ticker=ticker)
    rag_context = format_context_for_llm(rag_context_obj)

    system_prompt = CHAT_SYSTEM_V1.format(
        rag_context=rag_context or "No specific context available for this query.",
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    result = await _call_llm(messages, temperature=0.3)
    return result


# ── Formatting helpers ─────────────────────────────────────────────────────────


def extract_structured_signal_analysis(text: str) -> LLMStructuredThesis | None:
    """Parse the main structured sections from the markdown analysis."""

    def _extract(label: str) -> str:
        pattern = rf"^\*\*{re.escape(label)}\*\*:\s*(.+)$"
        match = re.search(pattern, text, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""

    thesis = LLMStructuredThesis(
        suggested_action=_extract("Suggested Action"),
        time_horizon=_extract("Time Horizon"),
        conviction=_extract("Conviction"),
    )
    if not any([thesis.suggested_action, thesis.time_horizon, thesis.conviction]):
        return None
    return thesis


def _format_signals(signals: list[Signal]) -> str:
    parts = []
    for i, s in enumerate(signals, 1):
        parts.append(
            f"{i}. [{s.type.value}] [{s.strength.value}] [{s.sentiment.value}] "
            f"Score: {s.score}\n   {s.headline}\n   {s.detail}"
        )
    return "\n\n".join(parts) if parts else "No signals detected."


def _format_market(market: MarketData | None) -> str:
    if not market:
        return "No market data available."

    parts = [
        f"Ticker: {market.ticker}",
        f"Sector: {market.sector}",
        f"Market Cap: ${market.market_cap:,.0f}" if market.market_cap else "",
        f"P/E: {market.pe_ratio:.1f}" if market.pe_ratio else "",
    ]

    if market.technicals:
        t = market.technicals
        parts.extend([
            f"Price: ${t.price:.2f}" if t.price else "",
            f"RSI(14): {t.rsi_14:.1f}" if t.rsi_14 else "",
            f"MACD: {t.macd:.3f}" if t.macd else "",
            f"SMA50: ${t.sma_50:.2f}" if t.sma_50 else "",
        ])

    changes = []
    if market.price_change_pct_30d is not None:
        changes.append(f"30d: {market.price_change_pct_30d:+.1f}%")
    if market.price_change_pct_90d is not None:
        changes.append(f"90d: {market.price_change_pct_90d:+.1f}%")
    if changes:
        parts.append(f"Price Changes: {', '.join(changes)}")

    return "\n".join(p for p in parts if p)
