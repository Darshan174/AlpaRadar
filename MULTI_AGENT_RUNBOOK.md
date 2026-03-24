# AlphaRadar Multi-Agent Runbook

This repo already exists and is not a blank MVP scaffold.

Current reality:
- Python/FastAPI backend in `src/`
- Next.js frontend in `web/`
- Supabase schema in `migrations/`
- Existing layers for ingestion, intelligence, analysis, alerts, storage, and API routes

Use the prompts below to split work across 4 worker agents plus 1 integrator.

## 1. Baseline Prep

Before you start, make sure the repo baseline is safe. Right now there is an untracked file: `CLAUDE.md`.

If you want that file available in all worktrees, commit it first. If not, leave it untracked.

Recommended setup:

```bash
cd /Users/darshann/Desktop/alpharadar
git status --short
git switch -c alpharadar-mvp-base

git worktree add ../alpharadar-agent1 -b agent-1-foundation alpharadar-mvp-base
git worktree add ../alpharadar-agent2 -b agent-2-ingestion alpharadar-mvp-base
git worktree add ../alpharadar-agent3 -b agent-3-intelligence alpharadar-mvp-base
git worktree add ../alpharadar-agent4 -b agent-4-product alpharadar-mvp-base
git worktree add ../alpharadar-integrator -b agent-integrator alpharadar-mvp-base
```

Use these folders:
- Agent 1: `/Users/darshann/Desktop/alpharadar-agent1`
- Agent 2: `/Users/darshann/Desktop/alpharadar-agent2`
- Agent 3: `/Users/darshann/Desktop/alpharadar-agent3`
- Agent 4: `/Users/darshann/Desktop/alpharadar-agent4`
- Integrator: `/Users/darshann/Desktop/alpharadar-integrator`

## 2. Shared Brief For All 4 Worker Agents

Paste this at the top of every worker prompt.

```text
You are working inside the existing AlphaRadar repo. Do not rewrite the stack.

Repo shape:
- Backend: FastAPI + Python in `src/`
- Frontend: Next.js in `web/`
- Database: Supabase/Postgres schema in `migrations/`
- Storage layer: `src/storage/supabase.py`

Goal:
Evolve the current AlphaRadar codebase into an MVP alternative-data intelligence product for US equities using public/free data.

Product constraints:
- Signals must be deterministic
- AI writes briefs only after a signal fires
- Every signal must be source-backed and timestamped
- No direct buy/sell advice
- Backward-compatible changes are preferred over rewrites

Target MVP scope:
- Monitor a small universe of US stocks
- Ingest public/free data for:
  - SEC insider and filing events
  - hiring momentum / job-posting signals
  - market context
- Detect at least these signal types:
  - `insider_buy_cluster`
  - `hiring_momentum`
  - `filing_catalyst`
  - `transcript_tone_shift` if transcript ingestion lands cleanly; otherwise degrade gracefully
- Show a product surface with:
  - signal feed
  - signal detail page with evidence
  - company detail page with recent signals and AI brief

Important engineering rules:
- Keep your edits inside your owned paths
- Do not remove existing functionality unless it directly blocks the MVP
- If a dependency from another agent is missing on your branch, create a local stub or adapter instead of blocking
- Preserve source URLs, source timestamps, and idempotency keys
- Add tests around non-trivial logic
- Leave a handoff markdown file summarizing what you built, assumptions, and integration risks
```

## 3. Agent 1 Prompt: Foundation, Contracts, Storage

Paste the shared brief first, then this.

```text
You own the foundation and data contract layer for AlphaRadar.

Your write ownership:
- `migrations/**`
- `src/core/**`
- `src/storage/**`
- `src/config.py`
- `src/api/schemas.py`
- `requirements.txt` if a new backend dependency is genuinely required
- `docs/contracts.md`
- `docs/agent1-handoff.md`
- storage/model tests

Do not edit:
- `src/ingestion/**`
- `src/intelligence/**`
- `src/analysis/**`
- `src/api/routes/**`
- `web/**`

Mission:
Extend the existing backend contracts so the rest of the team can build the MVP on top of a stable schema and model layer.

Required outcomes:
1. Add a new migration after `001_init.sql` for the alternative-data MVP. Do not rewrite the existing migration.
2. Preserve existing `signals`, `insights`, `company_profiles`, and `watchlist` behavior.
3. Introduce normalized storage for public-data ingestion. Use practical tables only. Minimum targets:
   - `source_runs`
   - `raw_documents`
   - `insider_trades`
   - `job_postings`
   - `filing_events`
   - `transcript_chunks` or equivalent if transcript support is feasible
4. Extend backend models in `src/core/models.py` with the new signal types and any normalized record models needed by ingestion and detection.
5. Add storage helpers in `src/storage/supabase.py` for:
   - upserting normalized records
   - storing raw payload metadata
   - fetching historical windows needed by detectors
   - looking up signal detail/company detail payloads
6. Keep fields for:
   - source URL
   - source name
   - source timestamp
   - dedupe/idempotency key
   - ticker and company identity
7. Keep compatibility with the current API response shapes where practical.

Design rules:
- Add, do not break
- Prefer JSONB for payloads that are still evolving
- Use simple, explicit table names
- Avoid over-modeling
- Make detector queries easy for Agent 3

Acceptance criteria:
- Backend models compile
- Migration is additive and readable
- Storage helpers are usable without editing your files later
- Contract docs explain tables, key fields, and intended query patterns
- Handoff doc lists anything other agents must assume
```

## 4. Agent 2 Prompt: Public-Data Ingestion

Paste the shared brief first, then this.

```text
You own the ingestion layer for AlphaRadar.

Your write ownership:
- `src/ingestion/**`
- `tests/ingestion/**`
- `tests/fixtures/**` for ingestion fixtures
- `docs/agent2-handoff.md`

Do not edit:
- `migrations/**`
- `src/core/**`
- `src/storage/**`
- `src/api/**`
- `src/intelligence/**`
- `src/analysis/**`
- `web/**`

Mission:
Implement public-data collection and normalization entrypoints that write into the contract layer defined by Agent 1.

Required outcomes:
1. Keep the current Crustdata integration intact. Do not remove it unless it directly blocks MVP work.
2. Add SEC ingestion modules under `src/ingestion/` for:
   - company identity / CIK lookup
   - Form 4 insider trade fetch + parse
   - 8-K filing event fetch + parse
   - optional 13F helper if easy, but Form 4 and 8-K matter more for MVP
3. Add hiring/job signal ingestion under `src/ingestion/` with a provider abstraction:
   - primary provider can be SerpAPI or another free/public-compatible approach
   - fixture-backed fallback must exist so the code is testable without live keys
4. If transcript ingestion is realistic in this repo, add a clean adapter; otherwise add a stub provider and document the next step.
5. Preserve raw payload metadata and write normalized records through storage helpers.
6. Expose callable entrypoints that later routes/schedulers can use, for example:
   - `sync_company_alt_data(ticker: str)`
   - `sync_sec_activity(ticker: str)`
   - `sync_job_postings(ticker: str)`

Design rules:
- Provider interfaces first, implementation second
- Graceful fallback to fixtures when env vars or free-tier limits block live calls
- Log source runs and errors clearly
- Dedupe repeated records
- Do not put signal logic here

Acceptance criteria:
- Collectors are modular and testable
- At least one ticker can run through fixture-backed ingestion end-to-end
- SEC and jobs ingestion both have tests
- Handoff doc lists env vars, rate-limit assumptions, and known data-quality gaps
```

## 5. Agent 3 Prompt: Deterministic Signals, Fusion, AI Briefing

Paste the shared brief first, then this.

```text
You own the intelligence layer for AlphaRadar.

Your write ownership:
- `src/intelligence/**`
- `src/analysis/**`
- `src/alerts/**`
- `tests/intelligence/**`
- `tests/analysis/**`
- `docs/agent3-handoff.md`

Do not edit:
- `migrations/**`
- `src/core/**`
- `src/storage/**`
- `src/ingestion/**`
- `src/api/routes/**`
- `web/**`

Mission:
Turn normalized public-data records into deterministic, explainable investment signals, then generate AI briefs that only explain what the detectors already found.

Required outcomes:
1. Implement or extend detectors for:
   - `insider_buy_cluster`
   - `hiring_momentum`
   - `filing_catalyst`
   - `transcript_tone_shift` only if transcript data exists cleanly; otherwise handle absence gracefully
2. Update fusion/scoring so the new signals contribute to a coherent per-company insight.
3. Ensure each produced signal includes auditable evidence in `signal.data`, such as:
   - triggering rows or event IDs
   - source URLs
   - source timestamps
   - threshold values
   - before/after comparison windows
4. Update LLM prompting in `src/analysis/` so generated briefs:
   - summarize only flagged evidence
   - include what happened, why it matters, and alternate explanations
   - avoid direct investment advice
5. Make the non-LLM path useful. If no Groq key exists, the system should still return a deterministic summary.
6. Update alert formatting if needed so human-readable alerts reflect the new source-backed signals.

Design rules:
- Detector logic must be deterministic and configurable
- Prefer explainable heuristics over opaque scoring
- Preserve existing functionality unless it conflicts with the MVP
- Keep false-positive guards explicit

Acceptance criteria:
- Signal logic has fixture-driven tests
- AI prompt path and non-AI fallback both work
- Handoff doc explains formulas, thresholds, and weak points
- Your code can plug into Agent 4 without requiring web changes from your side
```

## 6. Agent 4 Prompt: API Surface and Product UI

Paste the shared brief first, then this.

```text
You own the user-facing product surface for AlphaRadar.

Your write ownership:
- `src/api/routes/**`
- `web/**`
- `tests/api/**`
- `docs/agent4-handoff.md`

Do not edit:
- `migrations/**`
- `src/core/**`
- `src/storage/**`
- `src/ingestion/**`
- `src/intelligence/**`
- `src/analysis/**`

Mission:
Turn the existing backend and web app into a usable MVP product with a signal feed, source-backed detail views, and company pages.

Required outcomes:
1. Build or extend API routes for:
   - signal feed with filters
   - signal detail by ID
   - company detail by ticker
   - reuse existing analyze endpoints where sensible
2. Update the web app to support:
   - a signal feed page
   - signal detail page with evidence and timestamps
   - company detail page with recent signals, summary, and brief
   - filters by ticker, signal type, and score/date when practical
3. Update `web/src/lib/api.ts` and `web/src/lib/types.ts` to match the product surface you expose.
4. If backend data is incomplete on your branch, use mocked adapters or temporary response shims, but code toward the shared contract and document the assumption.
5. Prefer working with the existing UI patterns, but make the experience feel like a product, not just demo widgets.

Design rules:
- Source transparency must be visible in the UI
- Avoid generic “AI said so” presentation
- Do not invent data fields that the backend cannot reasonably supply
- Keep routes backward-compatible when practical

Acceptance criteria:
- Web app builds
- Feed and detail views render against mocked or real data
- API route behavior is documented in your handoff
- Your branch can be merged after backend branches with manageable conflict risk
```

## 7. Integrator Prompt

If you want me to do the integration later, come back and tell me to work in `/Users/darshann/Desktop/alpharadar-integrator`.

If you want a separate integration agent, use this prompt:

```text
You are the integration owner for AlphaRadar. You are working in `/Users/darshann/Desktop/alpharadar-integrator` on branch `agent-integrator`.

Your job is to merge the worker branches into one functioning product branch and fix integration issues without rewriting the architecture.

Worker branches:
- `agent-1-foundation`
- `agent-2-ingestion`
- `agent-3-intelligence`
- `agent-4-product`

Merge order:
1. `agent-1-foundation`
2. `agent-2-ingestion`
3. `agent-3-intelligence`
4. `agent-4-product`

After each merge:
1. Resolve conflicts carefully
2. Run backend tests: `pytest`
3. Run frontend validation: `cd web && npm run build`
4. Fix only integration breakages, contract mismatches, import issues, and obvious regressions
5. Commit the merge resolution before moving to the next branch

Rules:
- Do not silently drop worker changes
- Prefer the schema/contracts introduced by Agent 1 when conflicts are ambiguous
- Preserve backward compatibility where possible
- If a branch depends on a missing helper, add the smallest compatible integration fix
- Stop only if the conflict is truly semantic and cannot be resolved safely

Final deliverables:
- one merged working branch
- short integration report
- list of remaining issues or follow-up cleanup work
```

## 8. Operator Workflow

1. Create the worktrees.
2. Open each worktree in a separate agent.
3. Paste the shared brief plus the matching worker prompt.
4. Let them work in parallel.
5. When all 4 are done, either:
   - ask me to integrate them, or
   - paste the integrator prompt into a fifth agent pointed at `/Users/darshann/Desktop/alpharadar-integrator`

## 9. What To Send Me Later

When the workers finish, send me:
- the 4 branch names
- whether any agent changed its ownership boundaries
- whether you want me to integrate in `/Users/darshann/Desktop/alpharadar-integrator`

Then I can do the actual merge, resolve conflicts, run validation, and hand back the integrated result.
