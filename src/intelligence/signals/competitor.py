"""Competitor Shift Signal Detector.

Detects when talent flows abnormally between competing companies.
If Company A is losing employees to Company B at 3x normal rate,
that's a leading indicator of market share shift.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from src.core.models import (
    CompanyProfile,
    ExecutiveProfile,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
)
from src.logging_config import get_logger

log = get_logger(__name__)

# Minimum talent flow to trigger signal
MIN_TALENT_FLOW_COUNT = 3
STRONG_FLOW_COUNT = 8


def detect(
    target_company: CompanyProfile,
    target_ticker: str,
    competitor_profiles: dict[str, CompanyProfile],
    target_executives: list[ExecutiveProfile] | None = None,
) -> list[Signal]:
    """Detect competitor talent shift signals.

    Analyzes:
    1. Headcount trends of target vs competitors
    2. Executive origins (are execs coming from competitors?)
    3. Relative growth rates
    """
    signals: list[Signal] = []

    # Signal 1: Relative headcount growth vs competitors
    relative_signal = _detect_relative_growth(
        target_company, target_ticker, competitor_profiles
    )
    if relative_signal:
        signals.append(relative_signal)

    # Signal 2: Talent flow from competitors
    if target_executives:
        flow_signal = _detect_talent_inflow(
            target_company, target_ticker, target_executives, competitor_profiles
        )
        if flow_signal:
            signals.append(flow_signal)

    return signals


def _detect_relative_growth(
    target: CompanyProfile,
    ticker: str,
    competitors: dict[str, CompanyProfile],
) -> Signal | None:
    """Compare target's headcount growth to competitor average."""
    if not target.headcount_trend or not competitors:
        return None

    target_growth = target.headcount_trend.change_pct

    comp_growths = []
    for comp in competitors.values():
        if comp.headcount_trend:
            comp_growths.append(comp.headcount_trend.change_pct)

    if not comp_growths:
        return None

    avg_competitor_growth = sum(comp_growths) / len(comp_growths)
    advantage = target_growth - avg_competitor_growth

    if abs(advantage) < 10:
        return None

    is_winning = advantage > 0
    sentiment = Sentiment.BULLISH if is_winning else Sentiment.BEARISH

    score = min(100.0, abs(advantage) * 2 + 30)
    strength = SignalStrength.STRONG if abs(advantage) >= 25 else SignalStrength.MODERATE

    if is_winning:
        headline = (
            f"{target.name} outpacing competitors in hiring: "
            f"{target_growth:+.0f}% vs avg {avg_competitor_growth:+.0f}%"
        )
    else:
        headline = (
            f"{target.name} falling behind competitors: "
            f"{target_growth:+.0f}% vs avg {avg_competitor_growth:+.0f}%"
        )

    comp_details = []
    for name, comp in competitors.items():
        if comp.headcount_trend:
            comp_details.append(f"{name}: {comp.headcount_trend.change_pct:+.0f}%")

    return Signal(
        id=str(uuid.uuid4()),
        type=SignalType.COMPETITOR_SHIFT,
        strength=strength,
        sentiment=sentiment,
        ticker=ticker,
        company_name=target.name,
        headline=headline,
        detail=f"Target: {target_growth:+.1f}% | Competitors: {', '.join(comp_details)}",
        score=round(score, 1),
        data={
            "target_growth_pct": target_growth,
            "avg_competitor_growth_pct": round(avg_competitor_growth, 2),
            "advantage_pp": round(advantage, 2),
            "competitor_growths": {
                name: comp.headcount_trend.change_pct
                for name, comp in competitors.items()
                if comp.headcount_trend
            },
        },
    )


def _detect_talent_inflow(
    target: CompanyProfile,
    ticker: str,
    executives: list[ExecutiveProfile],
    competitors: dict[str, CompanyProfile],
) -> Signal | None:
    """Detect if target is pulling talent from competitors."""
    competitor_names = {name.lower() for name in competitors}

    inflow: dict[str, int] = defaultdict(int)
    for exec in executives:
        for prev in exec.previous_companies:
            if prev.lower() in competitor_names:
                inflow[prev] += 1

    total_from_competitors = sum(inflow.values())
    if total_from_competitors < MIN_TALENT_FLOW_COUNT:
        return None

    strength = (
        SignalStrength.STRONG
        if total_from_competitors >= STRONG_FLOW_COUNT
        else SignalStrength.MODERATE
    )

    score = min(100.0, total_from_competitors * 8 + 35)
    top_source = max(inflow, key=inflow.get) if inflow else ""

    headline = (
        f"{target.name} pulling talent from {len(inflow)} competitors "
        f"({total_from_competitors} execs, top source: {top_source})"
    )

    return Signal(
        id=str(uuid.uuid4()),
        type=SignalType.COMPETITOR_SHIFT,
        strength=strength,
        sentiment=Sentiment.BULLISH,
        ticker=ticker,
        company_name=target.name,
        headline=headline,
        detail=f"Talent inflow: {dict(inflow)}",
        score=round(score, 1),
        data={
            "talent_inflow": dict(inflow),
            "total_from_competitors": total_from_competitors,
            "top_source": top_source,
        },
    )
