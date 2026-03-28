-- AlphaRadar Alternative Data MVP — Additive Migration
-- Adds normalized storage for SEC filings, insider trades, job postings, and transcripts
-- Run AFTER 001_init.sql

-- ── Source Runs ─────────────────────────────────────────────────────────────
-- Tracks every data collection job for auditability and dedup

CREATE TABLE IF NOT EXISTS source_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,          -- 'sec_form4', 'sec_8k', 'job_postings', 'transcripts'
    ticker TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',  -- running, completed, failed
    records_fetched INTEGER DEFAULT 0,
    records_stored INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_source_runs_ticker ON source_runs(ticker);
CREATE INDEX IF NOT EXISTS idx_source_runs_source ON source_runs(source_name);
CREATE INDEX IF NOT EXISTS idx_source_runs_started ON source_runs(started_at DESC);

-- ── Raw Documents ───────────────────────────────────────────────────────────
-- Stores raw payloads from any source before normalization

CREATE TABLE IF NOT EXISTS raw_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    source_url TEXT,
    ticker TEXT,
    doc_type TEXT NOT NULL,             -- 'form4_xml', '8k_html', 'job_html', 'transcript_text'
    content_hash TEXT NOT NULL,         -- SHA-256 for dedup
    raw_payload JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_run_id UUID REFERENCES source_runs(id),
    UNIQUE(source_name, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_raw_docs_ticker ON raw_documents(ticker);
CREATE INDEX IF NOT EXISTS idx_raw_docs_source ON raw_documents(source_name);
CREATE INDEX IF NOT EXISTS idx_raw_docs_hash ON raw_documents(content_hash);

-- ── Insider Trades ──────────────────────────────────────────────────────────
-- Normalized SEC Form 4 data

CREATE TABLE IF NOT EXISTS insider_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    cik TEXT NOT NULL,                  -- SEC Central Index Key
    filer_name TEXT NOT NULL,
    filer_title TEXT DEFAULT '',
    is_officer BOOLEAN DEFAULT FALSE,
    is_director BOOLEAN DEFAULT FALSE,
    is_ten_pct_owner BOOLEAN DEFAULT FALSE,
    transaction_type TEXT NOT NULL,     -- 'buy', 'sell', 'grant', 'exercise'
    transaction_code TEXT DEFAULT '',   -- SEC transaction code (P, S, A, M, etc.)
    shares REAL NOT NULL,
    price_per_share REAL,
    total_value REAL,
    shares_owned_after REAL,
    filing_date DATE NOT NULL,
    transaction_date DATE,
    source_url TEXT NOT NULL,
    source_timestamp TIMESTAMPTZ,
    idempotency_key TEXT NOT NULL UNIQUE, -- e.g. '{cik}:{filing_date}:{transaction_code}:{shares}'
    raw_document_id UUID REFERENCES raw_documents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_insider_ticker ON insider_trades(ticker);
CREATE INDEX IF NOT EXISTS idx_insider_filing_date ON insider_trades(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_insider_type ON insider_trades(transaction_type);
CREATE INDEX IF NOT EXISTS idx_insider_cik ON insider_trades(cik);
CREATE INDEX IF NOT EXISTS idx_insider_filer ON insider_trades(filer_name);

-- ── Job Postings ────────────────────────────────────────────────────────────
-- Normalized job listing data from any provider

CREATE TABLE IF NOT EXISTS job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    title TEXT NOT NULL,
    department TEXT DEFAULT '',          -- 'engineering', 'sales', 'marketing', etc.
    seniority TEXT DEFAULT '',           -- 'entry', 'mid', 'senior', 'lead', 'director', 'vp', 'c_suite'
    location TEXT DEFAULT '',
    is_remote BOOLEAN DEFAULT FALSE,
    description_snippet TEXT DEFAULT '',
    source_name TEXT NOT NULL,           -- 'linkedin', 'indeed', 'serpapi', 'fixture'
    source_url TEXT,
    posted_date DATE,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE,
    idempotency_key TEXT NOT NULL UNIQUE, -- e.g. '{source}:{company}:{title_hash}:{location}'
    raw_document_id UUID REFERENCES raw_documents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_ticker ON job_postings(ticker);
CREATE INDEX IF NOT EXISTS idx_jobs_department ON job_postings(department);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON job_postings(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON job_postings(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON job_postings(first_seen_at DESC);

-- ── Filing Events ───────────────────────────────────────────────────────────
-- Normalized SEC 8-K and other material filing events

CREATE TABLE IF NOT EXISTS filing_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    cik TEXT NOT NULL,
    filing_type TEXT NOT NULL,           -- '8-K', '10-K', '10-Q', 'S-1', etc.
    form_items TEXT[] DEFAULT '{}',      -- 8-K item numbers: ['1.01', '2.01', '5.02']
    filing_date DATE NOT NULL,
    period_of_report DATE,
    headline TEXT DEFAULT '',
    summary TEXT DEFAULT '',
    source_url TEXT NOT NULL,
    accession_number TEXT NOT NULL,      -- SEC accession number, natural dedup key
    source_timestamp TIMESTAMPTZ,
    idempotency_key TEXT NOT NULL UNIQUE, -- accession_number
    raw_document_id UUID REFERENCES raw_documents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filing_events(ticker);
CREATE INDEX IF NOT EXISTS idx_filings_type ON filing_events(filing_type);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filing_events(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_filings_accession ON filing_events(accession_number);
CREATE INDEX IF NOT EXISTS idx_filings_items ON filing_events USING gin(form_items);

-- ── Transcript Chunks ───────────────────────────────────────────────────────
-- Earnings call transcript segments for tone analysis

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    fiscal_quarter TEXT NOT NULL,        -- 'Q1 2025', 'Q4 2024'
    call_date DATE NOT NULL,
    speaker_name TEXT DEFAULT '',
    speaker_role TEXT DEFAULT '',        -- 'ceo', 'cfo', 'analyst', 'operator'
    section TEXT DEFAULT '',             -- 'prepared_remarks', 'qa', 'opening', 'closing'
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    source_name TEXT DEFAULT '',
    source_url TEXT,
    source_timestamp TIMESTAMPTZ,
    idempotency_key TEXT NOT NULL UNIQUE, -- '{ticker}:{fiscal_quarter}:{speaker}:{chunk_index}'
    raw_document_id UUID REFERENCES raw_documents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transcripts_ticker ON transcript_chunks(ticker);
CREATE INDEX IF NOT EXISTS idx_transcripts_quarter ON transcript_chunks(fiscal_quarter);
CREATE INDEX IF NOT EXISTS idx_transcripts_call_date ON transcript_chunks(call_date DESC);
CREATE INDEX IF NOT EXISTS idx_transcripts_section ON transcript_chunks(section);

-- ── Add source fields to existing signals table ─────────────────────────────
-- These are safe ADDs, not modifications to existing columns

ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_name TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_timestamp TIMESTAMPTZ;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS evidence_ids UUID[] DEFAULT '{}';
ALTER TABLE signals ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

-- Unique index on idempotency_key (partial — nulls allowed for legacy rows)
CREATE UNIQUE INDEX IF NOT EXISTS idx_signals_idemp
    ON signals(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- ── Companies lookup table ──────────────────────────────────────────────────
-- Lightweight ticker-to-identity mapping for the MVP universe

CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cik TEXT,                            -- SEC Central Index Key
    sector TEXT DEFAULT '',
    industry TEXT DEFAULT '',
    domain TEXT DEFAULT '',              -- links to company_profiles if enriched
    market_cap_bucket TEXT DEFAULT '',   -- 'mega', 'large', 'mid', 'small', 'micro'
    in_universe BOOLEAN DEFAULT TRUE,    -- part of the tracked MVP universe
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_companies_cik ON companies(cik);
CREATE INDEX IF NOT EXISTS idx_companies_universe ON companies(in_universe) WHERE in_universe = TRUE;

-- ── Briefs ──────────────────────────────────────────────────────────────────
-- AI-generated briefs triggered by signal detection

CREATE TABLE IF NOT EXISTS briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    signal_id TEXT REFERENCES signals(id),
    brief_type TEXT NOT NULL DEFAULT 'signal', -- 'signal', 'company_summary', 'weekly_digest'
    headline TEXT NOT NULL,
    body TEXT NOT NULL,
    evidence_summary JSONB DEFAULT '{}',
    model_used TEXT DEFAULT '',
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_briefs_ticker ON briefs(ticker);
CREATE INDEX IF NOT EXISTS idx_briefs_signal ON briefs(signal_id);
CREATE INDEX IF NOT EXISTS idx_briefs_generated ON briefs(generated_at DESC);
