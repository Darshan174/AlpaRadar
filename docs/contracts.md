# AlphaRadar Data Contracts

Schema reference for all agents. Tables below are defined in `migrations/001_init.sql` (original) and `migrations/002_alt_data_mvp.sql` (alt-data MVP).

---

## Core Tables (001_init.sql — unchanged)

### `signals`
Detected alternative-data signals. Central to the product.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | Signal ID (e.g. `insider_buy_cluster:AAPL:20251217`) |
| type | TEXT | Signal type enum value |
| strength | TEXT | `strong`, `moderate`, `weak` |
| sentiment | TEXT | `bullish`, `bearish`, `neutral` |
| ticker | TEXT | Stock ticker |
| headline | TEXT | Human-readable one-liner |
| detail | TEXT | Extended explanation |
| score | REAL | 0-100 deterministic score |
| data | JSONB | Signal-specific evidence payload |
| embedding | vector(384) | For RAG search |
| detected_at | TIMESTAMPTZ | When signal was detected |
| source_url | TEXT | **NEW** — link to original source |
| source_name | TEXT | **NEW** — e.g. `sec_form4`, `job_postings` |
| source_timestamp | TIMESTAMPTZ | **NEW** — when source data was published |
| evidence_ids | UUID[] | **NEW** — FK refs to normalized records |
| idempotency_key | TEXT | **NEW** — dedup key, unique where non-null |

**Query patterns:**
- Signal feed: `SELECT * FROM signals ORDER BY detected_at DESC LIMIT 50`
- By ticker: `WHERE ticker = $1`
- By type: `WHERE type = $1`
- By score: `WHERE score >= $1`

### `company_profiles`
Enriched company data from Crustdata. PK is `domain`.

### `insights`
Fused insights per ticker. PK is `ticker`. Updated on each analysis run.

### `watchlist`
User watchlist. Composite PK `(user_id, ticker)`.

---

## Alt-Data MVP Tables (002_alt_data_mvp.sql)

### `companies`
Lightweight ticker-to-identity mapping for the MVP universe.

| Column | Type | Notes |
|--------|------|-------|
| ticker | TEXT PK | Stock ticker |
| name | TEXT | Company name |
| cik | TEXT | SEC Central Index Key |
| sector | TEXT | GICS sector |
| industry | TEXT | Sub-industry |
| domain | TEXT | Links to `company_profiles` |
| market_cap_bucket | TEXT | `mega`, `large`, `mid`, `small`, `micro` |
| in_universe | BOOLEAN | Whether actively tracked |

**Query patterns:**
- Universe list: `WHERE in_universe = TRUE`
- CIK lookup: `WHERE cik = $1`

### `source_runs`
Tracks every data collection job for auditability.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Auto-generated |
| source_name | TEXT | `sec_form4`, `sec_8k`, `job_postings`, `transcripts` |
| ticker | TEXT | Target ticker |
| status | TEXT | `running`, `completed`, `failed` |
| records_fetched | INTEGER | Count from source |
| records_stored | INTEGER | Count actually stored |
| error_message | TEXT | On failure |
| started_at / completed_at | TIMESTAMPTZ | Timing |

### `raw_documents`
Raw payloads before normalization. Deduped by `(source_name, content_hash)`.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| source_name | TEXT | |
| source_url | TEXT | |
| ticker | TEXT | |
| doc_type | TEXT | `form4_xml`, `8k_html`, `job_html`, `transcript_text` |
| content_hash | TEXT | SHA-256 dedup |
| raw_payload | JSONB | Full original payload |
| source_run_id | UUID FK | -> source_runs |

### `insider_trades`
Normalized SEC Form 4 data. Deduped by `idempotency_key`.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | TEXT | |
| cik | TEXT | SEC Central Index Key |
| filer_name | TEXT | Insider name |
| filer_title | TEXT | e.g. `CEO`, `CFO` |
| is_officer / is_director / is_ten_pct_owner | BOOLEAN | Insider classification |
| transaction_type | TEXT | `buy`, `sell`, `grant`, `exercise` |
| transaction_code | TEXT | SEC code (P, S, A, M) |
| shares | REAL | Number of shares |
| price_per_share | REAL | Per-share price |
| total_value | REAL | Total transaction value |
| filing_date | DATE | SEC filing date |
| transaction_date | DATE | Actual transaction date |
| source_url | TEXT | SEC EDGAR link |
| idempotency_key | TEXT UNIQUE | `{cik}:{filing_date}:{txn_code}:{shares}` |

**Query patterns (for `insider_buy_cluster` detector):**
```sql
SELECT * FROM insider_trades
WHERE ticker = $1
  AND transaction_type = 'buy'
  AND filing_date >= now() - interval '90 days'
ORDER BY filing_date DESC
```

### `job_postings`
Normalized job listings. Deduped by `idempotency_key`.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | TEXT | |
| title | TEXT | Job title |
| department | TEXT | `engineering`, `sales`, `marketing`, etc. |
| seniority | TEXT | `entry`, `mid`, `senior`, `lead`, `director`, `vp`, `c_suite` |
| source_name | TEXT | `linkedin`, `indeed`, `serpapi`, `fixture` |
| posted_date | DATE | |
| first_seen_at / last_seen_at | TIMESTAMPTZ | Tracking window |
| is_active | BOOLEAN | Still live? |
| idempotency_key | TEXT UNIQUE | `{source}:{company}:{title_hash}:{location}` |

**Query patterns (for `hiring_momentum` detector):**
```sql
SELECT department, COUNT(*) FROM job_postings
WHERE ticker = $1
  AND is_active = TRUE
  AND first_seen_at >= now() - interval '90 days'
GROUP BY department
```

### `filing_events`
Normalized SEC filings (8-K, etc). Deduped by `accession_number`.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | TEXT | |
| cik | TEXT | |
| filing_type | TEXT | `8-K`, `10-K`, `10-Q`, `S-1` |
| form_items | TEXT[] | 8-K item numbers: `['1.01', '5.02']` |
| filing_date | DATE | |
| headline / summary | TEXT | |
| source_url | TEXT | |
| accession_number | TEXT | SEC accession number |
| idempotency_key | TEXT UNIQUE | = accession_number |

**Material 8-K items:** `1.01` (agreements), `1.02` (termination), `2.01` (acquisition), `2.05` (delisting), `2.06` (impairment), `4.01` (auditor change), `5.02` (exec departure/appointment), `8.01` (other events)

**Query patterns (for `filing_catalyst` detector):**
```sql
SELECT * FROM filing_events
WHERE ticker = $1
  AND filing_type = '8-K'
  AND filing_date >= now() - interval '90 days'
ORDER BY filing_date DESC
```

### `transcript_chunks`
Earnings call transcript segments. Deduped by `idempotency_key`.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | TEXT | |
| fiscal_quarter | TEXT | `Q1 2025` |
| call_date | DATE | |
| speaker_name / speaker_role | TEXT | |
| section | TEXT | `prepared_remarks`, `qa`, `opening`, `closing` |
| chunk_index | INTEGER | Ordering within section |
| content | TEXT | Transcript text |
| idempotency_key | TEXT UNIQUE | `{ticker}:{quarter}:{speaker}:{chunk_index}` |

### `briefs`
AI-generated briefs triggered by signals.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | TEXT | |
| signal_id | TEXT FK | -> signals(id) |
| brief_type | TEXT | `signal`, `company_summary`, `weekly_digest` |
| headline | TEXT | |
| body | TEXT | Full brief text |
| evidence_summary | JSONB | Structured evidence refs |
| model_used | TEXT | e.g. `groq/llama-3.3-70b-versatile` |
| generated_at | TIMESTAMPTZ | |

---

## Signal Types

| Type | Detector Input | Key Evidence Fields in `signal.data` |
|------|---------------|--------------------------------------|
| `insider_buy_cluster` | `insider_trades` | `insider_count`, `total_value`, `window_days`, `buyers[]`, `avg_price` |
| `hiring_momentum` | `job_postings` | `total_postings`, `engineering_postings`, `weekly_avg`, `surge_ratio`, `top_departments{}` |
| `filing_catalyst` | `filing_events` | `filing_type`, `form_items[]`, `accession`, `is_material` |
| `transcript_tone_shift` | `transcript_chunks` | `fiscal_quarter`, `sentiment_before`, `sentiment_after`, `key_phrases[]` |

---

## Storage Helpers (src/storage/supabase.py)

All helpers are async. Key functions for each agent:

**Agent 2 (Ingestion) writes through:**
- `create_source_run(run)` / `complete_source_run(run_id, ...)`
- `store_raw_document(doc)`
- `upsert_insider_trade(trade)`
- `upsert_job_posting(posting)`
- `upsert_filing_event(event)`
- `upsert_transcript_chunk(chunk)`

**Agent 3 (Intelligence) reads through:**
- `get_insider_buy_cluster(ticker, days_back)` — returns insider buys
- `get_job_posting_counts(ticker, days_back)` — returns `{department: count, _total: n}`
- `get_material_filings(ticker, days_back)` — returns 8-K filings
- `get_transcript_chunks(ticker, fiscal_quarter, section)`

**Agent 4 (Product) reads through:**
- `get_signals(ticker, signal_type, min_score, limit)`
- `get_signal_detail(signal_id)` — signal + brief
- `get_company_detail(ticker)` — company + recent signals + briefs
- `get_briefs(ticker, signal_id, brief_type)`

**Agent 3 (Intelligence) writes through:**
- `store_signal(signal)` (existing)
- `store_brief(brief)`
