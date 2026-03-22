-- AlphaRadar Database Schema
-- Run against Supabase PostgreSQL (free tier)
-- Requires pgvector extension (enabled by default on Supabase)

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Signals Table ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,            -- hiring_surge, executive_move, etc.
    strength TEXT NOT NULL,        -- strong, moderate, weak
    sentiment TEXT NOT NULL,       -- bullish, bearish, neutral
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    headline TEXT NOT NULL,
    detail TEXT DEFAULT '',
    score REAL NOT NULL DEFAULT 0,
    data JSONB DEFAULT '{}',
    embedding vector(384),         -- fastembed BAAI/bge-small-en-v1.5 = 384 dims
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(type);
CREATE INDEX IF NOT EXISTS idx_signals_score ON signals(score DESC);
CREATE INDEX IF NOT EXISTS idx_signals_detected_at ON signals(detected_at DESC);

-- ── Company Profiles Table ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS company_profiles (
    domain TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ticker TEXT,
    industry TEXT DEFAULT '',
    sector TEXT DEFAULT '',
    country TEXT DEFAULT '',
    total_headcount INTEGER,
    headcount_trend_pct REAL,
    funding_total_usd REAL,
    competitors TEXT[] DEFAULT '{}',
    profile_json JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_company_ticker ON company_profiles(ticker);
CREATE INDEX IF NOT EXISTS idx_company_sector ON company_profiles(sector);

-- ── Fused Insights Table ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS insights (
    ticker TEXT PRIMARY KEY,
    company_name TEXT DEFAULT '',
    composite_score REAL NOT NULL DEFAULT 0,
    sentiment TEXT NOT NULL DEFAULT 'neutral',
    signal_count INTEGER DEFAULT 0,
    signal_ids TEXT[] DEFAULT '{}',
    summary TEXT DEFAULT '',
    llm_analysis TEXT DEFAULT '',
    insight_json JSONB DEFAULT '{}',
    embedding vector(384),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_insights_score ON insights(composite_score DESC);

-- ── Watchlist Table ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS watchlist (
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT DEFAULT '',
    alert_on TEXT[] DEFAULT '{}',
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);

-- ── Vector Similarity Search Functions ────────────────────────────────────────

CREATE OR REPLACE FUNCTION match_signals(
    query_embedding vector(384),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    type TEXT,
    strength TEXT,
    sentiment TEXT,
    ticker TEXT,
    company_name TEXT,
    headline TEXT,
    detail TEXT,
    score REAL,
    data JSONB,
    detected_at TIMESTAMPTZ,
    similarity REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id, s.type, s.strength, s.sentiment,
        s.ticker, s.company_name, s.headline, s.detail,
        s.score, s.data, s.detected_at,
        1 - (s.embedding <=> query_embedding)::REAL AS similarity
    FROM signals s
    WHERE s.embedding IS NOT NULL
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION match_insights(
    query_embedding vector(384),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    ticker TEXT,
    company_name TEXT,
    composite_score REAL,
    sentiment TEXT,
    summary TEXT,
    generated_at TIMESTAMPTZ,
    similarity REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.ticker, i.company_name, i.composite_score,
        i.sentiment, i.summary, i.generated_at,
        1 - (i.embedding <=> query_embedding)::REAL AS similarity
    FROM insights i
    WHERE i.embedding IS NOT NULL
    ORDER BY i.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
