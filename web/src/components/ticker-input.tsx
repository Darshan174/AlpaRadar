"use client";

import { useState, type FormEvent } from "react";

interface TickerInputProps {
  onSubmit: (ticker: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export function TickerInput({ onSubmit, loading, placeholder }: TickerInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const ticker = value.trim().toUpperCase();
    if (ticker) onSubmit(ticker);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value.toUpperCase())}
        placeholder={placeholder || "Enter ticker (e.g. NVDA)"}
        className="flex-1 rounded-lg border border-(--color-border) bg-(--color-bg-card) px-4 py-2.5 text-sm text-(--color-text-primary) placeholder:text-(--color-text-muted) outline-none transition-colors focus:border-(--color-accent)"
        maxLength={10}
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="rounded-lg bg-(--color-accent) px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}
