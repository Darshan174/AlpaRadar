"""Sector Pulse Signal Detector.

Aggregates alternative data across an entire sector to detect macro-level
talent flows and growth trends. Rising sector-wide hiring often precedes
sector rotation in public markets.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from src.core.models import (
    CompanyProfile,
    Sentiment,
    Signal,
    SignalStrength,
    SignalType,
)
from src.logging_config import get_logger

log = get_logger(__name__)

SECTOR_SURGE_THRESHOLD = 15.0  # Sector avg growth >= 15% is a surge
SECTOR_DECLINE_THRESHOLD = -5.0


def detect(
    companies: list[CompanyProfile],
    sector: str,
) -> Signal | None:
    """Detect sector-wide hiring pulse.

    Aggregates headcount trends across all companies in a sector
    to produce a macro signal about sector health.
    """
    if not companies:
        return None

    growths: list[float] = []
    growing = 0
    declining = 0
    total_headcount = 0

    for company in companies:
        if company.headcount_trend:
            growths.append(company.headcount_trend.change_pct)
            total_headcount += company.headcount_trend.current
            if company.headcount_trend.change_pct > 5:
                growing += 1
            elif company.headcount_trend.change_pct < -5:
                declining += 1

    if not growths:
        return None

    avg_growth = sum(growths) / len(growths)
    median_growth = sorted(growths)[len(growths) // 2]

    if SECTOR_DECLINE_THRESHOLD < avg_growth < SECTOR_SURGE_THRESHOLD:
        return None

    is_surging = avg_growth >= SECTOR_SURGE_THRESHOLD
    sentiment = Sentiment.BULLISH if is_surging else Sentiment.BEARISH

    # Score based on magnitude and breadth
    breadth = growing / len(companies) if is_surging else declining / len(companies)
    score = min(100.0, abs(avg_growth) * 2 + breadth * 40 + 20)

    strength = SignalStrength.STRONG if score >= 70 else SignalStrength.MODERATE

    if is_surging:
        headline = (
            f"{sector} sector hiring surge: avg +{avg_growth:.0f}% "
            f"({growing}/{len(companies)} companies growing)"
        )
    else:
        headline = (
            f"{sector} sector contraction: avg {avg_growth:.0f}% "
            f"({declining}/{len(companies)} companies declining)"
        )

    # Top movers
    sorted_companies = sorted(
        [(c.name, c.headcount_trend.change_pct) for c in companies if c.headcount_trend],
        key=lambda x: x[1],
        reverse=True,
    )
    top_growers = sorted_companies[:3]
    top_decliners = sorted_companies[-3:] if len(sorted_companies) > 3 else []

    detail_parts = [
        f"Avg growth: {avg_growth:+.1f}%",
        f"Median: {median_growth:+.1f}%",
        f"Companies tracked: {len(companies)}",
        f"Total headcount: {total_headcount:,}",
    ]
    if top_growers:
        detail_parts.append(
            f"Top growers: {', '.join(f'{n} ({g:+.0f}%)' for n, g in top_growers)}"
        )

    return Signal(
        id=str(uuid.uuid4()),
        type=SignalType.SECTOR_PULSE,
        strength=strength,
        sentiment=sentiment,
        ticker=sector.upper().replace(" ", "_"),
        company_name=f"{sector} Sector",
        headline=headline,
        detail=" | ".join(detail_parts),
        score=round(score, 1),
        data={
            "sector": sector,
            "avg_growth_pct": round(avg_growth, 2),
            "median_growth_pct": round(median_growth, 2),
            "companies_tracked": len(companies),
            "growing_count": growing,
            "declining_count": declining,
            "total_headcount": total_headcount,
            "top_growers": [{"name": n, "growth": g} for n, g in top_growers],
            "top_decliners": [{"name": n, "growth": g} for n, g in top_decliners],
        },
    )
