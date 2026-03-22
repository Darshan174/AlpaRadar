"""Fusion Engine — correlates alternative data signals with market data.

This is the core intelligence layer that combines Crustdata company intelligence
with market data to produce actionable FusedInsights.
"""

from __future__ import annotations

from datetime import datetime

from src.core.models import (
    CompanyProfile,
    ExecutiveProfile,
    FusedInsight,
    MarketData,
    Sentiment,
    Signal,
)
from src.intelligence.signals import (
    competitor,
    divergence,
    exec_moves,
    hiring_surge,
    sector_pulse,
)
from src.logging_config import get_logger

log = get_logger(__name__)


async def generate_insight(
    company: CompanyProfile,
    market: MarketData,
    executives: list[ExecutiveProfile] | None = None,
    previous_executives: list[ExecutiveProfile] | None = None,
    competitor_profiles: dict[str, CompanyProfile] | None = None,
) -> FusedInsight:
    """Run all signal detectors and fuse results into a single insight.

    This is the main entry point for the intelligence engine.
    """
    ticker = market.ticker
    signals: list[Signal] = []

    # 1. Hiring Surge
    hire_signal = hiring_surge.detect(company, market)
    if hire_signal:
        signals.append(hire_signal)
        log.info("signal_detected", type="hiring_surge", ticker=ticker, score=hire_signal.score)

    # 2. Executive Moves
    if executives:
        exec_signals = exec_moves.detect(
            executives=executives,
            company_name=company.name,
            ticker=ticker,
            previous_executives=previous_executives,
        )
        signals.extend(exec_signals)
        for s in exec_signals:
            log.info("signal_detected", type="exec_move", ticker=ticker, score=s.score)

    # 3. Growth vs Price Divergence
    div_signal = divergence.detect(company, market)
    if div_signal:
        signals.append(div_signal)
        log.info("signal_detected", type="divergence", ticker=ticker, score=div_signal.score)

    # 4. Competitor Shifts
    if competitor_profiles:
        comp_signals = competitor.detect(
            target_company=company,
            target_ticker=ticker,
            competitor_profiles=competitor_profiles,
            target_executives=executives,
        )
        signals.extend(comp_signals)

    # Calculate composite score & sentiment
    composite_score = _calculate_composite_score(signals)
    overall_sentiment = _determine_sentiment(signals)

    return FusedInsight(
        ticker=ticker,
        company_name=company.name,
        signals=signals,
        market_data=market,
        company_profile=company,
        composite_score=composite_score,
        sentiment=overall_sentiment,
        generated_at=datetime.utcnow(),
    )


async def generate_sector_insight(
    companies: list[CompanyProfile],
    sector: str,
) -> Signal | None:
    """Generate sector-level pulse signal."""
    return sector_pulse.detect(companies, sector)


def _calculate_composite_score(signals: list[Signal]) -> float:
    """Weighted composite across all detected signals."""
    if not signals:
        return 0.0

    # Weight by signal type importance
    weights = {
        "hiring_surge": 0.30,
        "executive_move": 0.25,
        "growth_price_divergence": 0.25,
        "competitor_shift": 0.15,
        "sector_pulse": 0.05,
    }

    weighted_sum = 0.0
    total_weight = 0.0

    for signal in signals:
        w = weights.get(signal.type.value, 0.1)
        # Strong signals get boosted weight
        if signal.strength.value == "strong":
            w *= 1.3
        weighted_sum += signal.score * w
        total_weight += w

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 1)


def _determine_sentiment(signals: list[Signal]) -> Sentiment:
    """Determine overall sentiment from signal consensus."""
    if not signals:
        return Sentiment.NEUTRAL

    bullish = sum(1 for s in signals if s.sentiment == Sentiment.BULLISH)
    bearish = sum(1 for s in signals if s.sentiment == Sentiment.BEARISH)

    # Weight by score
    bullish_score = sum(s.score for s in signals if s.sentiment == Sentiment.BULLISH)
    bearish_score = sum(s.score for s in signals if s.sentiment == Sentiment.BEARISH)

    if bullish_score > bearish_score * 1.3:
        return Sentiment.BULLISH
    if bearish_score > bullish_score * 1.3:
        return Sentiment.BEARISH
    return Sentiment.NEUTRAL
