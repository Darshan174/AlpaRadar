"""Multi-channel alert engine — Slack, Telegram, and webhook notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from src.config import settings
from src.core.exceptions import AlertDeliveryError
from src.core.models import AlertChannel, FusedInsight, Signal, WatchlistAlert
from src.logging_config import get_logger

log = get_logger(__name__)


async def send_signal_alert(
    signal: Signal,
    channels: list[AlertChannel] | None = None,
) -> None:
    """Send an alert for a detected signal to configured channels."""
    channels = channels or _default_channels()
    if not channels:
        return

    message = _format_signal_message(signal)

    for channel in channels:
        try:
            if channel == AlertChannel.SLACK:
                await _send_slack(message)
            elif channel == AlertChannel.TELEGRAM:
                await _send_telegram(message)
            elif channel == AlertChannel.WEBHOOK:
                await _send_webhook(signal.model_dump(mode="json"))
            log.info("alert_sent", channel=channel.value, ticker=signal.ticker)
        except Exception as e:
            log.error("alert_failed", channel=channel.value, error=str(e))


async def send_insight_alert(insight: FusedInsight) -> None:
    """Send a comprehensive alert for a fused insight."""
    channels = _default_channels()
    if not channels:
        return

    message = _format_insight_message(insight)

    for channel in channels:
        try:
            if channel == AlertChannel.SLACK:
                await _send_slack(message)
            elif channel == AlertChannel.TELEGRAM:
                await _send_telegram(message)
        except Exception as e:
            log.error("insight_alert_failed", channel=channel.value, error=str(e))


async def send_watchlist_alert(alert: WatchlistAlert) -> None:
    """Send alert for a watchlist item signal."""
    message = (
        f"*Watchlist Alert: {alert.ticker}*\n"
        f"{_format_signal_message(alert.signal)}"
    )
    if alert.channel == AlertChannel.SLACK:
        await _send_slack(message)
    elif alert.channel == AlertChannel.TELEGRAM:
        await _send_telegram(message)


# ── Channel Implementations ────────────────────────────────────────────────────


async def _send_slack(message: str) -> None:
    """Send via Slack Bot API."""
    if not settings.slack_bot_token or not settings.slack_channel:
        log.debug("slack_not_configured")
        return

    from slack_sdk.web.async_client import AsyncWebClient

    client = AsyncWebClient(token=settings.slack_bot_token)
    await client.chat_postMessage(channel=settings.slack_channel, text=message)


async def _send_telegram(message: str) -> None:
    """Send via Telegram Bot API."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.debug("telegram_not_configured")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
        )
        if resp.status_code != 200:
            raise AlertDeliveryError(f"Telegram error: {resp.text[:200]}")


async def _send_webhook(payload: dict[str, Any]) -> None:
    """Send JSON payload to a configured webhook URL."""
    # Placeholder for custom webhook integrations
    log.debug("webhook_send", payload_keys=list(payload.keys()))


# ── Formatting ─────────────────────────────────────────────────────────────────


def _format_signal_message(signal: Signal) -> str:
    strength_emoji = {"strong": "!!!", "moderate": "!!", "weak": "!"}
    sentiment_indicator = {"bullish": "BULLISH", "bearish": "BEARISH", "neutral": "NEUTRAL"}

    return (
        f"*[{signal.type.value.upper()}]* {strength_emoji.get(signal.strength.value, '!')} "
        f"*{signal.ticker}* — {sentiment_indicator.get(signal.sentiment.value, '')}\n"
        f"Score: {signal.score}/100\n"
        f"{signal.headline}\n"
        f"_{signal.detail}_"
    )


def _format_insight_message(insight: FusedInsight) -> str:
    signals_summary = "\n".join(
        f"  - [{s.type.value}] {s.headline} (score: {s.score})"
        for s in insight.signals[:5]
    )

    return (
        f"*AlphaRadar Insight: {insight.ticker}*\n"
        f"Composite Score: *{insight.composite_score}/100* | "
        f"Sentiment: *{insight.sentiment.value.upper()}*\n"
        f"Signals ({insight.signal_count}):\n{signals_summary}\n"
        f"\n{insight.llm_analysis[:500] if insight.llm_analysis else ''}"
    )


def _default_channels() -> list[AlertChannel]:
    channels = []
    if settings.slack_bot_token:
        channels.append(AlertChannel.SLACK)
    if settings.telegram_bot_token:
        channels.append(AlertChannel.TELEGRAM)
    return channels
