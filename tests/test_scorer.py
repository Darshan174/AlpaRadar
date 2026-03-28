"""Tests for shared scoring and trade setup helpers."""

from src.core.models import (
    FusedInsight,
    MarketData,
    PairsTradeSetup,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
    TradeAction,
    TimeHorizon,
)
from src.intelligence.scorer import attach_historical_signal_stats, suggest_action


def test_attach_historical_signal_stats_populates_signal_fields():
    signal = Signal(
        id="seed",
        type=SignalType.HIRING_SURGE,
        strength=SignalStrength.STRONG,
        sentiment=Sentiment.BULLISH,
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        headline="Hiring surge",
        detail="Bullish hiring trend",
        score=88,
    )

    attach_historical_signal_stats([signal])

    assert signal.historical_win_rate == 0.68
    assert signal.historical_avg_return == 7.2
    assert signal.historical_sample_size == 142


def test_suggest_action_value_trap_is_actionable():
    signal = Signal(
        id="trap",
        type=SignalType.EXECUTIVE_MOVE,
        strength=SignalStrength.STRONG,
        sentiment=Sentiment.BEARISH,
        ticker="SNOW",
        company_name="Snowflake",
        headline="Executive exits continue",
        detail="Negative people data",
        score=82,
    )
    insight = FusedInsight(
        ticker="SNOW",
        company_name="Snowflake",
        signals=[signal],
        sentiment=Sentiment.BEARISH,
        composite_score=78,
        market_data=MarketData(
            ticker="SNOW",
            company_name="Snowflake",
            pe_ratio=10.0,
            price_change_pct_90d=-30.0,
        ),
    )

    setup = suggest_action(insight)

    assert setup.time_horizon == TimeHorizon.VALUE_TRAP
    assert setup.action == TradeAction.SHORT_CANDIDATE
    assert "value trap" in setup.rationale.lower()


def test_suggest_action_prefers_pairs_trade_when_present():
    signal = Signal(
        id="pair",
        type=SignalType.HIRING_SURGE,
        strength=SignalStrength.STRONG,
        sentiment=Sentiment.BULLISH,
        ticker="AMD",
        company_name="AMD",
        headline="Hiring divergence vs peer",
        detail="Bullish hiring trend",
        score=80,
    )
    insight = FusedInsight(
        ticker="AMD",
        company_name="AMD",
        signals=[signal],
        sentiment=Sentiment.BULLISH,
        composite_score=66,
        pairs_trade=PairsTradeSetup(
            long_ticker="AMD",
            short_ticker="INTC",
            long_company="AMD",
            short_company="Intel",
            divergence_score=24.0,
            rationale="AMD hiring is accelerating while Intel contracts.",
            sector="Semiconductors",
        ),
    )

    setup = suggest_action(insight)

    assert setup.action == TradeAction.PAIRS_TRADE
    assert setup.time_horizon == TimeHorizon.MEDIUM_TERM_SWING
    assert "long AMD / short INTC" in setup.rationale
