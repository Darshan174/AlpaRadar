"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getDatasetOverview } from "@/lib/api";
import { ThemeToggle } from "./theme-toggle";

const NAV_ITEMS = [
  { href: "/radar", label: "Radar", icon: RadarIcon, description: "Current signal feed" },
  { href: "/compare", label: "Compare", icon: CompareIcon, description: "Company versus company" },
  { href: "/chat", label: "Ask AI", icon: MessageIcon, description: "Natural-language research" },
  { href: "/watchlist", label: "Watchlist", icon: EyeIcon, description: "Monitored companies" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      <aside className="hidden w-[320px] shrink-0 border-r border-(--color-border) bg-(--color-bg-secondary)/76 backdrop-blur-2xl md:flex">
        <SidebarContent pathname={pathname} />
      </aside>

      <nav className="fixed bottom-3 left-3 right-3 z-50 flex rounded-full border border-(--color-border) bg-(--color-bg-card-strong)/92 p-1 shadow-[0_18px_36px_rgba(2,6,23,0.24)] backdrop-blur-2xl md:hidden">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-1 flex-col items-center gap-1 rounded-full py-2 text-[10px] font-semibold uppercase tracking-[0.14em] transition ${
                active
                  ? "bg-linear-to-r from-orange-500 to-amber-500 text-white"
                  : "text-(--color-text-muted)"
              }`}
            >
              <item.icon className="h-[1.125rem] w-[1.125rem]" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

function SidebarContent({ pathname }: { pathname: string }) {
  const [stats, setStats] = useState<{ companies: number | null; signals: number | null; connected: boolean }>({
    companies: null,
    signals: null,
    connected: false,
  });

  useEffect(() => {
    let cancelled = false;

    getDatasetOverview()
      .then((overview) => {
        if (!cancelled) {
          setStats({
            companies: overview.companies,
            signals: overview.signals,
            connected: true,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStats({
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

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-(--color-border) px-5 py-5">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-linear-to-br from-orange-400 to-amber-600 text-base font-black text-white shadow-[0_16px_36px_rgba(249,115,22,0.34)]">
            AR
          </div>
          <div className="min-w-0">
            <div className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
              AlphaRadar
            </div>
            <div className="mt-1 font-display text-xl text-(--color-text-primary)">
              Alt-Data Intelligence
            </div>
          </div>
        </Link>

        <div className="mt-4 grid grid-cols-2 gap-2">
          <div className="surface-panel-muted rounded-2xl px-3 py-3">
            <div className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
              Companies
            </div>
            <div className="mt-2 metric-value text-xl text-(--color-text-primary)">{stats.companies ?? "—"}</div>
            <div className="mt-1 text-xs text-(--color-text-secondary)">from current API</div>
          </div>
          <div className="surface-panel-muted rounded-2xl px-3 py-3">
            <div className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-(--color-text-muted)">
              Signals
            </div>
            <div className="mt-2 metric-value text-xl text-(--color-text-primary)">{stats.signals ?? "—"}</div>
            <div className="mt-1 text-xs text-(--color-text-secondary)">feed total</div>
          </div>
        </div>
      </div>

      <div className="px-4 pt-4">
        <SearchTicker />
      </div>

      <div className="px-4 pt-5">
        <div className="text-[0.68rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
          Workspace
        </div>
      </div>

      <nav className="min-h-0 flex-1 space-y-2 overflow-y-auto px-4 py-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group block rounded-[22px] border px-4 py-3 transition-all ${
                active
                  ? "border-(--color-accent)/30 bg-(--color-accent)/12 shadow-[0_14px_28px_rgba(249,115,22,0.12)]"
                  : "border-(--color-border) bg-(--color-bg-card)/70 hover:border-(--color-border-strong) hover:bg-(--color-bg-hover)/40"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-0.5 flex h-10 w-10 items-center justify-center rounded-2xl ${
                    active
                      ? "bg-(--color-accent) text-white"
                      : "bg-(--color-bg-hover) text-(--color-text-secondary) group-hover:text-(--color-text-primary)"
                  }`}
                >
                  <item.icon className="h-[1.125rem] w-[1.125rem]" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className={`text-sm font-semibold ${active ? "text-(--color-text-primary)" : "text-(--color-text-secondary)"}`}>
                    {item.label}
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-(--color-text-muted)">
                    {item.description}
                  </p>
                </div>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-(--color-border) px-4 py-4">
        <div className="surface-panel-muted rounded-[22px] p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
                Dataset
              </div>
              <div className="mt-1 text-sm font-semibold text-(--color-text-primary)">
                {stats.connected ? "API connected" : "Counts unavailable"}
              </div>
            </div>
            {stats.connected ? <div className="live-dot" /> : null}
          </div>

          <p className="mt-4 text-xs leading-6 text-(--color-text-secondary)">
            Sidebar totals are fetched from the current API responses. Hardcoded platform counts have been removed.
          </p>

          <div className="mt-4 flex items-center justify-between gap-3">
            <div className="text-xs text-(--color-text-muted)">Interface theme</div>
            <ThemeToggle compact />
          </div>
        </div>
      </div>
    </div>
  );
}

function SearchTicker() {
  return (
    <form
      action="/company"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const input = form.querySelector("input") as HTMLInputElement;
        const value = input.value.trim().toUpperCase();
        if (value) window.location.href = `/company/${value}`;
      }}
    >
      <div className="relative">
        <SearchIcon className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-(--color-text-muted)" />
        <input
          type="text"
          placeholder="Drill into any ticker"
          maxLength={10}
          className="w-full rounded-[20px] border border-(--color-border) bg-(--color-bg-card-strong) py-3 pl-11 pr-4 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none transition focus:border-(--color-accent) focus:ring-2 focus:ring-(--color-accent)/20"
        />
      </div>
    </form>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
    </svg>
  );
}

function RadarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.652a3.75 3.75 0 0 1 0-5.304m5.304 0a3.75 3.75 0 0 1 0 5.304m-7.425 2.121a6.75 6.75 0 0 1 0-9.546m9.546 0a6.75 6.75 0 0 1 0 9.546M5.106 18.894c-3.808-3.807-3.808-9.98 0-13.788m13.788 0c3.808 3.807 3.808 9.98 0 13.788M12 12h.008v.008H12V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
    </svg>
  );
}

function CompareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
}

function MessageIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}
