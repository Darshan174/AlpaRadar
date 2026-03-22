"""AlphaRadar API — Alternative Data Intelligence Platform.

Production-grade FastAPI application with:
- Rate limiting
- API key auth on protected routes
- Request logging
- CORS
- Background scheduled ingestion
- Prometheus metrics
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app

from src.api.middleware import APIKeyMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
from src.api.routes import chat, intelligence, signals, watchlist
from src.api.schemas import HealthResponse
from src.config import settings
from src.logging_config import get_logger, setup_logging

log = get_logger(__name__)

# ── Prometheus Metrics ─────────────────────────────────────────────────────────

REQUEST_COUNT = Counter("alpharadar_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_DURATION = Histogram("alpharadar_request_duration_seconds", "Request duration")
SIGNALS_DETECTED = Counter("alpharadar_signals_detected", "Signals detected", ["type"])


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("alpharadar_starting", version="0.1.0")

    # Start background scheduler for watchlist ingestion
    _start_scheduler()

    yield

    log.info("alpharadar_shutting_down")


def _start_scheduler():
    """Start APScheduler for periodic watchlist ingestion."""
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _run_watchlist_scan,
            "interval",
            hours=settings.ingestion_interval_hours,
            id="watchlist_scan",
            replace_existing=True,
        )
        scheduler.start()
        log.info("scheduler_started", interval_hours=settings.ingestion_interval_hours)
    except Exception as e:
        log.warning("scheduler_failed_to_start", error=str(e))


async def _run_watchlist_scan():
    """Periodic scan: fetch signals for all watchlisted tickers."""
    from src.alerts.engine import send_signal_alert
    from src.core.models import CompanyProfile
    from src.ingestion.crustdata.client import CrustdataClient
    from src.ingestion.crustdata.transforms import to_company_profile
    from src.ingestion.market.price import fetch_market_data, ticker_to_domain
    from src.intelligence.fusion import generate_insight
    from src.intelligence.scorer import score_insight
    from src.storage import supabase as db

    try:
        tickers = await db.get_all_watched_tickers()
        log.info("watchlist_scan_started", tickers=len(tickers))

        async with CrustdataClient() as crustdata:
            for ticker in tickers:
                try:
                    market = await fetch_market_data(ticker)
                    domain = ticker_to_domain(ticker)

                    company = CompanyProfile(
                        name=market.company_name or ticker,
                        ticker=ticker,
                    )
                    if domain:
                        raw = await crustdata.enrich_company(domain=domain)
                        company = to_company_profile(raw)
                        company.ticker = ticker

                    insight = await generate_insight(company=company, market=market)
                    insight.composite_score = score_insight(insight)

                    for signal in insight.signals:
                        if signal.is_actionable:
                            await db.store_signal(signal)
                            await send_signal_alert(signal)

                except Exception as e:
                    log.error("watchlist_scan_ticker_failed", ticker=ticker, error=str(e))

        log.info("watchlist_scan_complete", tickers=len(tickers))
    except Exception as e:
        log.error("watchlist_scan_failed", error=str(e))


# ── App Factory ────────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="AlphaRadar",
        description="Alternative data intelligence — democratizing hedge fund insights",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware (order matters: last added = first executed)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(signals.router)
    app.include_router(intelligence.router)
    app.include_router(chat.router)
    app.include_router(watchlist.router)

    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Health check
    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health():
        return HealthResponse(timestamp=datetime.utcnow())

    return app


app = create_app()
