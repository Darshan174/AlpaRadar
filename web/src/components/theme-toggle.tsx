"use client";

import { useEffect, useState } from "react";

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("alpharadar-theme");
    const isDark = stored ? stored === "dark" : true;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("alpharadar-theme", next ? "dark" : "light");
  }

  return (
    <button
      onClick={toggle}
      className={`inline-flex items-center gap-2 rounded-full border border-(--color-border) bg-(--color-bg-card-strong) text-(--color-text-secondary) transition hover:border-(--color-border-strong) hover:text-(--color-text-primary) ${
        compact ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm"
      }`}
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? <SunIcon className={compact ? "h-3.5 w-3.5" : "h-4 w-4"} /> : <MoonIcon className={compact ? "h-3.5 w-3.5" : "h-4 w-4"} />}
      <span>{dark ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}

function SunIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
    </svg>
  );
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
    </svg>
  );
}
