# Product Handoff: Briefing Layer, API, and MVP UI

## What Was Built

### 1. Seed Data Layer (`src/seed/data.py`)
Realistic mock data for 10 companies (NVDA, PLTR, META, SNOW, CRM, TSLA, AMZN, GOOGL, AAPL, MSFT) with 14 signals across all 5 signal types. Every signal includes:
- Source evidence with type, title, detail, source name, URL, and timestamp
- Pre-generated briefs with what_happened, why_it_matters, supporting_evidence, and risks
- Filtering by ticker, signal type, score, and date range

The seed layer lets the full app work without Supabase or any external API.

### 2. Briefing Service (`src/briefing/`)
- **`prompts.py`** — Versioned prompt templates (v1, v2). Each version has a system prompt and user template. All prompts explicitly prohibit buy/sell recommendations.
- **`service.py`** — `generate_brief(signal, prompt_version)` calls Groq via LiteLLM, parses JSON response into structured sections (what_happened, why_it_matters, supporting_evidence, risks). Falls back to seed briefs when LLM is unavailable.

### 3. API Routes (`src/api/routes/feed.py`)
New endpoints registered on the FastAPI app:

| Endpoint | Method | Description |
|---|---|---|
| `GET /v1/feed` | GET | Paginated signal feed with filters (ticker, type, min_score, date_from, date_to) |
| `GET /v1/signal/{id}` | GET | Signal detail with evidence and brief |
| `POST /v1/signal/{id}/brief` | POST | Generate/regenerate AI brief for a signal |
| `GET /v1/company/{ticker}` | GET | Company detail with all signals and briefs |
| `GET /v1/companies` | GET | List all tracked companies |

All endpoints serve from seed data. The existing Supabase-backed routes (`/v1/signals`, `/v1/analyze`) remain unchanged.

### 4. Web UI (`web/`)

**New pages:**
- **Signal Detail (`/signal/[id]`)** — Full signal view with:
  - Signal metadata (type, strength, sentiment, score)
  - Data point cards (key metrics from signal.data)
  - Source evidence cards (color-coded by type: SEC, JOBS, LI, MKT, etc.)
  - AI intelligence brief (what happened, why it matters, evidence, risks)
  - Breadcrumb navigation

**New components:**
- **`EvidenceCard`** — Renders a source evidence item with type badge, detail, source, URL link, and timestamp
- **`BriefSection`** — Renders the full AI brief with structured sections

**Enhanced pages:**
- **Radar (`/radar`)** — Added filter bar with ticker search, signal type dropdown, and minimum score selector. Signals now link to `/signal/[id]` detail pages.
- **Company (`/company/[ticker]`)** — Now uses the new `/v1/company/` API. Shows source evidence in overview tab. All signal cards link to their detail pages.

### 5. Tests (`tests/`)
38 tests covering:
- Seed data integrity (required fields, evidence, valid types, score ranges)
- Briefing prompts (versioning, no-buy/sell constraint, template formatting)
- Briefing service (evidence formatting, JSON parsing, fallback handling)
- API routes (feed, filters, signal detail, company detail, 404 handling)

## How to Swap From Mocks to Live Data

The seed data layer (`src/seed/`) is a drop-in replacement. When live ingestion is ready:

1. **In `src/api/routes/feed.py`**: Replace the `from src.seed.data import ...` calls with equivalent queries against `src/storage/supabase.py`.

2. **Signals table** already has the right schema (see `migrations/001_init.sql`). Add an `evidence` JSONB column:
   ```sql
   ALTER TABLE signals ADD COLUMN evidence JSONB DEFAULT '[]';
   ```

3. **Brief storage**: Create a `briefs` table:
   ```sql
   CREATE TABLE briefs (
     signal_id TEXT PRIMARY KEY REFERENCES signals(id),
     ticker TEXT NOT NULL,
     prompt_version TEXT NOT NULL,
     sections JSONB NOT NULL,
     evidence JSONB DEFAULT '[]',
     generated_at TIMESTAMPTZ DEFAULT now()
   );
   ```

4. **Collectors** should populate the `evidence` field on each signal with source metadata (type, title, detail, source, url, timestamp).

5. **Briefing service** already calls Groq — just set `GROQ_API_KEY` in environment.

## Open Issues

1. **No live data collectors** — SEC EDGAR, SerpAPI (Google Jobs), and FMP collectors need to be built to replace Crustdata
2. **Brief caching** — Currently regenerates on every POST. Add caching with TTL in Supabase briefs table.
3. **Date filter** — The `date_from`/`date_to` filters in the feed API compare ISO strings lexicographically, which works but should use proper datetime parsing for production.
4. **Sector heatmap** — The `SectorHeatmap` component still uses hardcoded data. Wire to live sector pulse signals.
5. **Mobile polish** — Signal detail page scrolls well but filter bar on radar page could use a collapsible design on mobile.
6. **Auth** — Feed and detail endpoints are currently unauthenticated. The existing `APIKeyMiddleware` applies to `/v1/analyze` but should cover new routes too.

## Integration Notes

- **Frontend API client** (`web/src/lib/api.ts`) has all new functions: `getFeed`, `getSignalDetail`, `generateBrief`, `getCompanyDetail`, `listCompanies`
- **Types** (`web/src/lib/types.ts`) includes `Evidence`, `Brief`, `BriefSections`, `SignalDetail`, `CompanyDetail`, `FeedResponse`
- The briefing service imports from `src.seed.data` for fallback — this import should be made conditional (try/except) when seed data is eventually removed
- All signal cards throughout the app now link to `/signal/[id]` for drill-down
