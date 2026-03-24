# Agent 1 Handoff — Foundation, Contracts, Storage

## What was built

### Migration: `002_alt_data_mvp.sql`
Additive migration introducing 8 new tables and extending `signals` with source-tracking columns. Does not modify existing tables or columns from `001_init.sql`.

New tables: `companies`, `source_runs`, `raw_documents`, `insider_trades`, `job_postings`, `filing_events`, `transcript_chunks`, `briefs`

### Migration: `003_seed_data.sql`
Seed data with:
- 30 companies in the MVP universe (mega/large/mid cap US equities)
- 7 sample insider trades (AAPL cluster buy, NVDA CEO sell, CRM cluster buy, PLTR CEO sell)
- 13 sample job postings (NVDA engineering surge, CRM AI roles, AAPL ML roles)
- 4 sample 8-K filing events
- 4 sample signals with realistic evidence payloads
- 2 sample AI-generated briefs

### Models: `src/core/models.py`
Added `SignalType` enum values: `INSIDER_BUY_CLUSTER`, `HIRING_MOMENTUM`, `FILING_CATALYST`, `TRANSCRIPT_TONE_SHIFT`

Added Pydantic models: `SourceRun`, `RawDocument`, `InsiderTrade`, `JobPosting`, `FilingEvent`, `TranscriptChunk`, `Company`, `Brief`, `TransactionType`, `SourceRunStatus`

Key model properties for detectors:
- `InsiderTrade.is_buy` / `.is_notable` — filters notable officer/director buys above $10k
- `FilingEvent.is_material` — checks for material 8-K items (1.01, 2.01, 5.02, etc.)

### Storage: `src/storage/supabase.py`
Added ~25 new async helper functions covering all CRUD operations for new tables. Key detector-oriented queries:
- `get_insider_buy_cluster(ticker, days_back)` — fetches recent insider buys
- `get_job_posting_counts(ticker, days_back)` — returns department-level posting counts
- `get_material_filings(ticker, days_back)` — fetches 8-K filings
- `get_transcript_chunks(ticker, ...)` — fetches transcript segments
- `get_signal_detail(signal_id)` — composite: signal + brief
- `get_company_detail(ticker)` — composite: company + signals + briefs

### API Schemas: `src/api/schemas.py`
Extended `SignalResponse` with `source_url`, `source_name`, `source_timestamp`.

Added: `BriefResponse`, `SignalDetailResponse`, `CompanyDetailResponse`, `SignalFeedResponse`, `InsiderTradeResponse`, `JobPostingSummaryResponse`, `FilingEventResponse`

### Config: `src/config.py`
Added `sec_user_agent` (for SEC EDGAR) and `serpapi_key` (for job postings).

### Tests
- `tests/test_models.py` — 17 tests covering signal types, model validation, properties
- `tests/test_storage.py` — 13 tests covering all new storage helpers with mocked Supabase

All 30 tests pass.

---

## Assumptions other agents must follow

1. **Ingestion (Agent 2)**: Write normalized records via the `upsert_*` helpers. Always set `idempotency_key` — the DB enforces uniqueness. Use `create_source_run` / `complete_source_run` to track collection jobs.

2. **Intelligence (Agent 3)**: Read normalized data via `get_insider_buy_cluster`, `get_job_posting_counts`, `get_material_filings`, `get_transcript_chunks`. Write detected signals via `store_signal` (existing). Write briefs via `store_brief`. Use `SignalType.INSIDER_BUY_CLUSTER` etc. for new signal types. Populate `signal.data` with the evidence fields documented in `docs/contracts.md`.

3. **Product (Agent 4)**: Use `get_signals`, `get_signal_detail`, `get_company_detail`, `get_briefs` for API routes. Response shapes match the new schema classes in `src/api/schemas.py`.

4. **Idempotency keys**: Every normalized record has a unique `idempotency_key`. Format conventions:
   - Insider trades: `{cik}:{filing_date}:{txn_code}:{shares}`
   - Job postings: `{source}:{company}:{title_hash}:{location}`
   - Filing events: `{accession_number}`
   - Transcript chunks: `{ticker}:{quarter}:{speaker}:{chunk_index}`
   - Signals: `{signal_type}:{ticker}:{date_or_context}`

5. **signals table extensions**: New columns (`source_url`, `source_name`, `source_timestamp`, `evidence_ids`, `idempotency_key`) are nullable to preserve backward compatibility with existing signal creation paths.

---

## Open issues

- **`datetime.utcnow()` in models**: Pydantic model defaults still use `datetime.utcnow()`. These are upstream in the model layer and only trigger deprecation warnings; functional correctness is not affected.
- **Transcript support**: Tables and models are ready, but transcript data ingestion is the least-validated path. Agent 2 should stub it if no free transcript source is available.
- **`evidence_ids` on signals**: The `UUID[]` column exists but no storage helper populates it yet. Agent 3 should set it when creating signals from normalized records.
- **company_profiles vs companies**: Two tables overlap on company identity. `companies` is the lightweight MVP universe table (keyed by ticker). `company_profiles` is the richer Crustdata-enriched table (keyed by domain). They're linked by the `domain` field. Don't merge them — downstream code depends on both shapes.
