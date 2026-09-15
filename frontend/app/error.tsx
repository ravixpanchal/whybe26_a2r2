"use client";

import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-6">
      <div className="max-w-md rounded-2xl border border-[var(--line)] bg-white p-8 text-center">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--brand)]">Something went wrong</p>
        <h1 className="display-font mt-4 text-3xl text-[var(--brand-dark)]">We couldn&apos;t load this view.</h1>
        <p className="mt-4 text-sm leading-6 text-[var(--muted)]">Please try again. Your assessment data has not been changed.</p>
        <button onClick={() => reset()} className="mt-7 rounded-full bg-[var(--brand)] px-5 py-3 text-sm font-bold text-white hover:bg-[var(--brand-dark)]">
          Try again
        </button>
      </div>
    </main>
  );
}
