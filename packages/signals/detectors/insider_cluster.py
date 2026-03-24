"""Insider Buy Cluster Detector — SEC Form 4 data.

Detects when multiple company insiders purchase shares within a short window.
Insider buy clusters are one of the strongest predictive signals in public
markets — academic research shows 3+ insiders buying within 90 days
precedes outperformance ~65% of the time.

Logic (deterministic, no LLM):
1. Filter to open-market purchases in the lookback window
2. Count unique insiders who bought
3. Aggregate total purchase value
4. Compute buy/sell ratio
5. Fire signal if cluster thresholds are met
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from packages.signals.config import InsiderClusterConfig, default_config
from packages.signals.models import InsiderTransaction, MVPSignalType


def detect(
    transactions: list[InsiderTransaction],
    ticker: str,
    company_name: str = "",
    as_of: datetime | None = None,
    config: InsiderClusterConfig | None = None,
) -> dict | None:
    """Detect insider buy cluster signal.

    Args:
        transactions: SEC Form 4 transactions for this ticker.
        ticker: Stock ticker symbol.
        company_name: Human-readable company name.
        as_of: Reference date (defaults to now). Only transactions within
               [as_of - window_days, as_of] are considered.
        config: Override default thresholds.

    Returns:
        A signal dict compatible with the signals table, or None.
    """
    cfg = config or default_config.insider_cluster
    as_of = as_of or datetime.utcnow()
    cutoff = as_of - timedelta(days=cfg.window_days)

    # ── Step 1: Partition into buys vs sells in the window ────────────────
    buys: list[InsiderTransaction] = []
    sells: list[InsiderTransaction] = []

    for txn in transactions:
        if txn.filing_date < cutoff or txn.filing_date > as_of:
            continue
        if txn.ticker.upper() != ticker.upper():
            continue
        if txn.transaction_type == "P":
            buys.append(txn)
        elif txn.transaction_type == "S":
            sells.append(txn)

    if not buys:
        return None

    # ── Step 2: Cluster metrics ──────────────────────────────────────────
    unique_buyers: dict[str, list[InsiderTransaction]] = defaultdict(list)
    for b in buys:
        unique_buyers[b.insider_name].append(b)

    num_unique_insiders = len(unique_buyers)
    total_buy_value = sum(b.total_value for b in buys)
    total_sell_value = sum(s.total_value for s in sells) or 1.0  # avoid div-by-zero
    buy_sell_ratio = total_buy_value / total_sell_value

    # ── Step 3: Threshold gate ───────────────────────────────────────────
    if num_unique_insiders < cfg.min_insiders:
        return None
    if total_buy_value < cfg.min_total_value_usd:
        return None
    if buy_sell_ratio < cfg.min_buy_sell_ratio:
        return None

    # ── Step 4: Score (0-100) ────────────────────────────────────────────
    # Base score from insider count
    insider_score = min(40.0, (num_unique_insiders / cfg.strong_insider_count) * 40)
    # Value score
    value_score = min(30.0, (total_buy_value / cfg.strong_total_value_usd) * 30)
    # Ratio score — higher buy/sell ratio = more conviction
    ratio_score = min(20.0, (buy_sell_ratio / 5.0) * 20)
    # Cluster tightness bonus: if all buys happened within 30 days, extra points
    buy_dates = sorted(b.filing_date for b in buys)
    span_days = (buy_dates[-1] - buy_dates[0]).days or 1
    tightness_score = min(10.0, (30.0 / span_days) * 10) if span_days > 0 else 10.0

    score = round(min(100.0, insider_score + value_score + ratio_score + tightness_score), 1)

    # ── Step 5: Strength & sentiment ─────────────────────────────────────
    if num_unique_insiders >= cfg.strong_insider_count and total_buy_value >= cfg.strong_total_value_usd:
        strength = "strong"
    elif score >= 65:
        strength = "moderate"
    else:
        strength = "weak"

    sentiment = "bullish"  # Insider buy clusters are inherently bullish

    # ── Step 6: Build evidence ───────────────────────────────────────────
    evidence_rows = []
    for name, txns in sorted(unique_buyers.items(), key=lambda x: -sum(t.total_value for t in x[1])):
        person_total = sum(t.total_value for t in txns)
        evidence_rows.append({
            "insider_name": name,
            "title": txns[0].insider_title,
            "num_purchases": len(txns),
            "total_value_usd": round(person_total, 2),
            "dates": [t.filing_date.isoformat() for t in txns],
            "source_urls": [t.source_url for t in txns if t.source_url],
        })

    headline = (
        f"{num_unique_insiders} insiders bought ${total_buy_value:,.0f} of {ticker} "
        f"in {span_days}d (buy/sell ratio: {buy_sell_ratio:.1f}x)"
    )

    detail_parts = [
        f"Unique buyers: {num_unique_insiders}",
        f"Total purchased: ${total_buy_value:,.0f}",
        f"Buy/sell ratio: {buy_sell_ratio:.1f}x",
        f"Window: {span_days}d",
        f"Top buyer: {evidence_rows[0]['insider_name']} (${evidence_rows[0]['total_value_usd']:,.0f})",
    ]

    return {
        "id": str(uuid.uuid4()),
        "type": MVPSignalType.INSIDER_BUY_CLUSTER.value,
        "strength": strength,
        "sentiment": sentiment,
        "ticker": ticker.upper(),
        "company_name": company_name,
        "headline": headline,
        "detail": " | ".join(detail_parts),
        "score": score,
        "data": {
            "num_unique_insiders": num_unique_insiders,
            "total_buy_value_usd": round(total_buy_value, 2),
            "total_sell_value_usd": round(total_sell_value, 2),
            "buy_sell_ratio": round(buy_sell_ratio, 2),
            "cluster_span_days": span_days,
            "window_days": cfg.window_days,
            "evidence": evidence_rows,
        },
        "detected_at": as_of.isoformat(),
    }
