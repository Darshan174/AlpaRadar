"""Signal Scorer — assigns final actionability scores to fused insights.

100% formula-based, no LLM. Combines signal strength, market technicals,
and confidence metrics into a single 0-100 score.
"""

from __future__ import annotations

from src.core.models import FusedInsight, Sentiment, SignalStrength
from src.logging_config import get_logger

log = get_logger(__name__)


def score_insight(insight: FusedInsight) -> float:
    """Calculate final actionability score for a fused insight.

    Components:
    - Signal strength (40%): Weighted sum of individual signal scores
    - Technical alignment (25%): Do technicals confirm the signal direction?
    - Data confidence (20%): How much data do we have?
    - Signal consensus (15%): Do signals agree on direction?
    """
    signal_score = _signal_component(insight)
    technical_score = _technical_component(insight)
    confidence_score = _confidence_component(insight)
    consensus_score = _consensus_component(insight)

    final = (
        signal_score * 0.40
        + technical_score * 0.25
        + confidence_score * 0.20
        + consensus_score * 0.15
    )

    final = round(min(100.0, max(0.0, final)), 1)
    log.info(
        "insight_scored",
        ticker=insight.ticker,
        final=final,
        signal=signal_score,
        technical=technical_score,
        confidence=confidence_score,
        consensus=consensus_score,
    )
    return final


def _signal_component(insight: FusedInsight) -> float:
    """Average score of all signals, boosted by strong signals."""
    if not insight.signals:
        return 0.0
    scores = []
    for s in insight.signals:
        boost = 1.2 if s.strength == SignalStrength.STRONG else 1.0
        scores.append(s.score * boost)
    return min(100.0, sum(scores) / len(scores))


def _technical_component(insight: FusedInsight) -> float:
    """Check if market technicals align with signal sentiment."""
    md = insight.market_data
    if not md or not md.technicals:
        return 50.0  # Neutral if no data

    t = md.technicals
    score = 50.0  # Start neutral

    if insight.sentiment == Sentiment.BULLISH:
        # Bullish: RSI not overbought, price above SMA, positive MACD
        if t.rsi_14 and t.rsi_14 < 65:
            score += 15
        if t.rsi_14 and t.rsi_14 < 35:
            score += 10  # Extra boost for oversold
        if t.price and t.sma_50 and t.price > t.sma_50:
            score += 10
        if t.macd and t.macd_signal and t.macd > t.macd_signal:
            score += 15
    elif insight.sentiment == Sentiment.BEARISH:
        # Bearish: RSI overbought, price below SMA, negative MACD
        if t.rsi_14 and t.rsi_14 > 65:
            score += 15
        if t.rsi_14 and t.rsi_14 > 80:
            score += 10
        if t.price and t.sma_50 and t.price < t.sma_50:
            score += 10
        if t.macd and t.macd_signal and t.macd < t.macd_signal:
            score += 15

    return min(100.0, score)


def _confidence_component(insight: FusedInsight) -> float:
    """Score based on data availability and freshness."""
    score = 0.0
    checks = 0

    # Company data available?
    if insight.company_profile:
        score += 25
        if insight.company_profile.headcount_trend:
            score += 25
        if insight.company_profile.headcount_history:
            score += 15
        if insight.company_profile.competitors:
            score += 10
    checks += 75

    # Market data available?
    if insight.market_data:
        score += 15
        if insight.market_data.technicals:
            score += 10
    checks += 25

    return score


def _consensus_component(insight: FusedInsight) -> float:
    """Score based on how much signals agree on direction."""
    if not insight.signals:
        return 0.0

    bullish = sum(1 for s in insight.signals if s.sentiment == Sentiment.BULLISH)
    bearish = sum(1 for s in insight.signals if s.sentiment == Sentiment.BEARISH)
    total = len(insight.signals)

    if total <= 1:
        return 50.0

    dominant = max(bullish, bearish)
    consensus_ratio = dominant / total

    # 100% agreement = 100, 50/50 split = 30
    return 30 + (consensus_ratio * 70)
