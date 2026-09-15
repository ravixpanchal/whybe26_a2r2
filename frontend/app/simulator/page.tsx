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
      <main className="simulator-page flex min-h-screen items-center justify-center px-6">
        <Card className="simulator-card max-w-md p-8 text-center">
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
    <main className="simulator-page min-h-screen px-4 py-6 sm:px-6 sm:py-10 lg:px-10">
      <div className="simulator-shell mx-auto max-w-5xl">
        <header className="simulator-header">
          <Link href="/" className="simulator-brand" aria-label="CrediLens AI home">
            <span className="simulator-mark">C</span>
            <span>CrediLens AI</span>
          </Link>
          <Link href="/assessment" className="simulator-header-action">Start New Assessment ↗</Link>
        </header>
        <div className="simulator-intro">
          <Link href="/assessment/results" className="simulator-back-link">← Back to results</Link>
          <p className="simulator-eyebrow">What-if simulator</p>
          <h1>Explore a scenario.</h1>
          <p>
            Adjust a small set of user-editable inputs and rerun the same validated ensemble. The simulator does not estimate changes or promise an outcome.
          </p>
        </div>
        <div className="simulator-grid">
          <Card className="simulator-card simulator-input-card p-8">
            <h2>Change inputs</h2>
            <p className="simulator-card-description">Only plausible, non-sensitive model fields are editable here.</p>
            <div className="simulator-fields">
              {editableFields.map(([name, label, type]) => (
                <label key={name} className="simulator-field">
                  {label}
                  <input
                    type={type}
                    min="0"
                    step="0.01"
                    value={input[name] ?? ""}
                    onChange={(event) => update(name, event.target.value)}
                    className="simulator-input"
                  />
                </label>
              ))}
            </div>
            {error && <p role="alert" className="simulator-error">{error}</p>}
            <Button type="button" onClick={runSimulation} disabled={loading} className="simulator-run-button mt-7 w-full">
              {loading ? "Rerunning model…" : "Run simulated assessment →"}
            </Button>
            <p className="simulator-note">Simulated result, not a guarantee or lending decision.</p>
          </Card>
          <div className="space-y-6">
            <Card className="simulator-card simulator-comparison-card p-8">
              <p className="simulator-section-label">Original vs simulated</p>
              <div className="simulator-signal-card">
                <div className="simulator-card-lines" aria-hidden="true" />
                <div className="simulator-signal-top">
                  <span>CrediLens AI</span>
                  <small>INSIGHTS FOR A<br />BRIGHTER TOMORROW</small>
                </div>
                <div className="simulator-chip" aria-hidden="true"><span /><span /><span /><span /></div>
                <div className="simulator-results">
                {[["Original", original], ["Simulated", displayed]].map(([label, value]) => {
                  const assessment = value as AssessmentResponse;
                  return (
                    <div key={label as string} className="simulator-result">
                      <p>{label as string}</p>
                      <strong>{(assessment.risk_probability * 100).toFixed(1)}%</strong>
                      <span>{assessment.risk_category} risk</span>
                    </div>
                  );
                })}
                </div>
              </div>
              <p className="simulator-comparison-note">
                {simulated ? "This comparison reflects a fresh model prediction using your changed inputs." : "Run the simulation to compare a fresh model result."}
              </p>
            </Card>
            <Card className="simulator-card simulator-changed-card p-8">
              <h2>Changed inputs</h2>
              {changed.length ? (
                <ul className="simulator-changed-list">
                  {changed.map(([name, label]) => <li key={name}>• {label}</li>)}
                </ul>
              ) : (
                <p className="simulator-empty">No simulator values changed yet.</p>
              )}
              <p className="simulator-changed-note">
                The underlying model, preprocessing, threshold, and artifact bundle are unchanged.
              </p>
            </Card>
          </div>
        </div>
        <footer className="simulator-footer">
          <span>CrediLens AI · Built for clearer financial understanding</span>
          <span>Made with ♥ by AI &amp; DS Final Year Team (Prophetic Programmers)</span>
        </footer>
      </div>
    </main>
  );
}
