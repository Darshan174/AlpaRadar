"""Executive Movement Signal Detector.

Tracks C-suite and VP-level moves between public companies.
New CTO from FAANG → mid-cap is bullish. CFO departure before earnings is bearish.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from src.core.models import (
    ExecutiveMove,
    ExecutiveProfile,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
)
from src.logging_config import get_logger

log = get_logger(__name__)

# Prestigious origin companies — departures from these carry weight
PRESTIGE_COMPANIES = {
    "google", "meta", "apple", "amazon", "microsoft", "nvidia", "netflix",
    "goldman sachs", "jpmorgan", "citadel", "two sigma", "renaissance",
    "bridgewater", "blackrock", "stripe", "openai", "anthropic",
}

# Titles that carry maximum impact
HIGH_IMPACT_TITLES = {"ceo", "cto", "cfo", "coo", "president"}
MEDIUM_IMPACT_TITLES = {"cpo", "cio", "cso", "svp", "evp", "vp"}


def detect(
    executives: list[ExecutiveProfile],
    company_name: str,
    ticker: str,
    previous_executives: list[ExecutiveProfile] | None = None,
) -> list[Signal]:
    """Detect executive movement signals.

    Compares current executive roster with previous snapshot to find:
    - New hires from prestigious companies (bullish)
    - Departures of key executives (bearish)
    - C-suite reshuffles (neutral-to-bearish uncertainty)
    """
    signals: list[Signal] = []

    # Detect new high-impact hires
    for exec in executives:
        sig = _score_new_hire(exec, company_name, ticker)
        if sig:
            signals.append(sig)

    # Detect departures if we have a previous snapshot
    if previous_executives:
        departure_signals = _detect_departures(
            previous_executives, executives, company_name, ticker
        )
        signals.extend(departure_signals)

    return signals


def _score_new_hire(
    exec: ExecutiveProfile,
    company_name: str,
    ticker: str,
) -> Signal | None:
    """Score a new executive hire based on origin prestige and role impact."""
    title_lower = exec.title.lower()

    # Determine role impact
    is_high_impact = any(t in title_lower for t in HIGH_IMPACT_TITLES)
    is_medium_impact = any(t in title_lower for t in MEDIUM_IMPACT_TITLES)

    if not (is_high_impact or is_medium_impact):
        return None

    # Check if they come from a prestigious company
    prestige_origin = None
    for prev in exec.previous_companies:
        if prev.lower() in PRESTIGE_COMPANIES:
            prestige_origin = prev
            break

    if not prestige_origin and not is_high_impact:
        return None

    # Calculate significance score
    score = 40.0
    if is_high_impact:
        score += 30
    elif is_medium_impact:
        score += 15
    if prestige_origin:
        score += 25

    strength = SignalStrength.STRONG if score >= 75 else SignalStrength.MODERATE

    headline = f"{exec.name} ({exec.title}) joins {company_name}"
    if prestige_origin:
        headline += f" from {prestige_origin}"

    detail_parts = [f"New {exec.title} at {company_name}"]
    if prestige_origin:
        detail_parts.append(f"Previously at {prestige_origin}")
    if exec.previous_titles:
        detail_parts.append(f"Past roles: {', '.join(exec.previous_titles[:3])}")

    return Signal(
        id=str(uuid.uuid4()),
        type=SignalType.EXECUTIVE_MOVE,
        strength=strength,
        sentiment=Sentiment.BULLISH,
        ticker=ticker,
        company_name=company_name,
        headline=headline,
        detail=" | ".join(detail_parts),
        score=round(min(100, score), 1),
        data={
            "executive_name": exec.name,
            "title": exec.title,
            "from_company": prestige_origin or "unknown",
            "seniority_tier": exec.seniority_tier,
            "previous_companies": exec.previous_companies[:5],
        },
    )


def _detect_departures(
    previous: list[ExecutiveProfile],
    current: list[ExecutiveProfile],
    company_name: str,
    ticker: str,
) -> list[Signal]:
    """Detect executives who left (present in previous, absent in current)."""
    current_names = {e.name.lower() for e in current}
    signals = []

    for exec in previous:
        if exec.name.lower() not in current_names:
            title_lower = exec.title.lower()
            is_high_impact = any(t in title_lower for t in HIGH_IMPACT_TITLES)
            if not is_high_impact:
                continue

            score = 65.0 if "cfo" in title_lower else 55.0  # CFO departures are more bearish

            signals.append(
                Signal(
                    id=str(uuid.uuid4()),
                    type=SignalType.EXECUTIVE_MOVE,
                    strength=SignalStrength.MODERATE,
                    sentiment=Sentiment.BEARISH,
                    ticker=ticker,
                    company_name=company_name,
                    headline=f"{exec.name} ({exec.title}) departed {company_name}",
                    detail=f"Key executive departure: {exec.title}. May indicate internal issues or upcoming changes.",
                    score=round(score, 1),
                    data={
                        "executive_name": exec.name,
                        "title": exec.title,
                        "departure": True,
                        "seniority_tier": exec.seniority_tier,
                    },
                )
            )

    return signals
