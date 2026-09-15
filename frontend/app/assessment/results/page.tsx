"use client";

import Link from "next/link";
import { useId, useState } from "react";

import { ContributionChart } from "@/components/results/contribution-chart";
import { DownloadReportButton } from "@/components/results/download-report-button";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { BorrowerInput, ExplanationResponse } from "@/types/assessment";

const incomeFields = ["income_month_1", "income_month_2", "income_month_3", "income_month_4", "income_month_5", "income_month_6"] as const;
const borrowerTypeLabels: Record<string, string> = {
  gig: "Gig worker",
  migrant: "Migrant worker",
  rural: "Rural borrower",
};

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "Not provided";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function assessmentRecommendations(input: BorrowerInput) {
  const incomes = incomeFields.map((field) => input[field]).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const recommendations: string[] = [];
  if (incomes.length >= 2) {
    const average = incomes.reduce((sum, value) => sum + value, 0) / incomes.length;
    const variation = Math.max(...incomes) - Math.min(...incomes);
    if (average > 0 && variation / average > 0.25) {
      recommendations.push("Consider maintaining a larger emergency reserve to help manage months with lower reported income.");
    } else {
      recommendations.push("Continue keeping consistent income records so your financial profile remains easy to review.");
    }
  } else {
    recommendations.push("Add more monthly income records when available to make future assessments more informative.");
  }
  if (input.utility_bills_paid !== null && input.utility_bills_total !== null && input.utility_bills_total > 0 && input.utility_bills_paid < input.utility_bills_total) {
    recommendations.push("Review outstanding household bills and build a practical plan for keeping future payments on schedule.");
  }
  if (input.loan_amount_requested !== null && input.loan_amount_requested > 0) {
    recommendations.push("Before taking on additional obligations, compare the requested amount with your regular income and existing commitments.");
  }
  if (recommendations.length < 3) recommendations.push("Keep a record of timely payments and review existing obligations before adding new ones.");
  return recommendations.slice(0, 3);
}

export default function AssessmentResultsPage() {
  const reportIdToken = useId();
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
  const [borrowerMetadata] = useState(() => {
    if (typeof window === "undefined") return undefined;
    const stored = window.sessionStorage.getItem("credilens:borrower-metadata");
    return stored ? JSON.parse(stored) : undefined;
  });
  const [financialContext] = useState(() => {
    if (typeof window === "undefined") return undefined;
    const stored = window.sessionStorage.getItem("credilens:financial-context");
    return stored ? JSON.parse(stored) : undefined;
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
  const reportId = `CL-${reportIdToken.replace(/:/g, "").slice(-10).toUpperCase()}`;
  const probability = `${(assessment.risk_probability * 100).toFixed(1)}%`;
  const input = borrowerInput as BorrowerInput;
  const incomes = incomeFields.map((field) => input[field]).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const averageIncome = incomes.length ? incomes.reduce((sum, value) => sum + value, 0) / incomes.length : null;
  const incomeRange = incomes.length >= 2 ? Math.max(...incomes) - Math.min(...incomes) : null;
  const recommendations = assessmentRecommendations(input);
  const reliabilityColor =
    assessment.reliability.level === "high"
      ? "text-[var(--brand)]"
      : assessment.reliability.level === "medium"
        ? "text-amber-700"
        : "text-red-700";

  return (
    <main className="report-page min-h-screen px-4 py-5 sm:px-6 sm:py-8 lg:px-10 print:bg-white">
      <div className="report-shell mx-auto max-w-6xl">
        <header className="report-header">
          <Link href="/" className="report-brand" aria-label="CrediLens AI home"><span className="report-mark">C</span><span>CrediLens AI</span></Link>
          <div className="flex flex-wrap items-center justify-end gap-3 print:hidden">
            <Link href="/" className="report-action">← Back to Home</Link>
            <Link href="/assessment" className="report-action report-action-primary">Start New Assessment ↗</Link>
          </div>
        </header>
        <section className="report-intro">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="report-label">Alternative Credit Assessment Report</p>
              <h1 className="display-font mt-3 text-4xl tracking-[-0.04em] text-[#2456c7] sm:text-5xl">A signal, with context.</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--muted)]">This is an internal educational estimate from the received soft-voting ensemble, not an official credit score or lending decision.</p>
            </div>
            <div className="text-left text-xs text-[var(--muted)] sm:text-right">
              <p>Reference: <strong className="text-[var(--brand-dark)]">{reportId}</strong></p>
              <p className="mt-1">Assessment date: {new Date().toLocaleDateString("en-IN")}</p>
            </div>
          </div>
          <div className="report-borrower-strip mt-7">
            <div><p className="report-label">Borrower</p><p className="report-value">{borrowerMetadata?.full_name ?? "Not provided"}</p></div>
            <div><p className="report-label">Date of birth</p><p className="report-value">{borrowerMetadata?.date_of_birth ?? "Not provided"}</p></div>
            <div><p className="report-label">Borrower type</p><p className="report-value">{borrowerTypeLabels[input.borrower_type ?? ""] ?? input.borrower_type ?? "Not provided"}</p></div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
          <Card className="report-signal-card p-7 sm:p-8">
            <div className="report-card-lines" aria-hidden="true" />
            <div className="report-signal-top"><span className="report-signal-brand">CrediLens AI</span><span className="report-signal-label">ALTERNATIVE<br />FINANCIAL SIGNAL</span></div>
            <div className="report-chip" aria-hidden="true"><span /><span /><span /><span /></div>
            <p className="relative z-10 mt-5 text-sm text-blue-100">Alternative assessment signal</p>
            <div className="mt-3 flex items-end justify-between gap-4">
              <p className="relative z-10 display-font text-6xl text-white">{probability}</p>
              <p className="relative z-10 rounded-full bg-white/15 px-3 py-1 text-sm font-bold capitalize text-blue-50">
                {assessment.risk_category} risk
              </p>
            </div>
            <div className="relative z-10 mt-7 h-2 overflow-hidden rounded-full bg-white/25">
              <div
                className="h-full rounded-full bg-white transition-all"
                style={{ width: `${Math.max(3, assessment.risk_probability * 100)}%` }}
              />
            </div>
            <div className="relative z-10 mt-2 flex justify-between text-xs text-blue-100">
              <span>Lower risk</span><span>Model risk probability</span><span>Higher risk</span>
            </div>
            <p className="relative z-10 mt-5 text-sm leading-6 text-blue-50">The validated model estimates the probability associated with the returned risk category. This is not a standalone lending decision or a universal credit-score range.</p>
            <div className="relative z-10 mt-8 grid gap-4 border-t border-white/20 pt-6 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-blue-100">Primary model</p>
                <p className="mt-2 font-bold text-white">Soft-voting ensemble</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-blue-100">Predicted class</p>
                <p className="mt-2 font-bold text-white">{assessment.model_comparison.prediction.predicted_class}</p>
              </div>
            </div>
          </Card>

          <Card className="report-reliability-card p-7 sm:p-8">
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
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-1">
          <Card className="p-8">
            <p className="report-label">Financial overview</p>
            <h2 className="display-font mt-2 text-3xl text-[var(--brand-dark)]">Submitted financial picture</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="metric-card"><span>Average monthly income</span><strong>{formatCurrency(averageIncome)}</strong></div>
              <div className="metric-card"><span>Income months provided</span><strong>{incomes.length} of 6</strong></div>
              <div className="metric-card"><span>Loan amount requested</span><strong>{formatCurrency(input.loan_amount_requested)}</strong></div>
            </div>
            <div className="mt-6">
              <div className="flex items-end justify-between gap-3"><p className="text-sm font-bold text-[var(--brand-dark)]">Income history</p><p className="text-xs text-[var(--muted)]">{incomeRange === null ? "Add at least two months for a comparison" : `Range: ${formatCurrency(incomeRange)}`}</p></div>
              <div className="mt-4 grid grid-cols-6 items-end gap-2" aria-label="Monthly income history">
                {incomeFields.map((field, index) => {
                  const value = input[field];
                  const max = Math.max(...incomes, 1);
                  return <div key={field} className="text-center"><div className="flex h-28 items-end justify-center"><div className="w-full max-w-8 rounded-t-lg bg-[var(--brand)]" style={{ height: `${value === null || value === undefined ? 4 : Math.max(8, (value / max) * 100)}%` }} /></div><p className="mt-2 text-[10px] text-[var(--muted)]">M{index + 1}</p><p className="text-[10px] font-bold text-[var(--brand-dark)]">{value === null || value === undefined ? "—" : formatCurrency(value)}</p></div>;
                })}
              </div>
            </div>
          </Card>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
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
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <Card className="p-8">
            <p className="report-label">Additional Financial Context</p>
            <h2 className="display-font mt-2 text-3xl text-[var(--brand-dark)]">Your perspective</h2>
            <dl className="mt-6 space-y-4 text-sm">
              <div className="flex justify-between gap-4 border-b border-[var(--line)] pb-3"><dt className="text-[var(--muted)]">Emergency resilience</dt><dd className="text-right font-bold text-[var(--brand-dark)]">{financialContext?.emergency_financial_resilience ?? "Not provided"}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-[var(--muted)]">Repayment comfort</dt><dd className="font-bold text-[var(--brand-dark)]">{financialContext?.repayment_comfort ? `${financialContext.repayment_comfort} / 5` : "Not provided"}</dd></div>
            </dl>
            <p className="mt-6 text-xs leading-5 text-[var(--muted)]">These responses are self-reported supplementary context. They are not independently treated as verified facts or a lending decision.</p>
          </Card>
          <Card className="p-8">
            <p className="report-label">Executive summary</p>
            <h2 className="display-font mt-2 text-3xl text-[var(--brand-dark)]">What this means</h2>
            <p className="mt-5 text-sm leading-7 text-[var(--muted)]">{result.explanation}</p>
          </Card>
        </section>

        <Card className="mt-6 p-8">
          <h2 className="display-font text-3xl text-[var(--brand-dark)]">Recommended next steps</h2>
          <p className="mt-3 text-sm text-[var(--muted)]">Practical, conditional observations based only on the submitted information.</p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
          {recommendations.map((suggestion, index) => (
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
              borrowerMetadata={borrowerMetadata}
              financialContext={financialContext}
              simulator={simulator}
            />
            <Button type="button" variant="outline" onClick={() => window.print()}>Print report</Button>
            <Button href="/simulator" variant="outline">Explore a what-if scenario</Button>
            <Button href="/assessment" variant="outline">Start another assessment</Button>
          </div>
        </div>
        <footer className="report-footer">
          <span>CrediLens AI · Built for clearer financial understanding</span>
          <span>Made with ♥ by AI &amp; DS Final Year Team (Prophetic Programmers)</span>
        </footer>
        <p className="border-t border-[var(--line)] pb-4 pt-6 text-xs leading-5 text-[var(--muted)]">Responsible AI notice: This report is an assessment aid based on the information provided, not a guaranteed lending decision or a substitute for a lender&apos;s complete evaluation. Full Name and Date of Birth are report metadata only and are not used as ML prediction features. Self-reported information may require independent verification.</p>
      </div>
    </main>
  );
}
