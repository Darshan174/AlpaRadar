"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";

const SECTION_LABELS: { match: RegExp; title: string; subtitle: string }[] = [
  { match: /^\/radar/, title: "Radar", subtitle: "Current signal command center" },
  { match: /^\/compare/, title: "Compare", subtitle: "Side-by-side competitive intelligence" },
  { match: /^\/chat/, title: "Ask AI", subtitle: "Natural-language intelligence workspace" },
  { match: /^\/watchlist/, title: "Watchlist", subtitle: "Monitored companies and alert settings" },
  { match: /^\/company\//, title: "Company DNA", subtitle: "Multi-signal drilldown and evidence" },
  { match: /^\/signal\//, title: "Signal Detail", subtitle: "Catalyst context, evidence, and risks" },
];

function getWorkspaceMeta(pathname: string) {
  return (
    SECTION_LABELS.find((item) => item.match.test(pathname)) ?? {
      title: "Workspace",
      subtitle: "Alternative data intelligence",
    }
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const meta = getWorkspaceMeta(pathname);

  if (isLandingPage) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="min-h-screen p-2 sm:p-3 lg:p-4">
      <div className="surface-panel subtle-grid relative flex h-[calc(100vh-1rem)] overflow-hidden rounded-[32px] sm:h-[calc(100vh-1.5rem)] lg:h-[calc(100vh-2rem)]">
        <Sidebar />

        <div className="relative flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-50 border-b border-(--color-border) bg-(--color-bg-secondary)/80 px-4 py-3 backdrop-blur-2xl md:hidden">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <Link href="/" className="text-[0.7rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
                  AlphaRadar
                </Link>
                <div className="mt-1 truncate font-display text-lg text-(--color-text-primary)">
                  {meta.title}
                </div>
              </div>
              <ThemeToggle compact />
            </div>
          </header>

          <header className="hidden border-b border-(--color-border) bg-(--color-bg-secondary)/70 px-8 py-5 backdrop-blur-2xl md:flex md:items-center md:justify-between">
            <div className="min-w-0">
              <div className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-(--color-text-muted)">
                Workspace
              </div>
              <div className="mt-2 flex items-end gap-3">
                <h1 className="font-display text-2xl leading-none text-(--color-text-primary)">
                  {meta.title}
                </h1>
                <p className="pb-0.5 text-sm text-(--color-text-secondary)">{meta.subtitle}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="status-pill">Current workspace</div>
              <ThemeToggle />
            </div>
          </header>

          <main className="app-scroll min-h-0 flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
