"""Material Event / Transcript Tone-Change Detector.

Two sub-detectors in one:
A) 8-K Material Event Detector: flags high-severity SEC 8-K filings
B) Earnings Transcript Tone-Change: detects significant sentiment shifts
   between consecutive earnings calls using deterministic keyword analysis

Logic is purely deterministic — no LLM calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from packages.signals.config import MaterialEventConfig, default_config
from packages.signals.models import (
    MVPSignalType,
    MaterialFiling,
    TranscriptSentiment,
)

# ── 8-K Item Descriptions (for human-readable evidence) ─────────────────────

ITEM_DESCRIPTIONS: dict[str, str] = {
    "1.01": "Entry into Material Definitive Agreement",
    "1.02": "Termination of Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of Direct Financial Obligation",
    "2.04": "Triggering Events That Accelerate Obligations",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Transfer",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure of Directors or Certain Officers",
    "5.03": "Amendments to Articles/Bylaws",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
}

# Bearish 8-K items (typically negative for stock price)
BEARISH_ITEMS = {"1.02", "2.04", "2.05", "2.06", "3.01", "4.01", "4.02", "5.02"}
# Bullish 8-K items (typically positive)
BULLISH_ITEMS = {"1.01", "2.01"}


def detect(
    filings: list[MaterialFiling] | None = None,
    transcripts: list[TranscriptSentiment] | None = None,
    ticker: str = "",
    company_name: str = "",
    as_of: datetime | None = None,
    config: MaterialEventConfig | None = None,
) -> list[dict]:
    """Detect material event signals from 8-Ks and transcript tone changes.

    Args:
        filings: Recent 8-K filings for this ticker.
        transcripts: Earnings transcript sentiment records (at least 2 for delta).
        ticker: Stock ticker symbol.
        company_name: Human-readable company name.
        as_of: Reference date.
        config: Override default thresholds.

    Returns:
        List of signal dicts (may be empty, may contain multiple).
    """
    cfg = config or default_config.material_event
    as_of = as_of or datetime.utcnow()
    signals: list[dict] = []

    if filings:
        filing_signal = _detect_material_filing(filings, ticker, company_name, as_of, cfg)
        if filing_signal:
            signals.append(filing_signal)

    if transcripts and len(transcripts) >= 2:
        tone_signal = _detect_tone_change(transcripts, ticker, company_name, as_of, cfg)
        if tone_signal:
            signals.append(tone_signal)

    return signals


def _detect_material_filing(
    filings: list[MaterialFiling],
    ticker: str,
    company_name: str,
    as_of: datetime,
    cfg: MaterialEventConfig,
) -> dict | None:
    """Detect high-severity 8-K filings in the last 30 days."""
    cutoff = as_of - timedelta(days=30)
    recent = [f for f in filings if f.filing_date >= cutoff and f.ticker.upper() == ticker.upper()]

    if not recent:
        return None

    # Score each filing by severity of its items
    scored_filings = []
    for filing in recent:
        high_severity_hits = [item for item in filing.items if item in cfg.high_severity_items]
        if high_severity_hits:
            scored_filings.append((filing, high_severity_hits))

    if not scored_filings:
        return None

    # Aggregate severity
    all_high_items = set()
    for _, items in scored_filings:
        all_high_items.update(items)

    # Determine sentiment from item types
    bearish_hits = all_high_items & BEARISH_ITEMS
    bullish_hits = all_high_items & BULLISH_ITEMS
    if len(bearish_hits) > len(bullish_hits):
        sentiment = "bearish"
    elif len(bullish_hits) > len(bearish_hits):
        sentiment = "bullish"
    else:
        sentiment = "neutral"

    # Score
    base_score = min(50.0, len(all_high_items) * 15.0)
    filing_count_bonus = min(20.0, len(scored_filings) * 10.0)
    severity_bonus = min(30.0, (len(bearish_hits) + len(bullish_hits)) * 10.0)
    score = round(min(100.0, base_score + filing_count_bonus + severity_bonus), 1)

    strength = "strong" if score >= 70 else "moderate" if score >= 45 else "weak"

    # Evidence
    evidence_rows = []
    for filing, high_items in scored_filings:
        evidence_rows.append({
            "filing_date": filing.filing_date.isoformat(),
            "form_type": filing.form_type,
            "items": high_items,
            "item_descriptions": [ITEM_DESCRIPTIONS.get(i, i) for i in high_items],
            "description": filing.description,
            "source_url": filing.source_url,
        })

    item_names = [ITEM_DESCRIPTIONS.get(i, i) for i in sorted(all_high_items)]
    headline = (
        f"{ticker} filed {len(scored_filings)} material 8-K(s): "
        f"{', '.join(item_names[:3])}"
    )
    if len(item_names) > 3:
        headline += f" (+{len(item_names) - 3} more)"

    detail_parts = [
        f"High-severity items: {len(all_high_items)}",
        f"Filings in last 30d: {len(scored_filings)}",
    ]
    if bearish_hits:
        detail_parts.append(f"Bearish items: {', '.join(sorted(bearish_hits))}")
    if bullish_hits:
        detail_parts.append(f"Bullish items: {', '.join(sorted(bullish_hits))}")

    return {
        "id": str(uuid.uuid4()),
        "type": MVPSignalType.MATERIAL_EVENT.value,
        "strength": strength,
        "sentiment": sentiment,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "headline": headline,
        "detail": " | ".join(detail_parts),
        "score": score,
        "data": {
            "sub_type": "8k_material_filing",
            "num_filings": len(scored_filings),
            "high_severity_items": sorted(all_high_items),
            "bearish_items": sorted(bearish_hits),
            "bullish_items": sorted(bullish_hits),
            "evidence": evidence_rows,
        },
        "detected_at": as_of.isoformat(),
    }


def _detect_tone_change(
    transcripts: list[TranscriptSentiment],
    ticker: str,
    company_name: str,
    as_of: datetime,
    cfg: MaterialEventConfig,
) -> dict | None:
    """Detect significant tone shift between consecutive earnings transcripts."""
    # Sort by date and filter to this ticker
    relevant = sorted(
        [t for t in transcripts if t.ticker.upper() == ticker.upper()],
        key=lambda t: t.date,
    )

    if len(relevant) < 2:
        return None

    prev = relevant[-2]
    curr = relevant[-1]

    # ── Compute sentiment deltas ─────────────────────────────────────────
    overall_delta = curr.overall_sentiment - prev.overall_sentiment
    guidance_delta = curr.guidance_sentiment - prev.guidance_sentiment

    # Weighted delta: guidance changes matter more
    weighted_delta = overall_delta * 0.4 + guidance_delta * 0.6

    if abs(weighted_delta) < cfg.min_sentiment_delta:
        return None

    # ── Keyword score bonus ──────────────────────────────────────────────
    keyword_delta = (
        (curr.positive_keyword_hits - curr.negative_keyword_hits)
        - (prev.positive_keyword_hits - prev.negative_keyword_hits)
    )

    # ── Score ────────────────────────────────────────────────────────────
    base_score = min(60.0, (abs(weighted_delta) / cfg.strong_sentiment_delta) * 60)
    keyword_bonus = min(20.0, abs(keyword_delta) * 2.0) if abs(keyword_delta) >= cfg.min_keyword_score else 0.0
    # Risk keyword spike is extra bearish
    risk_bonus = 0.0
    if curr.risk_keyword_hits > prev.risk_keyword_hits * 1.5 and curr.risk_keyword_hits >= 3:
        risk_bonus = 15.0

    score = round(min(100.0, base_score + keyword_bonus + risk_bonus + 10), 1)  # +10 base for firing

    is_positive_shift = weighted_delta > 0
    sentiment = "bullish" if is_positive_shift else "bearish"
    strength = "strong" if abs(weighted_delta) >= cfg.strong_sentiment_delta else "moderate"

    direction = "improved" if is_positive_shift else "deteriorated"
    headline = (
        f"{ticker} earnings tone {direction}: "
        f"{prev.quarter} ({prev.overall_sentiment:+.2f}) -> "
        f"{curr.quarter} ({curr.overall_sentiment:+.2f})"
    )

    detail_parts = [
        f"Overall sentiment delta: {overall_delta:+.3f}",
        f"Guidance delta: {guidance_delta:+.3f}",
        f"Weighted delta: {weighted_delta:+.3f}",
    ]
    if keyword_delta != 0:
        detail_parts.append(f"Net keyword shift: {keyword_delta:+d}")
    if curr.risk_keyword_hits > 0:
        detail_parts.append(f"Risk keywords: {curr.risk_keyword_hits} (prev: {prev.risk_keyword_hits})")
    if curr.notable_phrases:
        detail_parts.append(f"Key phrases: {', '.join(curr.notable_phrases[:3])}")

    return {
        "id": str(uuid.uuid4()),
        "type": MVPSignalType.MATERIAL_EVENT.value,
        "strength": strength,
        "sentiment": sentiment,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "headline": headline,
        "detail": " | ".join(detail_parts),
        "score": score,
        "data": {
            "sub_type": "transcript_tone_change",
            "current_quarter": curr.quarter,
            "previous_quarter": prev.quarter,
            "overall_delta": round(overall_delta, 4),
            "guidance_delta": round(guidance_delta, 4),
            "weighted_delta": round(weighted_delta, 4),
            "keyword_delta": keyword_delta,
            "risk_keywords_current": curr.risk_keyword_hits,
            "risk_keywords_previous": prev.risk_keyword_hits,
            "evidence": {
                "current": {
                    "quarter": curr.quarter,
                    "date": curr.date.isoformat(),
                    "overall_sentiment": curr.overall_sentiment,
                    "guidance_sentiment": curr.guidance_sentiment,
                    "notable_phrases": curr.notable_phrases[:5],
                    "source_url": curr.source_url,
                },
                "previous": {
                    "quarter": prev.quarter,
                    "date": prev.date.isoformat(),
                    "overall_sentiment": prev.overall_sentiment,
                    "guidance_sentiment": prev.guidance_sentiment,
                    "notable_phrases": prev.notable_phrases[:5],
                    "source_url": prev.source_url,
                },
            },
        },
        "detected_at": as_of.isoformat(),
    }
