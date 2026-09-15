"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { AssessmentResponse } from "@/types/assessment";

export default function AssessmentResultsPage() {
  const [result] = useState<AssessmentResponse | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = window.sessionStorage.getItem("credilens:last-assessment");
    return stored ? (JSON.parse(stored) as AssessmentResponse) : null;
  });

  if (!result) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-6">
        <Card className="max-w-md p-8 text-center">
          <h1 className="display-font text-3xl text-[var(--brand-dark)]">No assessment found</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">Start a new assessment to see your result.</p>
          <Button href="/assessment" className="mt-6">Start assessment</Button>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-10 lg:px-10">
      <div className="mx-auto max-w-4xl">
        <Link href="/" className="text-sm font-bold text-[var(--brand)]">← CrediLens home</Link>
        <div className="mt-10">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">Assessment result</p>
          <h1 className="display-font mt-4 text-5xl tracking-[-0.04em] text-[var(--brand-dark)]">A signal, with context.</h1>
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-[1fr_1.3fr]">
          <Card className="p-8">
            <p className="text-sm text-[var(--muted)]">Default-risk probability</p>
            <p className="display-font mt-4 text-6xl text-[var(--brand-dark)]">
              {(result.risk_probability * 100).toFixed(1)}%
            </p>
            <p className="mt-4 inline-flex rounded-full bg-[#e0f1e8] px-3 py-1 text-sm font-bold capitalize text-[var(--brand)]">
              {result.risk_category} risk
            </p>
            <p className="mt-8 text-xs leading-5 text-[var(--muted)]">
              This result is educational and is not an official credit decision.
            </p>
          </Card>
          <Card className="p-8">
            <div className="flex items-center justify-between gap-4">
              <h2 className="display-font text-2xl text-[var(--brand-dark)]">Reliability</h2>
              <span className="font-bold capitalize text-[var(--brand)]">{result.reliability.level}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{result.reliability.disclaimer}</p>
            <ul className="mt-5 space-y-2 text-sm text-[var(--muted)]">
              {result.reliability.reasons.map((reason) => <li key={reason}>• {reason}</li>)}
            </ul>
            <h2 className="display-font mt-8 text-2xl text-[var(--brand-dark)]">Leading factors</h2>
            <div className="mt-4 space-y-3">
              {result.feature_contributions.slice(0, 5).map((factor) => (
                <div key={factor.feature} className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-[var(--muted)]">{factor.feature.replaceAll("_", " ")}</span>
                  <span className={factor.direction === "risk_increasing" ? "font-bold text-amber-700" : "font-bold text-[var(--brand)]"}>
                    {factor.direction === "risk_increasing" ? "+" : "−"}{Math.abs(factor.contribution).toFixed(3)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <Button href="/assessment" variant="outline" className="mt-8">Start another assessment</Button>
      </div>
    </main>
  );
}
