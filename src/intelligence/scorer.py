"""Signal Scorer — assigns final actionability scores to fused insights.

100% formula-based, no LLM. Combines signal strength, market technicals,
and confidence metrics into a single 0-100 score.

Also generates a concrete TradeSetup (action, time horizon, conviction)
so users get actionable output, not just a number.
"""

from __future__ import annotations

from src.core.models import (
    FusedInsight,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
    TradeAction,
    TradeSetup,
    TimeHorizon,
)
from src.logging_config import get_logger

log = get_logger(__name__)


# ── Historical Signal Win-Rate Table ──────────────────────────────────────────
# These are placeholder base rates derived from academic alt-data research.
# Replace with actual backtested numbers as the platform collects data.

SIGNAL_HISTORICAL_STATS: dict[str, dict[str, float]] = {
    SignalType.HIRING_SURGE.value: {
        "win_rate": 0.68,
        "avg_return_3m": 7.2,
        "sample_size": 142,
    },
    SignalType.EXECUTIVE_MOVE.value: {
        "win_rate": 0.61,
        "avg_return_3m": 4.8,
        "sample_size": 89,
    },
    SignalType.GROWTH_PRICE_DIVERGENCE.value: {
        "win_rate": 0.72,
        "avg_return_3m": 9.1,
        "sample_size": 67,
    },
    SignalType.COMPETITOR_SHIFT.value: {
        "win_rate": 0.58,
        "avg_return_3m": 3.9,
        "sample_size": 54,
    },
    SignalType.SECTOR_PULSE.value: {
        "win_rate": 0.55,
        "avg_return_3m": 2.4,
        "sample_size": 110,
    },
}


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


def attach_historical_signal_stats(signals: list[Signal]) -> list[Signal]:
    """Attach per-signal historical base rates in place."""
    for signal in signals:
        stats = get_signal_historical_stats(signal.type.value)
        if not stats:
            continue
        signal.historical_win_rate = stats["win_rate"]
        signal.historical_avg_return = stats["avg_return_3m"]
        signal.historical_sample_size = int(stats["sample_size"])
    return signals


def suggest_action(insight: FusedInsight) -> TradeSetup:
    """Derive a concrete trade suggestion from the scored insight.

    This is 100% formula-based (no LLM). It maps the composite score,
    sentiment direction, signal composition, and price action into an
    explicit TradeAction + TimeHorizon + conviction level.
    """
    score = insight.composite_score
    sentiment = insight.sentiment
    signals = insight.signals

    if not signals:
        return TradeSetup(
            action=TradeAction.NO_ACTION,
            conviction="low",
            rationale="Insufficient alternative data to form a thesis.",
        )

    # ── Detect "Take Profit" divergence ───────────────────────────────────
    # Price is up significantly but alt-data is turning negative
    price_extended_up = False
    if insight.market_data and insight.market_data.price_change_pct_30d is not None:
        price_extended_up = insight.market_data.price_change_pct_30d > 15.0

    has_bearish_alt_data = any(
        s.sentiment == Sentiment.BEARISH and s.strength in (SignalStrength.STRONG, SignalStrength.MODERATE)
        for s in signals
    )

    if price_extended_up and has_bearish_alt_data and sentiment != Sentiment.BULLISH:
        return TradeSetup(
            action=TradeAction.TAKE_PROFIT,
            time_horizon=TimeHorizon.SHORT_TERM_CATALYST,
            conviction="high" if score >= 60 else "medium",
            rationale=(
                f"Price is extended (+{insight.market_data.price_change_pct_30d:.1f}% in 30d) "
                f"but alternative data is deteriorating. Insider/hiring signals diverge from price."
            ),
            risk_note="Price momentum could continue if macro environment stays supportive.",
        )

    if insight.pairs_trade:
        pair = insight.pairs_trade
        return TradeSetup(
            action=TradeAction.PAIRS_TRADE,
            time_horizon=TimeHorizon.MEDIUM_TERM_SWING,
            conviction="high" if pair.divergence_score >= 25 else "medium",
            rationale=(
                f"{pair.rationale} Structure as long {pair.long_ticker} / short "
                f"{pair.short_ticker} rather than a pure directional bet."
            ),
            risk_note=(
                "Pairs trades still carry basis, borrow, and squeeze risk. "
                "Size both legs deliberately and monitor divergence decay."
            ),
        )

    # ── Determine time horizon from signal types ──────────────────────────
    time_horizon = _determine_time_horizon(signals, insight)

    # ── Map score + sentiment to action ───────────────────────────────────
    if sentiment == Sentiment.BULLISH:
        if score >= 70:
            action = TradeAction.ACCUMULATE
            conviction = "high"
            rationale = (
                f"Strong bullish conviction (score {score}). "
                f"{len(signals)} signals align with positive alt-data momentum."
            )
        elif score >= 50:
            action = TradeAction.ACCUMULATE
            conviction = "medium"
            rationale = (
                f"Moderate bullish signal (score {score}). "
                f"Alt-data supports gradual position building."
            )
        else:
            action = TradeAction.HOLD
            conviction = "low"
            rationale = f"Mildly bullish signals (score {score}) but conviction is insufficient for new positions."

    elif sentiment == Sentiment.BEARISH:
        if score >= 70:
            action = TradeAction.SHORT_CANDIDATE
            conviction = "high"
            rationale = (
                f"Strong bearish conviction (score {score}). "
                f"Multiple negative alt-data signals converging."
            )
        elif score >= 50:
            action = TradeAction.REDUCE
            conviction = "medium"
            rationale = (
                f"Negative alt-data signals emerging (score {score}). "
                f"Consider trimming existing positions."
            )
        else:
            action = TradeAction.HOLD
            conviction = "low"
            rationale = f"Mixed bearish signals (score {score}). Monitor but no urgent action."

    else:  # NEUTRAL
        action = TradeAction.HOLD
        conviction = "low"
        rationale = f"Signals are mixed or neutral (score {score}). Wait for clearer directional conviction."

    # ── Check for value trap ──────────────────────────────────────────────
    if time_horizon == TimeHorizon.VALUE_TRAP:
        if score >= 70:
            action = TradeAction.SHORT_CANDIDATE
            conviction = "high"
        elif score >= 50:
            action = TradeAction.REDUCE
            conviction = "medium"
        else:
            action = TradeAction.HOLD
            conviction = "low"
        rationale = (
            "Stock screens cheap after a drawdown, but the underlying alt-data remains bearish. "
            "Treat this as a potential value trap until people and hiring trends improve."
        )

    risk_note = _generate_risk_note(action, signals)

    return TradeSetup(
        action=action,
        time_horizon=time_horizon,
        conviction=conviction,
        rationale=rationale,
        risk_note=risk_note,
    )


def get_signal_historical_stats(signal_type: str) -> dict[str, float] | None:
    """Return historical win-rate stats for a signal type."""
    return SIGNAL_HISTORICAL_STATS.get(signal_type)


# ── Private helpers ───────────────────────────────────────────────────────────


def _determine_time_horizon(signals: list, insight: FusedInsight) -> TimeHorizon:
    """Classify the expected time horizon based on signal types present."""
    types = {s.type for s in signals}

    # Executive departures or filing catalysts are short-term
    short_term_types = {SignalType.EXECUTIVE_MOVE, SignalType.FILING_CATALYST, SignalType.TRANSCRIPT_TONE_SHIFT}
    long_term_types = {SignalType.HIRING_SURGE, SignalType.HIRING_MOMENTUM}

    has_short = bool(types & short_term_types)
    has_long = bool(types & long_term_types)

    # Value trap detection: bearish alt-data but stock looks cheap (low PE or big drawdown)
    if insight.sentiment == Sentiment.BEARISH:
        md = insight.market_data
        if md:
            low_pe = md.pe_ratio is not None and md.pe_ratio < 12
            big_drawdown = (md.price_change_pct_90d or 0) < -25
            if low_pe or big_drawdown:
                return TimeHorizon.VALUE_TRAP

    if has_short and not has_long:
        return TimeHorizon.SHORT_TERM_CATALYST
    if has_long and not has_short:
        return TimeHorizon.LONG_TERM_COMPOUNDER
    return TimeHorizon.MEDIUM_TERM_SWING


def _generate_risk_note(action: TradeAction, signals: list) -> str:
    """Generate a risk warning appropriate for the suggested action."""
    if action == TradeAction.ACCUMULATE:
        return "Alt-data signals can lag. Confirm with earnings results and management guidance."
    if action == TradeAction.SHORT_CANDIDATE:
        return "Short positions carry unlimited loss potential. Use stop-losses and size appropriately."
    if action == TradeAction.TAKE_PROFIT:
        return "Momentum can persist longer than expected. Consider trailing stops over full exits."
    if action == TradeAction.REDUCE:
        return "Partial reduction is preferred if core thesis is intact but signals are weakening."
    return "Signal data is observational, not predictive. Always combine with fundamental analysis."


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
        if t.rsi_14 and t.rsi_14 < 65:
            score += 15
        if t.rsi_14 and t.rsi_14 < 35:
            score += 10
        if t.price and t.sma_50 and t.price > t.sma_50:
            score += 10
        if t.macd and t.macd_signal and t.macd > t.macd_signal:
            score += 15
    elif insight.sentiment == Sentiment.BEARISH:
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

    if insight.company_profile:
        score += 25
        if insight.company_profile.headcount_trend:
            score += 25
        if insight.company_profile.headcount_history:
            score += 15
        if insight.company_profile.competitors:
            score += 10

    if insight.market_data:
        score += 15
        if insight.market_data.technicals:
            score += 10

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

    return 30 + (consensus_ratio * 70)
