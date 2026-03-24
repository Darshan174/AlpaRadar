"""Configurable thresholds for all signal detectors.

All detection thresholds live here, not hardcoded in detector logic.
Tune these based on backtest results.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class InsiderClusterConfig(BaseModel):
    """Thresholds for SEC Form 4 insider buy cluster detection."""

    # Minimum unique insiders buying in the window to fire
    min_insiders: int = 3
    # Lookback window in days
    window_days: int = 90
    # Minimum aggregate purchase value (USD) across the cluster
    min_total_value_usd: float = 100_000.0
    # Buy/sell ratio threshold — must be > this to count as net-buying cluster
    min_buy_sell_ratio: float = 2.0
    # Score thresholds
    strong_insider_count: int = 5
    strong_total_value_usd: float = 500_000.0


class HiringMomentumConfig(BaseModel):
    """Thresholds for job-posting-based hiring momentum detection."""

    # Minimum spike ratio (current / rolling_avg) to fire
    min_spike_ratio: float = 1.5
    # Strong spike ratio
    strong_spike_ratio: float = 2.5
    # Rolling average window in days for baseline
    baseline_window_days: int = 60
    # Minimum absolute posting count to avoid noise on tiny companies
    min_posting_count: int = 10
    # Department-specific boost multiplier (engineering postings matter more)
    engineering_boost: float = 1.3


class MaterialEventConfig(BaseModel):
    """Thresholds for 8-K material event and transcript tone-change detection."""

    # 8-K item types considered high-severity
    high_severity_items: list[str] = Field(default_factory=lambda: [
        "1.01",  # Entry into a Material Definitive Agreement
        "1.02",  # Termination of a Material Definitive Agreement
        "2.01",  # Completion of Acquisition or Disposition
        "2.04",  # Triggering Events That Accelerate Obligations
        "2.05",  # Costs Associated with Exit/Disposal Activities
        "2.06",  # Material Impairments
        "4.01",  # Changes in Registrant's Certifying Accountant
        "4.02",  # Non-Reliance on Previously Issued Financial Statements
        "5.01",  # Changes in Control of Registrant
        "5.02",  # Departure of Directors or Certain Officers
    ])
    # Minimum sentiment delta between consecutive transcripts to fire
    min_sentiment_delta: float = 0.25
    # Strong sentiment delta
    strong_sentiment_delta: float = 0.50
    # Minimum keyword density score to boost signal
    min_keyword_score: float = 3.0


class SignalEngineConfig(BaseModel):
    """Top-level config aggregating all detector configs."""

    insider_cluster: InsiderClusterConfig = Field(default_factory=InsiderClusterConfig)
    hiring_momentum: HiringMomentumConfig = Field(default_factory=HiringMomentumConfig)
    material_event: MaterialEventConfig = Field(default_factory=MaterialEventConfig)


# Default singleton — importable everywhere
default_config = SignalEngineConfig()
