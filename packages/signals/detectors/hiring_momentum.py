"""Hiring Momentum Spike Detector — Job Posting data.

Detects when a company's active job postings spike relative to its own
historical baseline. Unlike the headcount-based hiring_surge detector,
this uses real-time job posting counts as a *leading* indicator —
postings spike before headcount grows.

Logic (deterministic, no LLM):
1. Compute rolling average of postings over baseline window
2. Compare latest snapshot to the rolling average
3. Fire signal if spike ratio exceeds threshold
4. Boost score for engineering-heavy spikes
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from packages.signals.config import HiringMomentumConfig, default_config
from packages.signals.models import JobPostingSnapshot, MVPSignalType


def detect(
    snapshots: list[JobPostingSnapshot],
    ticker: str,
    company_name: str = "",
    as_of: datetime | None = None,
    config: HiringMomentumConfig | None = None,
) -> dict | None:
    """Detect hiring momentum spike from job posting snapshots.

    Args:
        snapshots: Time-series of job posting counts, sorted by date ascending.
        ticker: Stock ticker symbol.
        company_name: Human-readable company name.
        as_of: Reference date (defaults to now).
        config: Override default thresholds.

    Returns:
        A signal dict compatible with the signals table, or None.
    """
    cfg = config or default_config.hiring_momentum
    as_of = as_of or datetime.utcnow()

    # Filter to this ticker and sort by date
    relevant = sorted(
        [s for s in snapshots if s.ticker.upper() == ticker.upper()],
        key=lambda s: s.date,
    )

    if len(relevant) < 2:
        return None

    # ── Step 1: Find latest snapshot and compute baseline ────────────────
    latest = relevant[-1]
    baseline_cutoff = latest.date - timedelta(days=cfg.baseline_window_days)

    baseline_snapshots = [s for s in relevant[:-1] if s.date >= baseline_cutoff]
    if not baseline_snapshots:
        return None

    avg_total = sum(s.total_postings for s in baseline_snapshots) / len(baseline_snapshots)
    avg_eng = sum(s.engineering_postings for s in baseline_snapshots) / len(baseline_snapshots)

    if avg_total == 0:
        return None

    # ── Step 2: Compute spike ratios ─────────────────────────────────────
    total_spike_ratio = latest.total_postings / avg_total
    eng_spike_ratio = (latest.engineering_postings / avg_eng) if avg_eng > 0 else 0.0

    # ── Step 3: Threshold gate ───────────────────────────────────────────
    if total_spike_ratio < cfg.min_spike_ratio:
        return None
    if latest.total_postings < cfg.min_posting_count:
        return None

    # ── Step 4: Score (0-100) ────────────────────────────────────────────
    # Base score from spike magnitude
    base_score = min(60.0, ((total_spike_ratio - 1.0) / (cfg.strong_spike_ratio - 1.0)) * 60)

    # Engineering boost
    eng_bonus = 0.0
    if eng_spike_ratio >= cfg.min_spike_ratio:
        eng_bonus = min(20.0, (eng_spike_ratio - 1.0) * 10 * cfg.engineering_boost)

    # Consistency bonus: are postings trending up across snapshots?
    if len(baseline_snapshots) >= 3:
        last_three = baseline_snapshots[-3:]
        if all(last_three[i].total_postings <= last_three[i + 1].total_postings for i in range(len(last_three) - 1)):
            consistency_bonus = 10.0
        else:
            consistency_bonus = 0.0
    else:
        consistency_bonus = 0.0

    # Absolute size bonus: large companies with spikes are more meaningful
    size_bonus = min(10.0, latest.total_postings / 50.0 * 10)

    score = round(min(100.0, base_score + eng_bonus + consistency_bonus + size_bonus), 1)

    # ── Step 5: Strength & sentiment ─────────────────────────────────────
    if total_spike_ratio >= cfg.strong_spike_ratio:
        strength = "strong"
    elif score >= 60:
        strength = "moderate"
    else:
        strength = "weak"

    sentiment = "bullish"  # Hiring spikes are forward-looking bullish

    # ── Step 6: Build evidence ───────────────────────────────────────────
    dept_changes = {}
    for dept, count in latest.department_breakdown.items():
        baseline_dept_counts = [s.department_breakdown.get(dept, 0) for s in baseline_snapshots]
        avg_dept = sum(baseline_dept_counts) / len(baseline_dept_counts) if baseline_dept_counts else 0
        if avg_dept > 0:
            dept_changes[dept] = round((count / avg_dept - 1) * 100, 1)

    headline = (
        f"{company_name or ticker} job postings surging {total_spike_ratio:.1f}x baseline "
        f"({latest.total_postings} vs avg {avg_total:.0f})"
    )

    detail_parts = [
        f"Current postings: {latest.total_postings}",
        f"Baseline avg ({cfg.baseline_window_days}d): {avg_total:.0f}",
        f"Spike ratio: {total_spike_ratio:.2f}x",
    ]
    if eng_spike_ratio > 1.0:
        detail_parts.append(f"Engineering spike: {eng_spike_ratio:.2f}x ({latest.engineering_postings} postings)")
    if dept_changes:
        top_dept = max(dept_changes, key=dept_changes.get)
        detail_parts.append(f"Fastest growing dept: {top_dept} (+{dept_changes[top_dept]:.0f}%)")

    return {
        "id": str(uuid.uuid4()),
        "type": MVPSignalType.HIRING_MOMENTUM.value,
        "strength": strength,
        "sentiment": sentiment,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "headline": headline,
        "detail": " | ".join(detail_parts),
        "score": score,
        "data": {
            "total_spike_ratio": round(total_spike_ratio, 3),
            "engineering_spike_ratio": round(eng_spike_ratio, 3),
            "current_postings": latest.total_postings,
            "baseline_avg_postings": round(avg_total, 1),
            "engineering_postings": latest.engineering_postings,
            "baseline_window_days": cfg.baseline_window_days,
            "department_changes_pct": dept_changes,
            "snapshot_date": latest.date.isoformat(),
            "evidence": {
                "baseline_snapshots": len(baseline_snapshots),
                "trend": [
                    {"date": s.date.isoformat(), "postings": s.total_postings}
                    for s in (baseline_snapshots[-5:] + [latest])
                ],
            },
        },
        "detected_at": (as_of or datetime.utcnow()).isoformat(),
    }
