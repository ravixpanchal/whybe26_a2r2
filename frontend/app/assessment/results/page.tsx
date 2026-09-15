"use client";

import Link from "next/link";
import { useState } from "react";

import { ContributionChart } from "@/components/results/contribution-chart";
import { DownloadReportButton } from "@/components/results/download-report-button";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { ExplanationResponse } from "@/types/assessment";

const suggestions = [
  "Keep your income and employment information current when you review your financial profile.",
  "Build a consistent record of on-time household and rental payments where possible.",
  "Use this assessment as a conversation starter with a qualified financial professional.",
];

export default function AssessmentResultsPage() {
  const [result] = useState<ExplanationResponse | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = window.sessionStorage.getItem("credilens:last-explanation");
    if (stored) return JSON.parse(stored) as ExplanationResponse;
    const assessment = window.sessionStorage.getItem("credilens:last-assessment");
    return assessment
      ? {
          assessment: JSON.parse(assessment),
          explanation:
            "Your validated assessment is ready. Review the factors and reliability information below.",
          explanation_source: "fallback",
          disclaimer: "This is an educational model explanation, not a loan decision.",
        }
      : null;
  });
  const [simulator] = useState(() => {
    if (typeof window === "undefined") return undefined;
    const stored = window.sessionStorage.getItem("credilens:last-simulation");
    return stored ? JSON.parse(stored) : undefined;
  });
  const [borrowerInput] = useState(() => {
    if (typeof window === "undefined") return {};
    const stored = window.sessionStorage.getItem("credilens:last-input");
    return stored ? JSON.parse(stored) : {};
  });

  if (!result) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-6">
        <Card className="max-w-md p-8 text-center">
          <h1 className="display-font text-3xl text-[var(--brand-dark)]">No assessment found</h1>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
            Start a new assessment to see your result.
          </p>
          <Button href="/assessment" className="mt-6">Start assessment</Button>
        </Card>
      </main>
    );
  }

  const assessment = result.assessment;
  const probability = `${(assessment.risk_probability * 100).toFixed(1)}%`;
  const reliabilityColor =
    assessment.reliability.level === "high"
      ? "text-[var(--brand)]"
      : assessment.reliability.level === "medium"
        ? "text-amber-700"
        : "text-red-700";

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-10 lg:px-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link href="/" className="text-sm font-bold text-[var(--brand)]">← CrediLens home</Link>
          <span className="rounded-full bg-[#e0f1e8] px-3 py-1 text-xs font-bold text-[var(--brand)]">
            Validated ensemble
          </span>
        </div>
        <div className="mt-10 max-w-3xl">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">Assessment result</p>
          <h1 className="display-font mt-4 text-5xl tracking-[-0.04em] text-[var(--brand-dark)]">
            A signal, with context.
          </h1>
          <p className="mt-5 text-base leading-7 text-[var(--muted)]">
            This is an internal educational estimate from the received soft-voting ensemble, not an official credit score or lending decision.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-[1fr_1.15fr]">
          <Card className="p-8">
            <p className="text-sm text-[var(--muted)]">Default-risk probability</p>
            <div className="mt-3 flex items-end justify-between gap-4">
              <p className="display-font text-6xl text-[var(--brand-dark)]">{probability}</p>
              <p className="rounded-full bg-[#e0f1e8] px-3 py-1 text-sm font-bold capitalize text-[var(--brand)]">
                {assessment.risk_category} risk
              </p>
            </div>
            <div className="mt-7 h-3 overflow-hidden rounded-full bg-[#e4eee9]">
              <div
                className="h-full rounded-full bg-[var(--brand)] transition-all"
                style={{ width: `${Math.max(3, assessment.risk_probability * 100)}%` }}
              />
            </div>
            <div className="mt-2 flex justify-between text-xs text-[var(--muted)]">
              <span>Lower risk</span><span>Validated threshold: 59%</span><span>Higher risk</span>
            </div>
            <div className="mt-8 grid gap-4 border-t border-[var(--line)] pt-6 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Primary model</p>
                <p className="mt-2 font-bold text-[var(--brand-dark)]">Soft-voting ensemble</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Predicted class</p>
                <p className="mt-2 font-bold text-[var(--brand-dark)]">{assessment.model_comparison.prediction.predicted_class}</p>
              </div>
            </div>
          </Card>

          <Card className="p-8">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Reliability indicator</p>
                <h2 className={`display-font mt-2 text-3xl capitalize ${reliabilityColor}`}>
                  {assessment.reliability.level}
                </h2>
              </div>
              <div className="text-right">
                <p className="display-font text-4xl text-[var(--brand-dark)]">{assessment.reliability.score}</p>
                <p className="text-xs text-[var(--muted)]">heuristic score / 100</p>
              </div>
            </div>
            <p className="mt-5 text-sm leading-6 text-[var(--muted)]">{assessment.reliability.disclaimer}</p>
            <ul className="mt-5 space-y-2 text-sm text-[var(--muted)]">
              {assessment.reliability.reasons.map((reason) => <li key={reason}>• {reason}</li>)}
            </ul>
            <div className="mt-6 rounded-xl bg-[#f0f6f2] p-4 text-xs leading-5 text-[var(--muted)]">
              Compatibility status: <strong className="text-[var(--brand-dark)]">{assessment.model_comparison.compatibility_status}</strong>.
              Component agreement is shown only when exposed by the validated artifact.
            </div>
          </Card>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
          <Card className="p-8">
            <h2 className="display-font text-3xl text-[var(--brand-dark)]">What shaped the result</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              Directional model contributions, mapped back to the original feature names. They describe model behavior, not cause and effect.
            </p>
            <div className="mt-6">
              <ContributionChart contributions={assessment.feature_contributions} />
            </div>
            <div className="mt-4 flex flex-wrap gap-4 text-xs text-[var(--muted)]">
              <span><b className="text-[var(--brand)]">■</b> Risk-reducing contribution</span>
              <span><b className="text-amber-700">■</b> Risk-increasing contribution</span>
            </div>
          </Card>

          <Card className="p-8">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">
              Plain-language explanation · {result.explanation_source}
            </p>
            <h2 className="display-font mt-3 text-3xl text-[var(--brand-dark)]">In brief</h2>
            <p className="mt-5 text-sm leading-7 text-[var(--muted)]">{result.explanation}</p>
            <p className="mt-6 border-t border-[var(--line)] pt-5 text-xs leading-5 text-[var(--muted)]">{result.disclaimer}</p>
          </Card>
        </div>

        <Card className="mt-6 p-8">
          <h2 className="display-font text-3xl text-[var(--brand-dark)]">Educational next steps</h2>
          <p className="mt-3 text-sm text-[var(--muted)]">General suggestions only — not personalized financial advice.</p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {suggestions.map((suggestion, index) => (
              <div key={suggestion} className="rounded-xl bg-[#f0f6f2] p-5">
                <span className="text-sm font-bold text-[var(--brand)]">0{index + 1}</span>
                <p className="mt-4 text-sm leading-6 text-[var(--muted)]">{suggestion}</p>
              </div>
            ))}
          </div>
        </Card>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-[var(--line)] py-6">
          <p className="max-w-2xl text-xs leading-5 text-[var(--muted)]">
            CrediLens is for education and preparation only. This assessment is not an official credit decision, loan approval, rejection, or guarantee.
          </p>
          <div className="flex flex-wrap gap-3">
            <DownloadReportButton
              explanation={result}
              borrowerInput={borrowerInput}
              simulator={simulator}
            />
            <Button href="/simulator" variant="outline">Explore a what-if scenario</Button>
            <Button href="/assessment" variant="outline">Start another assessment</Button>
          </div>
        </div>
      </div>
    </main>
  );
}
