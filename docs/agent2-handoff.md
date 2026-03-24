# Agent 2 Handoff: Data Ingestion & Normalization

## What Was Built

### Provider Architecture (`src/ingestion/base.py`)
- `BaseProvider` abstract class with source-run logging, rate limiting, and lifecycle methods
- `NormalizedRecord` base model for all ingestion outputs — includes `idempotency_key`, `source_url`, `source_timestamp`, `ticker`, `raw_payload`
- `SourceRun` model for tracking collection runs (started/completed/failed, record counts)
- `RateLimiter` (simple token-bucket) and `make_idempotency_key` (SHA-256 based dedupe)

### Storage Adapter (`src/ingestion/storage_adapter.py`)
- Wraps Agent 1's Supabase storage helpers for: `insider_trades`, `filing_events`, `job_postings`, `transcript_chunks`, `raw_documents`, `source_runs`
- Falls back to in-memory store when Supabase is unavailable (for dev/testing)
- All stores deduplicate on `idempotency_key`

### SEC EDGAR Collectors (`src/ingestion/sec/`)

**CIK Lookup** (`cik_lookup.py`)
- Resolves ticker -> CIK from SEC's `company_tickers.json`
- Caches in memory after first load
- Falls back to fixture file if SEC is unreachable

**Form 4 Insider Trades** (`form4.py`)
- Fetches filings from `data.sec.gov/submissions/CIK{padded}.json`
- Downloads and parses Form 4 XML documents
- Extracts: filer name/title, director/officer flags, transaction type (P/S/A), shares, price, post-transaction holdings
- Stores raw XML in `raw_documents` for audit

**8-K Filing Events** (`filing8k.py`)
- Fetches 8-K filings from same submissions endpoint
- Maps item numbers to descriptions (e.g., 2.02 = "Results of Operations")
- Classifies filings as `is_material` based on item type
- 15 material item types tracked (see `MATERIAL_ITEMS` dict)

### Job Posting Collector (`src/ingestion/jobs/`)

**Provider Interface** (`provider.py`)
- `JobPostingProvider` abstract base — implement `search_jobs(company_name, ticker)` for any source
- `FixtureJobProvider` — loads from `tests/fixtures/jobs/` JSON files
- `JobPostingCollector` — normalizes raw job data, classifies department (8 categories) and seniority (7 levels)

**SerpAPI Adapter** (`serpapi.py`)
- Google Jobs search via SerpAPI
- Requires `SERPAPI_KEY` env var

### Transcript Stub (`src/ingestion/transcripts/fmp.py`)
- FMP (Financial Modeling Prep) adapter for earnings call transcripts
- Requires `FMP_API_KEY` env var (250 calls/day free tier)
- Falls back to fixture data
- Basic paragraph-level chunking (~500 char segments)
- **Not production-ready** — see "Next Steps" below

### Orchestration Entrypoints (`src/ingestion/entrypoints.py`)
- `sync_sec_activity(ticker)` — runs Form 4 + 8-K collectors
- `sync_job_postings(ticker)` — runs job collector with auto-provider selection
- `sync_transcripts(ticker)` — runs transcript collector
- `sync_company_alt_data(ticker)` — orchestrates all three, handles partial failures
- `sync_universe(tickers)` — batch sync across multiple tickers

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `SERPAPI_KEY` | No | — | For live job search; falls back to fixtures |
| `FMP_API_KEY` | No | — | For earnings transcripts; falls back to fixtures |
| `SUPABASE_URL` | No | — | Falls back to in-memory store |
| `SUPABASE_KEY` | No | — | Falls back to in-memory store |

SEC EDGAR requires **no API key**. Only a User-Agent header (`AlphaRadar research@alpharadar.dev`).

## Rate Limits

| Source | Limit | Implementation |
|--------|-------|----------------|
| SEC EDGAR | 10 req/s | RateLimiter at 8 req/s (conservative) |
| SerpAPI | 100 searches/month (free) | No built-in limiter; rely on quota |
| FMP | 250 calls/day (free) | No built-in limiter; low volume |

## Known Data Quality Issues

1. **Form 4 XML namespaces**: Some filings use XML namespaces, others don't. Parser handles both, but edge cases may exist with older filings.
2. **8-K item extraction**: Items come from EDGAR's `items` field in submissions JSON. Some 8-Ks have empty items — these are tracked but classified as `is_material=False`.
3. **Job department classification**: Heuristic-based on title keywords. Accuracy is ~80-90% for common titles, weaker for ambiguous ones.
4. **Transcript chunking**: Current implementation is paragraph-level without speaker attribution. Doesn't parse "Q: ... A: ..." patterns.
5. **CIK mapping**: Uses SEC's official ticker file. Some tickers (especially for dual-listed or recently renamed companies) may not resolve.

## Integration Notes for Other Agents

### Agent 1 (Foundation/Storage)
The storage adapter (`storage_adapter.py`) expects these tables to exist:
- `source_runs` (id, source_name, ticker, status, records_fetched, records_stored, error_message, started_at, completed_at, metadata)
- `insider_trades` (idempotency_key as conflict target, plus all fields from `InsiderTradeRecord`)
- `filing_events` (idempotency_key as conflict target, plus all fields from `FilingEventRecord`)
- `job_postings` (idempotency_key as conflict target, plus all fields from `JobPostingRecord`)
- `transcript_chunks` (idempotency_key as conflict target, plus all fields from `TranscriptChunkRecord`)
- `raw_documents` (idempotency_key as conflict target)

If these tables don't exist, the in-memory fallback keeps things running.

### Agent 3 (Intelligence/Signals)
Detector queries should target:
- `insider_trades` — filter by `ticker`, `transaction_type='P'` (purchases), look for clusters within date windows
- `filing_events` — filter by `ticker`, `is_material=True`, look at `items` array for specific event types
- `job_postings` — count by `ticker` + `department`, compare against baseline for hiring momentum
- `transcript_chunks` — full-text or embedding search for sentiment analysis

### Agent 4 (API/Product)
Entrypoints are ready to call from API routes or scheduler:
```python
from src.ingestion.entrypoints import sync_company_alt_data, sync_sec_activity
result = await sync_company_alt_data("AAPL")
```

## Test Coverage

49 tests across 5 test files:
- `test_base.py` — idempotency keys, source runs, rate limiter
- `test_sec_form4.py` — XML parsing (7 unit), integration with mocked HTTP (2)
- `test_sec_8k.py` — event normalization (5 unit), integration (3 including dedup)
- `test_jobs.py` — department/seniority classification (12), collector integration (6)
- `test_entrypoints.py` — orchestration (4)

All tests are fixture-backed and run without network access.

## Next Steps

1. **Transcript speaker attribution**: Parse "Speaker Name:" patterns in transcript text to attribute chunks to CEO/CFO/analyst roles
2. **13F holdings**: Add 13F parser for institutional ownership changes (lower priority than Form 4)
3. **Job posting deduplication across runs**: Current dedupe is by idempotency key; could add fuzzy matching for slightly different postings of the same role
4. **Historical backfill**: Add `--backfill` mode to fetch older filings beyond the default 90-day window
5. **USPTO/openFDA**: Patent and FDA event stubs are not included — leave for future iteration
