"""Market data fetcher using yfinance (free, no API key)."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

from src.core.exceptions import MarketDataError
from src.core.models import MarketData, PriceBar, TechnicalIndicators
from src.logging_config import get_logger

log = get_logger(__name__)


# ── Ticker → Company Domain mapping (for Crustdata enrichment) ─────────────────

TICKER_DOMAIN_MAP: dict[str, str] = {
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "GOOGL": "google.com",
    "AMZN": "amazon.com",
    "META": "meta.com",
    "NVDA": "nvidia.com",
    "TSLA": "tesla.com",
    "NFLX": "netflix.com",
    "CRM": "salesforce.com",
    "PLTR": "palantir.com",
    "SNOW": "snowflake.com",
    "SNAP": "snap.com",
}


def ticker_to_domain(ticker: str) -> str | None:
    """Best-effort ticker → domain resolution."""
    return TICKER_DOMAIN_MAP.get(ticker.upper())


async def fetch_market_data(
    ticker: str,
    period: str = "1y",
) -> MarketData:
    """Fetch price history + fundamentals from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            raise MarketDataError(f"No data returned for {ticker}")

        info = stock.info or {}

        price_history = [
            PriceBar(
                date=idx.to_pydatetime(),
                open=round(row["Open"], 2),
                high=round(row["High"], 2),
                low=round(row["Low"], 2),
                close=round(row["Close"], 2),
                volume=int(row["Volume"]),
            )
            for idx, row in hist.iterrows()
        ]

        technicals = _calculate_technicals(hist)

        now = datetime.utcnow()
        price_changes = _calculate_price_changes(hist)

        return MarketData(
            ticker=ticker.upper(),
            company_name=info.get("shortName", ""),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            price_history=price_history,
            technicals=technicals,
            price_change_pct_30d=price_changes.get("30d"),
            price_change_pct_90d=price_changes.get("90d"),
            price_change_pct_180d=price_changes.get("180d"),
            fetched_at=now,
        )
    except MarketDataError:
        raise
    except Exception as e:
        log.error("market_data_fetch_failed", ticker=ticker, error=str(e))
        raise MarketDataError(f"Failed to fetch {ticker}: {e}") from e


def _calculate_technicals(hist: pd.DataFrame) -> TechnicalIndicators:
    """Calculate technical indicators from price history."""
    close = hist["Close"]
    volume = hist["Volume"]

    try:
        import ta

        rsi = ta.momentum.RSIIndicator(close, window=14)
        macd_ind = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        bb = ta.volatility.BollingerBands(close, window=20)
        atr = ta.volatility.AverageTrueRange(hist["High"], hist["Low"], close, window=14)
        adx = ta.trend.ADXIndicator(hist["High"], hist["Low"], close, window=14)

        latest_close = float(close.iloc[-1])

        return TechnicalIndicators(
            rsi_14=_safe_last(rsi.rsi()),
            macd=_safe_last(macd_ind.macd()),
            macd_signal=_safe_last(macd_ind.macd_signal()),
            sma_20=_safe_last(close.rolling(20).mean()),
            sma_50=_safe_last(close.rolling(50).mean()),
            sma_200=_safe_last(close.rolling(200).mean()),
            bollinger_upper=_safe_last(bb.bollinger_hband()),
            bollinger_lower=_safe_last(bb.bollinger_lband()),
            atr_14=_safe_last(atr.average_true_range()),
            adx_14=_safe_last(adx.adx()),
            vwap=_safe_last((close * volume).cumsum() / volume.cumsum()),
            volume_sma_20=_safe_last(volume.rolling(20).mean()),
            price=latest_close,
        )
    except ImportError:
        # Fallback: compute basic indicators manually
        return TechnicalIndicators(
            sma_20=_safe_last(close.rolling(20).mean()),
            sma_50=_safe_last(close.rolling(50).mean()),
            sma_200=_safe_last(close.rolling(200).mean()),
            price=float(close.iloc[-1]),
        )


def _calculate_price_changes(hist: pd.DataFrame) -> dict[str, float | None]:
    """Calculate price change percentages over various periods."""
    close = hist["Close"]
    if len(close) < 2:
        return {}

    latest = float(close.iloc[-1])
    changes: dict[str, float | None] = {}

    for label, days in [("30d", 30), ("90d", 90), ("180d", 180)]:
        if len(close) >= days:
            past = float(close.iloc[-days])
            changes[label] = round(((latest - past) / past) * 100, 2)
        else:
            changes[label] = None

    return changes


def _safe_last(series: pd.Series) -> float | None:
    """Get last non-NaN value from a Series."""
    if series is None or series.empty:
        return None
    last = series.iloc[-1]
    if pd.isna(last):
        return None
    return round(float(last), 4)
