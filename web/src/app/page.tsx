"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getDatasetOverview } from "@/lib/api";

const SIGNAL_FAMILIES = ["Hiring", "Executive", "Divergence", "Competitor", "Sector"];
const WORKSPACE_VIEWS = ["Radar", "Compare", "Ask AI", "Watchlist", "Company DNA", "Signal Detail"];

const FEATURE_CARDS = [
  {
    title: "Radar",
    href: "/radar",
    eyebrow: "Signal feed",
    description: "Scan the full signal stream, filter conviction, and move from market-wide anomalies into company-level drilldowns.",
    bullets: ["Signal mix and market pulse", "Sector-signal panels from current feed data", "Fast filters for ticker, type, and score"],
  },
  {
    title: "Company DNA",
    href: "/company/NVDA",
    eyebrow: "Deep drilldown",
    description: "Unpack every ticker through its current signals, evidence, executive context, sector context, and briefing coverage.",
    bullets: ["Dense tabbed intelligence views", "Evidence-backed signal narratives", "No frontend-generated fake charts"],
  },
  {
    title: "Compare Rivals",
    href: "/compare?a=NVDA",
    eyebrow: "Competitive intelligence",
    description: "Put two names side-by-side to compare the signals, summaries, and evidence the API actually returns.",
    bullets: ["Score and sentiment comparison", "Signal mix and narrative comparison", "Evidence coverage side-by-side"],
  },
  {
    title: "Ask AI",
    href: "/chat",
    eyebrow: "Analyst copilot",
    description: "Interrogate the platform in plain English and keep the conversation grounded in current platform context.",
    bullets: ["Context focus by ticker", "Prompt starters by workflow", "Structured answers from current platform data"],
  },
  {
    title: "Watchlists",
    href: "/watchlist",
    eyebrow: "Portfolio monitoring",
    description: "Track the names you care about, see which alert categories dominate your book, and jump back into analysis quickly.",
    bullets: ["Actionable monitoring surface", "Coverage by alert type", "Quick links back into deep analysis"],
  },
  {
    title: "Evidence Layer",
    href: "/radar",
    eyebrow: "Primary-source context",
    description: "Every surfaced idea can be inspected through source evidence, AI brief sections, and structured signal metadata.",
    bullets: ["Evidence cards and timestamps", "AI brief with risk framing", "Clean company and signal linkage"],
  },
];

const WORKFLOW = [
  {
    step: "01",
    title: "Scan the market",
    description: "Start from radar to see what is changing across the current tracked companies and sectors.",
  },
  {
    step: "02",
    title: "Drill into a ticker",
    description: "Open company DNA to understand why a name is lighting up and which evidence supports the move.",
  },
  {
    step: "03",
    title: "Pressure-test the thesis",
    description: "Use compare and Ask AI to benchmark the current signal set against peers and surrounding context.",
  },
  {
    step: "04",
    title: "Monitor continuously",
    description: "Move the company into a watchlist and keep the intelligence stream close to your portfolio process.",
  },
];

const START_WITH = ["NVDA", "PLTR", "META", "SNOW", "CRM", "TSLA"];

export default function LandingPage() {
  const [ticker, setTicker] = useState("");
  const [dataset, setDataset] = useState<{ companies: number | null; signals: number | null; connected: boolean }>({
    companies: null,
    signals: null,
    connected: false,
  });
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    getDatasetOverview()
      .then((overview) => {
        if (!cancelled) {
          setDataset({
            companies: overview.companies,
            signals: overview.signals,
            connected: true,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDataset({
            companies: null,
            signals: null,
            connected: false,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    const nextTicker = ticker.trim().toUpperCase();
    if (nextTicker) router.push(`/company/${nextTicker}`);
  }

  return (
    <div className="relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 -z-10 h-[620px] bg-[radial-gradient(circle_at_top,rgba(249,115,22,0.22),transparent_35%)]" />
      <div className="absolute right-0 top-24 -z-10 h-80 w-80 rounded-full bg-sky-400/10 blur-[120px]" />
      <div className="absolute left-8 top-64 -z-10 h-72 w-72 rounded-full bg-emerald-400/10 blur-[120px]" />

      <header className="mx-auto max-w-[1440px] px-6 pt-6 sm:px-8 lg:px-10">
        <nav className="surface-panel flex flex-wrap items-center justify-between gap-4 rounded-[30px] px-5 py-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-linear-to-br from-orange-400 to-amber-600 text-base font-black text-white shadow-[0_16px_36px_rgba(249,115,22,0.34)]">
              AR
            </div>
            <div>
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
                AlphaRadar
              </div>
              <div className="mt-1 font-display text-xl text-(--color-text-primary)">
                Alternative Data Intelligence
              </div>
            </div>
          </Link>

          <div className="hidden items-center gap-6 text-sm text-(--color-text-secondary) lg:flex">
            <a href="#features" className="hover:text-(--color-text-primary)">Features</a>
            <a href="#workflow" className="hover:text-(--color-text-primary)">Workflow</a>
            <a href="#workspace" className="hover:text-(--color-text-primary)">Workspace</a>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="inline-flex min-h-[44px] items-center justify-center rounded-full border border-(--color-border) px-4 py-2 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary) active:scale-95"
            >
              Ask AI
            </Link>
            <Link
              href="/radar"
              className="inline-flex min-h-[44px] items-center justify-center rounded-full bg-linear-to-r from-orange-500 to-amber-500 px-5 py-2 text-sm font-semibold text-white shadow-[0_16px_30px_rgba(249,115,22,0.28)] transition hover:translate-y-[-1px] active:scale-95 active:translate-y-0"
            >
              Enter Radar
            </Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-[1440px] px-6 pb-24 pt-8 sm:px-8 lg:px-10 lg:pt-12">
        <section className="grid gap-10 lg:grid-cols-[minmax(0,1.05fr)_460px] lg:items-center animate-fade-up">
          <div className="max-w-3xl">
            <div className="kicker">Current platform overview</div>

            <h1 className="display-title mt-6 text-5xl leading-[0.92] text-(--color-text-primary) sm:text-6xl lg:text-7xl">
              Alternative-data research for teams that want signal density, not dashboard fluff.
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-(--color-text-secondary)">
              AlphaRadar brings hiring signals, executive movement, sector context, watchlists, and AI-assisted analysis into one workflow. This landing page now avoids hardcoded platform totals and only shows counts fetched from the current API.
            </p>

            <form onSubmit={handleSearch} className="surface-panel mt-8 flex flex-col gap-3 rounded-[30px] p-4 sm:flex-row sm:items-center">
              <div className="min-w-0 flex-1">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                  Jump straight into a ticker
                </div>
                <input
                  type="text"
                  value={ticker}
                  onChange={(event) => setTicker(event.target.value.toUpperCase())}
                  placeholder="Enter any ticker, e.g. NVDA"
                  maxLength={10}
                  className="mt-2 w-full bg-transparent text-lg text-(--color-text-primary) outline-none placeholder:text-(--color-text-muted)"
                />
              </div>
              <button
                type="submit"
                disabled={!ticker.trim()}
                className="inline-flex min-h-[48px] items-center justify-center rounded-[22px] bg-linear-to-r from-orange-500 to-amber-500 px-6 py-4 text-sm font-semibold text-white transition hover:translate-y-[-1px] active:scale-[0.98] active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Open Company DNA
              </button>
            </form>

            <div className="mt-5 flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                Start with
              </span>
              {START_WITH.map((item) => (
                <Link key={item} href={`/company/${item}`} className="data-chip hover:border-(--color-border-strong) hover:text-(--color-text-primary)">
                  {item}
                </Link>
              ))}
            </div>
          </div>

          <div className="surface-panel subtle-grid rounded-[36px] p-6 shadow-[0_30px_70px_rgba(2,6,23,0.32)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.26em] text-(--color-text-muted)">
                  Current Dataset
                </div>
                <div className="mt-2 font-display text-3xl text-(--color-text-primary)">
                  Counts here come from the active API, not from hardcoded marketing numbers.
                </div>
              </div>
              <span className="status-pill">{dataset.connected ? "API connected" : "API unavailable"}</span>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <div className="surface-panel-muted rounded-[26px] p-4">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                  Dataset totals
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                    <div className="text-xs text-(--color-text-muted)">Tracked companies</div>
                    <div className="mt-2 metric-value text-4xl text-(--color-text-primary)">{dataset.companies ?? "—"}</div>
                  </div>
                  <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-4">
                    <div className="text-xs text-(--color-text-muted)">Current signals</div>
                    <div className="mt-2 metric-value text-4xl text-(--color-text-primary)">{dataset.signals ?? "—"}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="surface-panel-muted rounded-[26px] p-4">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                    Product scope
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                      <div className="text-xs text-(--color-text-muted)">Signal families</div>
                      <div className="mt-1 text-sm font-semibold text-(--color-text-primary)">{SIGNAL_FAMILIES.length}</div>
                    </div>
                    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                      <div className="text-xs text-(--color-text-muted)">Workspace views</div>
                      <div className="mt-1 text-sm font-semibold text-(--color-text-primary)">{WORKSPACE_VIEWS.length}</div>
                    </div>
                    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                      <div className="text-xs text-(--color-text-muted)">Source of truth</div>
                      <div className="mt-1 text-sm font-semibold text-(--color-text-primary)">Current API responses</div>
                    </div>
                    <div className="rounded-[22px] border border-(--color-border) bg-(--color-bg-hover)/28 p-3">
                      <div className="text-xs text-(--color-text-muted)">Unavailable data</div>
                      <div className="mt-1 text-sm font-semibold text-(--color-text-primary)">Not shown</div>
                    </div>
                  </div>
                </div>

                <div className="surface-panel-muted rounded-[26px] p-4">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                    Product scope
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {[...SIGNAL_FAMILIES, "Watchlists", "AI Q&A"].map((item) => (
                      <span key={item} className="data-chip">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4 animate-fade-up stagger-1">
          {[
            { label: "Tracked Companies", value: dataset.companies ?? "—", detail: "from `/v1/companies`" },
            { label: "Current Signals", value: dataset.signals ?? "—", detail: "from `/v1/feed`" },
            { label: "Signal Families", value: SIGNAL_FAMILIES.length, detail: "supported signal categories" },
            { label: "Workspace Views", value: WORKSPACE_VIEWS.length, detail: "navigable product destinations" },
          ].map((item) => (
            <div key={item.label} className="surface-panel hover-lift rounded-[28px] p-5">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
                {item.label}
              </div>
              <div className="mt-4 metric-value text-4xl text-(--color-text-primary)">{item.value}</div>
              <div className="mt-2 text-sm text-(--color-text-secondary)">{item.detail}</div>
            </div>
          ))}
        </section>

        <section id="features" className="mt-20 animate-fade-up stagger-2">
          <div className="max-w-3xl">
            <div className="kicker">Platform Features</div>
            <h2 className="display-title mt-5 text-4xl text-(--color-text-primary) sm:text-5xl">
              A professional research flow from first anomaly to monitored thesis.
            </h2>
            <p className="mt-5 text-lg leading-8 text-(--color-text-secondary)">
              Every page in the product now has a clear job: scan, drill down, compare, interrogate, and monitor. The redesign keeps the denser workflow while removing fabricated platform statistics and synthetic visuals.
            </p>
          </div>

          <div className="mt-10 grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
            {FEATURE_CARDS.map((card) => (
              <Link key={card.title} href={card.href} className="surface-panel hover-lift rounded-[30px] p-6">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.24em] text-(--color-accent)">
                  {card.eyebrow}
                </div>
                <div className="mt-3 font-display text-2xl text-(--color-text-primary)">{card.title}</div>
                <p className="mt-3 text-sm leading-7 text-(--color-text-secondary)">{card.description}</p>
                <div className="mt-5 space-y-2">
                  {card.bullets.map((bullet) => (
                    <div key={bullet} className="flex items-start gap-2 text-sm text-(--color-text-secondary)">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-(--color-accent)" />
                      <span>{bullet}</span>
                    </div>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section id="workflow" className="mt-20 grid gap-8 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:items-start animate-fade-up stagger-3">
          <div className="surface-panel rounded-[34px] p-6 lg:p-8">
            <div className="kicker">Standard Workflow</div>
            <h2 className="display-title mt-5 text-4xl text-(--color-text-primary)">Built to feel like a serious analyst workspace.</h2>
            <p className="mt-5 text-base leading-8 text-(--color-text-secondary)">
              The UI now frames activity the way a research team expects: clear status, denser supporting panels, obvious next actions, and continuity across landing, app shell, and drilldown views. Unsupported or unauthenticated numbers are intentionally absent.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <div className="surface-panel-muted rounded-[24px] p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-(--color-text-muted)">Design Direction</div>
                <div className="mt-2 text-lg font-semibold text-(--color-text-primary)">Cinematic, dense, and research-facing</div>
              </div>
              <div className="surface-panel-muted rounded-[24px] p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-(--color-text-muted)">Information Style</div>
                <div className="mt-2 text-lg font-semibold text-(--color-text-primary)">Dashboards first, unsupported claims removed</div>
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            {WORKFLOW.map((item) => (
              <div key={item.step} className="surface-panel hover-lift rounded-[30px] p-6">
                <div className="flex items-start gap-4">
                  <div className="metric-value text-4xl text-(--color-accent)">{item.step}</div>
                  <div>
                    <div className="text-xl font-semibold text-(--color-text-primary)">{item.title}</div>
                    <p className="mt-2 text-sm leading-7 text-(--color-text-secondary)">{item.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section id="workspace" className="mt-20 surface-panel rounded-[36px] p-6 lg:p-8 animate-fade-up stagger-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="kicker">Inside The Workspace</div>
              <h2 className="display-title mt-5 text-4xl text-(--color-text-primary)">Every destination inside the product is denser and grounded in current API data.</h2>
            </div>
            <Link
              href="/radar"
              className="inline-flex min-h-[48px] items-center justify-center rounded-full border border-(--color-border) px-6 py-3 text-sm font-semibold text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary) active:scale-95"
            >
              Launch the app
            </Link>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-5">
            {[
              ["Radar", "Filter by type, conviction, and ticker while seeing current pulse metrics."],
              ["Company Tabs", "Overview, executives, competitors, and earnings show only what the current dataset actually provides."],
              ["Compare", "See which company is ahead on current signals and supporting evidence."],
              ["Ask AI", "Run research queries without leaving the platform context."],
              ["Watchlist", "Treat monitored names like an operating book, not a blank favorites list."],
            ].map(([title, description]) => (
              <div key={title} className="surface-panel-muted rounded-[26px] p-4">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-(--color-accent)">
                  {title}
                </div>
                <p className="mt-3 text-sm leading-7 text-(--color-text-secondary)">{description}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
