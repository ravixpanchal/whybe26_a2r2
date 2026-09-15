"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { simulateAssessment } from "@/lib/api";
import type { AssessmentRequest, AssessmentResponse, BorrowerInput } from "@/types/assessment";

const editableFields = [
  ["income_month_1", "Income month 1", "number"],
  ["income_month_2", "Income month 2", "number"],
  ["income_month_3", "Income month 3", "number"],
  ["num_income_sources", "Income sources", "number"],
  ["months_at_current_job", "Months at current job", "number"],
  ["loan_tenure_months", "Loan tenure months", "number"],
] as const;

export default function SimulatorPage() {
  const [input, setInput] = useState<BorrowerInput | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = window.sessionStorage.getItem("credilens:last-input");
    return stored ? (JSON.parse(stored) as BorrowerInput) : null;
  });
  const [original] = useState<AssessmentResponse | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = window.sessionStorage.getItem("credilens:last-assessment");
    return stored ? (JSON.parse(stored) as AssessmentResponse) : null;
  });
  const [simulated, setSimulated] = useState<AssessmentResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!input || !original) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-6">
        <Card className="max-w-md p-8 text-center">
          <h1 className="display-font text-3xl text-[var(--brand-dark)]">Start with an assessment</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">Run an assessment before exploring a simulated scenario.</p>
          <Button href="/assessment" className="mt-6">Start assessment</Button>
        </Card>
      </main>
    );
  }

  const changed = editableFields.filter(([name]) => input[name] !== (() => {
    const originalInput = window.sessionStorage.getItem("credilens:last-input");
    return originalInput ? (JSON.parse(originalInput) as BorrowerInput)[name] : input[name];
  })());

  const update = (name: keyof BorrowerInput, value: string) => {
    setInput((current) => current && { ...current, [name]: value === "" ? null : Number(value) });
  };

  const runSimulation = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await simulateAssessment({ borrower_input: input } satisfies AssessmentRequest);
      setSimulated(result.assessment);
      window.sessionStorage.setItem("credilens:last-simulation", JSON.stringify(result));
    } catch {
      setError("The simulation could not be completed. Check the values and try again.");
    } finally {
      setLoading(false);
    }
  };

  const displayed = simulated ?? original;
  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-10 lg:px-10">
      <div className="mx-auto max-w-5xl">
        <Link href="/assessment/results" className="text-sm font-bold text-[var(--brand)]">← Back to results</Link>
        <div className="mt-10 max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">What-if simulator</p>
          <h1 className="display-font mt-4 text-5xl tracking-[-0.04em] text-[var(--brand-dark)]">Explore a scenario.</h1>
          <p className="mt-5 text-base leading-7 text-[var(--muted)]">
            Adjust a small set of user-editable inputs and rerun the same validated ensemble. The simulator does not estimate changes or promise an outcome.
          </p>
        </div>
        <div className="mt-10 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <Card className="p-8">
            <h2 className="display-font text-2xl text-[var(--brand-dark)]">Change inputs</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">Only plausible, non-sensitive model fields are editable here.</p>
            <div className="mt-7 space-y-5">
              {editableFields.map(([name, label, type]) => (
                <label key={name} className="block text-sm font-semibold text-[var(--brand-dark)]">
                  {label}
                  <input
                    type={type}
                    min="0"
                    step="0.01"
                    value={input[name] ?? ""}
                    onChange={(event) => update(name, event.target.value)}
                    className="mt-2 w-full rounded-xl border border-[var(--line)] bg-white px-3 py-3 font-normal outline-none focus:border-[var(--brand)] focus:ring-2 focus:ring-[#bfe4d4]"
                  />
                </label>
              ))}
            </div>
            {error && <p role="alert" className="mt-5 text-sm font-semibold text-red-700">{error}</p>}
            <Button type="button" onClick={runSimulation} disabled={loading} className="mt-7 w-full">
              {loading ? "Rerunning model…" : "Run simulated assessment →"}
            </Button>
            <p className="mt-4 text-xs leading-5 text-[var(--muted)]">Simulated result, not a guarantee or lending decision.</p>
          </Card>
          <div className="space-y-6">
            <Card className="p-8">
              <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Original vs simulated</p>
              <div className="mt-5 grid grid-cols-2 gap-4">
                {[["Original", original], ["Simulated", displayed]].map(([label, value]) => {
                  const assessment = value as AssessmentResponse;
                  return (
                    <div key={label as string} className="rounded-xl bg-[#f0f6f2] p-5">
                      <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">{label as string}</p>
                      <p className="display-font mt-3 text-4xl text-[var(--brand-dark)]">{(assessment.risk_probability * 100).toFixed(1)}%</p>
                      <p className="mt-2 text-sm font-bold capitalize text-[var(--brand)]">{assessment.risk_category} risk</p>
                    </div>
                  );
                })}
              </div>
              <p className="mt-5 text-sm leading-6 text-[var(--muted)]">
                {simulated ? "This comparison reflects a fresh model prediction using your changed inputs." : "Run the simulation to compare a fresh model result."}
              </p>
            </Card>
            <Card className="p-8">
              <h2 className="display-font text-2xl text-[var(--brand-dark)]">Changed inputs</h2>
              {changed.length ? (
                <ul className="mt-4 space-y-2 text-sm text-[var(--muted)]">
                  {changed.map(([name, label]) => <li key={name}>• {label}</li>)}
                </ul>
              ) : (
                <p className="mt-4 text-sm text-[var(--muted)]">No simulator values changed yet.</p>
              )}
              <p className="mt-6 border-t border-[var(--line)] pt-5 text-xs leading-5 text-[var(--muted)]">
                The underlying model, preprocessing, threshold, and artifact bundle are unchanged.
              </p>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
