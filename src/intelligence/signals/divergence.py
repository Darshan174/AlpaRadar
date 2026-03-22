"""Growth vs. Price Divergence Signal Detector.

Finds stocks where company fundamentals (headcount growth, funding) diverge
significantly from stock price movement. A company growing 40% by headcount
with a flat stock price represents a potential catch-up opportunity.
"""

from __future__ import annotations

import uuid

from src.core.models import (
    CompanyProfile,
    MarketData,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
)
from src.logging_config import get_logger

log = get_logger(__name__)

# Minimum divergence (in percentage points) to trigger a signal
DIVERGENCE_THRESHOLD_PP = 15.0
STRONG_DIVERGENCE_PP = 30.0


def detect(
    company: CompanyProfile,
    market: MarketData,
) -> Signal | None:
    """Detect divergence between company growth and stock price."""
    trend = company.headcount_trend
    if not trend:
        return None

    growth_pct = trend.change_pct
    price_pct = market.price_change_pct_90d
    if price_pct is None:
        price_pct = market.price_change_pct_30d
    if price_pct is None:
        return None

    # Divergence = growth - price change
    # Positive divergence = company growing faster than stock (bullish)
    # Negative divergence = stock outrunning fundamentals (bearish)
    divergence = growth_pct - price_pct

    if abs(divergence) < DIVERGENCE_THRESHOLD_PP:
        return None

    is_bullish = divergence > 0  # Company outgrowing its stock price

    if abs(divergence) >= STRONG_DIVERGENCE_PP:
        strength = SignalStrength.STRONG
    else:
        strength = SignalStrength.MODERATE

    # Score: higher divergence = higher score
    score = min(100.0, (abs(divergence) / STRONG_DIVERGENCE_PP) * 70 + 20)

    # Factor in technical setup
    if market.technicals:
        # RSI oversold + positive divergence = very bullish setup
        if is_bullish and market.technicals.rsi_14 and market.technicals.rsi_14 < 35:
            score = min(100.0, score + 15)
        # RSI overbought + negative divergence = very bearish
        elif not is_bullish and market.technicals.rsi_14 and market.technicals.rsi_14 > 70:
            score = min(100.0, score + 15)

    ticker = market.ticker
    sentiment = Sentiment.BULLISH if is_bullish else Sentiment.BEARISH

    if is_bullish:
        headline = (
            f"{company.name} growing {growth_pct:+.0f}% by headcount "
            f"but stock only {price_pct:+.0f}% — {abs(divergence):.0f}pp gap"
        )
    else:
        headline = (
            f"{company.name} stock {price_pct:+.0f}% but headcount only "
            f"{growth_pct:+.0f}% — fundamentals may not support price"
        )

    detail_parts = [
        f"Headcount growth: {growth_pct:+.1f}%",
        f"Stock price change: {price_pct:+.1f}%",
        f"Divergence: {divergence:+.1f}pp",
    ]
    if market.technicals and market.technicals.rsi_14:
        detail_parts.append(f"RSI(14): {market.technicals.rsi_14:.0f}")
    if market.pe_ratio:
        detail_parts.append(f"P/E: {market.pe_ratio:.1f}")

    return Signal(
        id=str(uuid.uuid4()),
        type=SignalType.GROWTH_PRICE_DIVERGENCE,
        strength=strength,
        sentiment=sentiment,
        ticker=ticker,
        company_name=company.name,
        headline=headline,
        detail=" | ".join(detail_parts),
        score=round(score, 1),
        data={
            "headcount_growth_pct": growth_pct,
            "price_change_pct": price_pct,
            "divergence_pp": round(divergence, 2),
            "direction": "bullish_undervalued" if is_bullish else "bearish_overvalued",
            "rsi": market.technicals.rsi_14 if market.technicals else None,
            "pe_ratio": market.pe_ratio,
        },
    )
