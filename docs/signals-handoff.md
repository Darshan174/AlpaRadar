# Signal Engine — Handoff Document

## What was built

Three deterministic signal detectors and an orchestration engine at `packages/signals/`.

### 1. Insider Buy Cluster Detector (`detectors/insider_cluster.py`)

**What it detects:** Multiple company insiders purchasing shares within a rolling window (SEC Form 4 data).

**Formula:**
- Filter to open-market purchases (type = "P") within `window_days` of `as_of`
- Count unique insider buyers, aggregate total purchase value
- Compute buy/sell ratio = total_buy_value / total_sell_value
- Gate: `num_insiders >= 3`, `total_value >= $100K`, `buy_sell_ratio >= 2.0`
- Score = insider_count_score (40) + value_score (30) + ratio_score (20) + tightness_bonus (10)
- Tightness bonus rewards clusters where all buys happen in a short span

**Thresholds (in `config.py`):**
| Param | Default | Purpose |
|---|---|---|
| `min_insiders` | 3 | Minimum unique buyers to fire |
| `window_days` | 90 | Lookback window |
| `min_total_value_usd` | 100,000 | Minimum aggregate purchase value |
| `min_buy_sell_ratio` | 2.0 | Net buying conviction |
| `strong_insider_count` | 5 | Threshold for "strong" strength |
| `strong_total_value_usd` | 500,000 | Threshold for "strong" strength |

**Where logic is weak:**
- Does not distinguish between 10b5-1 planned purchases and discretionary buys (planned buys are less informative)
- Same-dollar-value purchases by a CEO vs. a VP are treated equally (could weight by seniority)
- No sector-relative comparison (3 insiders buying in biotech may be routine; in banks it's unusual)

---

### 2. Hiring Momentum Spike Detector (`detectors/hiring_momentum.py`)

**What it detects:** Job posting count spikes relative to a company's own rolling average baseline.

**Formula:**
- Compute rolling average of `total_postings` over baseline_window_days (default 60d)
- spike_ratio = latest.total_postings / baseline_avg
- Gate: `spike_ratio >= 1.5`, `total_postings >= 10`
- Score = base_score (60) + engineering_bonus (20) + consistency_bonus (10) + size_bonus (10)
- Engineering postings are boosted by 1.3x multiplier

**Thresholds:**
| Param | Default | Purpose |
|---|---|---|
| `min_spike_ratio` | 1.5 | Minimum spike to fire |
| `strong_spike_ratio` | 2.5 | Threshold for "strong" |
| `baseline_window_days` | 60 | Rolling average window |
| `min_posting_count` | 10 | Filter noise from tiny companies |
| `engineering_boost` | 1.3 | Weight multiplier for eng postings |

**Where logic is weak:**
- Seasonal hiring patterns (e.g., retail Q4 spikes) are not accounted for
- Cannot distinguish between organic growth and M&A-driven posting surges
- Relies on regular snapshot cadence; irregular collection intervals degrade the baseline average

---

### 3. Material Event / Tone-Change Detector (`detectors/material_event.py`)

Two sub-detectors in one file:

**A) 8-K Material Filing Detection:**
- Looks at 8-K filings from the last 30 days
- Flags filings containing high-severity item numbers (configurable list)
- Classifies sentiment by item type: acquisition items are bullish, impairments/departures are bearish
- Score = item_severity (50) + filing_count_bonus (20) + sentiment_bonus (30)

**B) Earnings Transcript Tone-Change:**
- Compares the two most recent transcript sentiment records
- weighted_delta = overall_delta * 0.4 + guidance_delta * 0.6
- Gate: `abs(weighted_delta) >= 0.25`
- Score = base_score (60) + keyword_bonus (20) + risk_spike_bonus (15) + base (10)
- Risk keyword spikes (>1.5x previous count, >=3 total) add 15 bonus points

**Thresholds:**
| Param | Default | Purpose |
|---|---|---|
| `high_severity_items` | [1.01, 1.02, 2.01, 2.04, 2.05, 2.06, 4.01, 4.02, 5.01, 5.02] | 8-K items that matter |
| `min_sentiment_delta` | 0.25 | Minimum weighted delta to fire |
| `strong_sentiment_delta` | 0.50 | Threshold for "strong" |
| `min_keyword_score` | 3.0 | Minimum keyword count change for bonus |

**Where logic is weak:**
- Transcript sentiment comes from a pre-processor (collector) — garbage in, garbage out. Keyword-based sentiment is crude.
- 8-K item classification is binary (high/low severity) — real impact varies enormously within the same item type
- No comparison to consensus expectations (e.g., a "bad" quarter that still beats analyst estimates is actually bullish)
- 30-day filing window is arbitrary; some 8-K events have delayed market impact

---

## Architecture

```
packages/signals/
  __init__.py
  config.py          # All thresholds, Pydantic models
  models.py          # Input data models (InsiderTransaction, JobPostingSnapshot, etc.)
  engine.py          # Orchestrator: run_all() and run_universe()
  detectors/
    __init__.py
    insider_cluster.py
    hiring_momentum.py
    material_event.py
  tests/             # 46 tests, all passing
    test_insider_cluster.py
    test_hiring_momentum.py
    test_material_event.py
    test_engine.py
  backtests/
    run_backtest.py  # Historical fixture evaluation
    fixtures/        # JSON fixture data
```

**Key design decisions:**
- Detectors are pure functions (no side effects, no DB, no API calls)
- All output dicts are compatible with the existing `signals` table schema
- Config is externalized in Pydantic models — no hardcoded thresholds in detector logic
- Each signal includes full evidence payloads for audit

---

## Integration notes

1. **Collectors → Signal Engine:** Collectors should write `InsiderTransaction`, `JobPostingSnapshot`, `MaterialFiling`, and `TranscriptSentiment` records. The engine consumes these.

2. **Signal Engine → DB:** The engine outputs dicts matching the `signals` table schema. The caller (cron worker) should insert these. Signal type values are `insider_buy_cluster`, `hiring_momentum`, `material_event`.

3. **New SignalType values:** The existing `src/core/models.py:SignalType` enum does not include our three types. Either extend that enum or store these as raw strings (the DB column is `TEXT` so this works).

4. **Fusion engine integration:** `src/intelligence/fusion.py` could call `packages.signals.engine.run_all()` alongside its existing detectors. The output dicts can be converted to `Signal` objects if needed.

5. **Cron scheduling:** Add a worker that calls `run_universe()` on the watchlist tickers every N hours.

---

## Open issues

- [ ] **No real data collectors yet** — detectors are built and tested on fixtures. Need SEC EDGAR Form 4 parser, job posting scraper, and 8-K/transcript ingestion.
- [ ] **Transcript sentiment pre-processor** — the `TranscriptSentiment` model assumes a keyword-based pre-processor exists. This needs to be built.
- [ ] **10b5-1 plan filtering** — insider buy detector should deprioritize planned trades vs. discretionary open-market purchases.
- [ ] **Seasonality adjustment** — hiring momentum should normalize for seasonal patterns (requires 12+ months of data).
- [ ] **Signal deduplication** — if the engine runs repeatedly, it may produce duplicate signals for the same underlying event. Need a dedup strategy (e.g., hash of ticker + type + date window).
- [ ] **Backtest on real data** — current backtests use synthetic fixtures. Validate with actual SEC filings and job posting histories.
