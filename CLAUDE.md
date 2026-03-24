# AlphaRadar

Alternative data intelligence platform — democratizing hedge fund insights.

## Architecture

```
src/
  core/          - Domain models (Signal, CompanyProfile, FusedInsight, etc.)
  ingestion/
    crustdata/   - Crustdata API client (company intel, people, social posts)
    market/      - Market data via yfinance (free)
  intelligence/
    signals/     - 5 signal detectors: hiring_surge, exec_moves, divergence, competitor, sector_pulse
    fusion.py    - Combines signals into FusedInsights
    scorer.py    - Formula-based scoring (no LLM)
    rag.py       - RAG retrieval from pgvector
  analysis/      - LLM analysis via Groq (free) with litellm
  storage/       - Supabase (free) + pgvector + fastembed (local, free)
  alerts/        - Slack/Telegram/webhook notifications
  api/           - FastAPI backend with rate limiting, auth, CORS
```

## Tech Stack (all free)

- Python 3.11+ / FastAPI / uvicorn
- yfinance (market data, free)
- Crustdata API (company intelligence)
- Groq free tier (Llama 3.3 70B via litellm)
- fastembed (local ONNX embeddings, no API key)
- Supabase free tier (PostgreSQL + pgvector)
- structlog / prometheus-client for observability

## Commands

- `make install` — install deps
- `make dev` — run API server
- `make lint` — ruff check + format
- `make test` — run tests
- `python3` not `python` on this system

## Key Design Decisions

- Signal detectors are pure functions (no side effects) for testability
- Fusion engine orchestrates all detectors and produces FusedInsight
- Scorer is 100% formula-based (no LLM) for deterministic results
- LLM is only used for natural language analysis briefs
- Embeddings run locally via fastembed (384-dim BAAI/bge-small-en-v1.5)
- Background scheduler polls watchlisted tickers every N hours
