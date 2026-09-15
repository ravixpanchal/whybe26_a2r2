"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm, useWatch, type FieldErrors } from "react-hook-form";
import { z } from "zod";

import { Field } from "@/components/forms/field";
import { LivingIdentityCard } from "@/components/assessment/living-identity-card";
import { Button } from "@/components/ui/button";
import { requestExplanation } from "@/lib/api";
import type { AssessmentRequest, BorrowerInput, FinancialContext } from "@/types/assessment";

const optionalNumber = (minimum?: number, maximum?: number) =>
  z.preprocess(
    (value) => (value === "" || (typeof value === "number" && Number.isNaN(value)) ? null : value),
    z.number().finite().min(minimum ?? -Infinity).max(maximum ?? Infinity).nullable(),
  );
const optionalInteger = (minimum?: number, maximum?: number) =>
  z.preprocess(
    (value) => (value === "" || (typeof value === "number" && Number.isNaN(value)) ? null : value),
    z.number().finite().int("Enter a whole number.").min(minimum ?? -Infinity).max(maximum ?? Infinity).nullable(),
  );
const borrowerSchema = z
  .object({
    borrower_type: z.preprocess((value) => (value === "" ? null : value), z.enum(["gig", "migrant", "rural"]).nullable()),
    household_size: optionalInteger(0),
    income_month_1: optionalNumber(0),
    income_month_2: optionalNumber(0),
    income_month_3: optionalNumber(0),
    income_month_4: optionalNumber(0),
    income_month_5: optionalNumber(0),
    income_month_6: optionalNumber(0),
    employment_type: z.preprocess((value) => (value === "" ? null : value), z.enum(["daily-wage", "salaried-gig", "seasonal", "self-employed"]).nullable()),
    months_at_current_job: optionalInteger(0),
    num_income_sources: optionalInteger(0),
    upi_transactions_per_month: optionalNumber(0),
    upi_avg_transaction_amount: optionalNumber(0),
    upi_months_active: optionalInteger(0),
    mobile_wallet_used: optionalInteger(0, 1),
    utility_bills_paid: optionalInteger(0),
    utility_bills_total: optionalInteger(0),
    rent_paid_on_time_months: optionalInteger(0),
    total_rental_months: optionalInteger(0),
    same_number_since_year: optionalInteger(1900, 2100),
    avg_monthly_recharge_amount: optionalNumber(0),
    recharge_frequency_per_month: optionalNumber(0),
    ecomm_orders_per_month: optionalNumber(0),
    ecomm_return_rate: optionalNumber(0, 1),
    prepaid_orders_ratio: optionalNumber(0, 1),
    survey_q1: optionalInteger(1, 5),
    survey_q2: optionalInteger(1, 5),
    survey_q3: optionalInteger(1, 5),
    survey_q4: optionalInteger(1, 5),
    survey_q5: optionalInteger(1, 5),
    survey_q6: optionalInteger(1, 5),
    survey_q7: optionalInteger(1, 5),
    survey_q8: optionalInteger(1, 5),
    loan_amount_requested: optionalNumber(0),
    loan_purpose: z.preprocess((value) => (value === "" ? null : value), z.enum(["agriculture", "business", "consumption", "education", "medical"]).nullable()),
    loan_tenure_months: optionalInteger(0),
  })
  .superRefine((value, context) => {
    if (
      value.utility_bills_paid !== null &&
      value.utility_bills_total !== null &&
      value.utility_bills_paid > value.utility_bills_total
    ) {
      context.addIssue({ code: "custom", path: ["utility_bills_paid"], message: "Cannot exceed total bills." });
    }
    if (
      value.rent_paid_on_time_months !== null &&
      value.total_rental_months !== null &&
      value.rent_paid_on_time_months > value.total_rental_months
    ) {
      context.addIssue({ code: "custom", path: ["rent_paid_on_time_months"], message: "Cannot exceed total rental months." });
    }
    if (
      value.num_income_sources === 0 &&
      [value.income_month_1, value.income_month_2, value.income_month_3, value.income_month_4, value.income_month_5, value.income_month_6].some(
        (income) => income !== null && income > 0,
      )
    ) {
      context.addIssue({ code: "custom", path: ["num_income_sources"], message: "Positive income requires an income source." });
    }
  });

type FormValues = z.input<typeof borrowerSchema>;
type SelectionName = keyof FormValues | "emergency_financial_resilience" | "repayment_comfort";

const defaults: FormValues = {
  borrower_type: "", household_size: "", income_month_1: "", income_month_2: "", income_month_3: "",
  income_month_4: "", income_month_5: "", income_month_6: "", employment_type: "", months_at_current_job: "",
  num_income_sources: "", upi_transactions_per_month: "", upi_avg_transaction_amount: "", upi_months_active: "",
  mobile_wallet_used: "", utility_bills_paid: "", utility_bills_total: "", rent_paid_on_time_months: "",
  total_rental_months: "", same_number_since_year: "", avg_monthly_recharge_amount: "",
  recharge_frequency_per_month: "", ecomm_orders_per_month: "", ecomm_return_rate: "", prepaid_orders_ratio: "",
  survey_q1: "", survey_q2: "", survey_q3: "", survey_q4: "", survey_q5: "", survey_q6: "", survey_q7: "",
  survey_q8: "", loan_amount_requested: "", loan_purpose: "", loan_tenure_months: "",
};

const numericFields = [
  ["household_size", "Household size", "People in the household"],
  ["months_at_current_job", "Months at current job", "Whole months"],
  ["num_income_sources", "Income sources", "Number of current income sources"],
  ["upi_transactions_per_month", "UPI transactions per month", "Average monthly count"],
  ["upi_avg_transaction_amount", "Average UPI transaction", "Amount in local currency"],
  ["upi_months_active", "UPI months active", "Months with activity"],
  ["mobile_wallet_used", "Mobile wallet used", "0 for no, 1 for yes"],
  ["utility_bills_paid", "Utility bills paid", "Bills paid on time"],
  ["utility_bills_total", "Utility bills total", "Bills in the period"],
  ["rent_paid_on_time_months", "Rent paid on time", "Months"],
  ["total_rental_months", "Total rental months", "Months"],
  ["same_number_since_year", "Same number since year", "Year"],
  ["avg_monthly_recharge_amount", "Average monthly recharge", "Amount in local currency"],
  ["recharge_frequency_per_month", "Recharge frequency", "Times per month"],
  ["ecomm_orders_per_month", "E-commerce orders", "Orders per month"],
  ["ecomm_return_rate", "E-commerce return rate", "Decimal from 0 to 1"],
  ["prepaid_orders_ratio", "Prepaid orders ratio", "Decimal from 0 to 1"],
  ["loan_amount_requested", "Loan amount requested", "Amount in local currency"],
  ["loan_tenure_months", "Loan tenure", "Months"],
] as const;

type FieldSpec = {
  name: keyof FormValues | "emergency_financial_resilience" | "repayment_comfort";
  label: string;
  description: string;
  explanation: string;
  group: string;
  kind: "number" | "select" | "context";
  options?: { label: string; value: string }[];
  step?: string;
  contextStep?: 1 | 2;
};

const integerFieldNames = new Set<keyof FormValues>([
  "household_size",
  "months_at_current_job",
  "num_income_sources",
  "upi_months_active",
  "mobile_wallet_used",
  "utility_bills_paid",
  "utility_bills_total",
  "rent_paid_on_time_months",
  "total_rental_months",
  "same_number_since_year",
  "survey_q1",
  "survey_q2",
  "survey_q3",
  "survey_q4",
  "survey_q5",
  "survey_q6",
  "survey_q7",
  "survey_q8",
  "loan_tenure_months",
]);

function numericConstraint(name: keyof FormValues) {
  if (name === "mobile_wallet_used") return { min: 0, max: 1 };
  if (name === "same_number_since_year") return { min: 1900, max: 2100 };
  if (name.startsWith("survey_q")) return { min: 1, max: 5 };
  if (name === "ecomm_return_rate" || name === "prepaid_orders_ratio") return { min: 0, max: 1 };
  return { min: 0 };
}

const fieldCatalog: FieldSpec[] = [
  {
    name: "borrower_type",
    label: "Borrower type",
    description: "The broad borrower profile that best describes you.",
    explanation: "This helps the model compare your context with similar borrower profiles. Choose the closest available option.",
    group: "Profile",
    kind: "select",
    options: [
      { label: "Gig worker", value: "gig" },
      { label: "Migrant worker", value: "migrant" },
      { label: "Rural borrower", value: "rural" },
    ],
  },
  ...numericFields.slice(0, 3).map(([name, label, description]) => ({
    name,
    label,
    description,
    explanation: `This records ${description.toLowerCase()} so the assessment can interpret your household and employment context.`,
    group: "Profile",
    kind: "number" as const,
  })),
  {
    name: "employment_type",
    label: "Employment type",
    description: "The work arrangement that best matches your current situation.",
    explanation: "Employment structure provides context for income consistency and how your financial profile may be interpreted.",
    group: "Profile",
    kind: "select",
    options: [
      { label: "Daily wage", value: "daily-wage" },
      { label: "Salaried gig", value: "salaried-gig" },
      { label: "Seasonal", value: "seasonal" },
      { label: "Self-employed", value: "self-employed" },
    ],
  },
  ...Array.from({ length: 6 }, (_, index) => ({
    name: `income_month_${index + 1}` as keyof FormValues,
    label: `Income month ${index + 1}`,
    description: "Monthly income amount",
    explanation: "Recent income history helps show how steady your reported earnings are across several months.",
    group: "Income",
    kind: "number" as const,
    step: "0.01",
  })),
  ...numericFields.slice(3, 17).map(([name, label, description]) => ({
    name,
    label,
    description,
    explanation: `This captures ${description.toLowerCase()} as part of your everyday financial activity.`,
    group: "Activity",
    kind: "number" as const,
    step: "0.01",
  })),
  {
    name: "emergency_financial_resilience",
    label: "Emergency financial resilience",
    description: "If an unexpected expense occurred this month, how would you manage it?",
    explanation: "This is supplementary self-reported context about how you would respond to an unexpected expense. It is not used as an ML feature.",
    group: "Financial context",
    kind: "context",
    contextStep: 1,
  },
  {
    name: "repayment_comfort",
    label: "Repayment comfort",
    description: "How comfortable are you with your current monthly repayment obligations?",
    explanation: "This self-reported context helps personalize your report, but it does not independently approve or reject a borrower.",
    group: "Financial context",
    kind: "context",
    contextStep: 2,
  },
  {
    name: "loan_amount_requested",
    label: "Loan amount requested",
    description: "Amount in local currency",
    explanation: "The requested amount gives the assessment context about the scale of the borrowing need.",
    group: "Loan",
    kind: "number",
    step: "0.01",
  },
  {
    name: "loan_purpose",
    label: "Loan purpose",
    description: "The primary reason for the requested loan",
    explanation: "Purpose provides context for how you intend to use the requested funds.",
    group: "Loan",
    kind: "select",
    options: [
      { label: "Agriculture", value: "agriculture" },
      { label: "Business", value: "business" },
      { label: "Consumption", value: "consumption" },
      { label: "Education", value: "education" },
      { label: "Medical", value: "medical" },
    ],
  },
  {
    name: "loan_tenure_months",
    label: "Loan tenure",
    description: "Requested repayment period in months",
    explanation: "Repayment duration helps describe the shape of the borrowing request alongside the amount.",
    group: "Loan",
    kind: "number",
    step: "0.01",
  },
];

function inputClass(hasError: boolean) {
  return `w-full rounded-2xl border bg-white px-4 py-3.5 text-sm text-[var(--brand-dark)] outline-none transition focus:border-[#536fe8] focus:ring-4 focus:ring-[#dfe5ff] ${hasError ? "border-red-400" : "border-[#d9def3]"}`;
}

const emergencyOptions = [
  "I would use emergency savings.",
  "I would use regular savings.",
  "I would borrow from family or friends.",
  "I would use a credit facility or loan.",
  "I would struggle to manage it.",
  "Prefer not to say.",
];

export default function AssessmentPage() {
  const router = useRouter();
  const [selectedField, setSelectedField] = useState<SelectionName>("borrower_type");
  const [fullName, setFullName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [identityError, setIdentityError] = useState("");
  const [financialContext, setFinancialContext] = useState<FinancialContext>({
    emergency_financial_resilience: null,
    repayment_comfort: null,
  });
  const { register, handleSubmit, setError, control, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(borrowerSchema),
    defaultValues: defaults,
  });
  const watchedValues = useWatch({ control });

  const onSubmit = async (values: FormValues) => {
    if (!fullName.trim()) {
      setIdentityError("Please enter your full name.");
      return;
    }
    if (!dateOfBirth) {
      setIdentityError("Please enter your date of birth.");
      return;
    }
    if (dateOfBirth > new Date().toISOString().slice(0, 10)) {
      setIdentityError("Date of birth cannot be in the future.");
      return;
    }
    setIdentityError("");
    const parsed = borrowerSchema.parse(values);
    try {
      const result = await requestExplanation({ borrower_input: parsed as BorrowerInput } satisfies AssessmentRequest);
      sessionStorage.setItem("credilens:last-explanation", JSON.stringify(result));
      sessionStorage.setItem("credilens:last-assessment", JSON.stringify(result.assessment));
      sessionStorage.setItem("credilens:last-input", JSON.stringify(parsed));
      sessionStorage.setItem("credilens:borrower-metadata", JSON.stringify({
        full_name: fullName.trim(),
        date_of_birth: dateOfBirth,
      }));
      sessionStorage.setItem("credilens:financial-context", JSON.stringify(financialContext));
      router.push("/assessment/results");
    } catch {
      setError("root", { message: "We could not reach the assessment service. Please try again." });
    }
  };

  const onInvalid = (formErrors: FieldErrors<FormValues>) => {
    const firstInvalidField = Object.keys(formErrors)[0] as keyof FormValues | undefined;
    if (firstInvalidField) {
      setSelectedField(firstInvalidField);
    }
    setError("root", {
      message: "Please review the highlighted field before generating your assessment.",
    });
  };

  const activeField = fieldCatalog.find((field) => field.name === selectedField) ?? fieldCatalog[0];
  const isContextField = activeField.kind === "context";
  const contextNumber = activeField.contextStep ?? null;
  const activeError = isContextField
    ? undefined
    : errors[activeField.name as keyof FormValues]?.message as string | undefined;
  const previousContext = contextNumber === 2 ? "emergency_financial_resilience" : null;
  const nextContext = contextNumber === 1 ? "repayment_comfort" : null;

  return (
    <main className="min-h-screen bg-[#e9edff] px-4 py-6 sm:px-6 sm:py-10 lg:px-10">
      <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] border border-[#cbd5f4] bg-[#fbfcff] shadow-[0_30px_90px_rgba(50,72,150,0.14)]">
        <div className="flex items-center justify-between border-b border-[#e2e6f7] px-6 py-5 sm:px-10">
          <Link href="/" className="flex items-center gap-3 text-sm font-bold tracking-[0.14em] text-[#3157c8]">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#3157c8] text-white">C</span>
            CREDILENS
          </Link>
          <span className="rounded-full border border-[#c8d2f4] bg-[#eef1ff] px-4 py-2 text-xs font-bold text-[#3157c8]">{fieldCatalog.length}-field assessment</span>
        </div>

        <div className="px-6 pb-8 pt-8 sm:px-10 sm:pb-12 sm:pt-10">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-[#536fe8]">Borrower assessment</p>
            <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em] text-[#1d2b68] sm:text-6xl">Bring your context.</h1>
            <p className="mt-4 text-base leading-7 text-[#66719b]">
              Select a field to enter your information and understand why it matters to the assessment.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit, onInvalid)} className="mt-9" noValidate>
            <section className="mb-6 rounded-[1.5rem] border border-[#cbd5f4] bg-white p-6 sm:p-8">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#536fe8]">Let&apos;s get started</p>
              <h2 className="mt-3 text-2xl font-bold tracking-[-0.03em] text-[#1d2b68]">Personalize your report</h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-[#66719b]">Enter your basic details before completing the assessment. These details are used for borrower identification in your report only.</p>
              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                <label className="block text-sm font-bold text-[#34406e]" htmlFor="full-name">
                  Full name
                  <input id="full-name" type="text" value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="name" className={`${inputClass(Boolean(identityError) && !fullName.trim())} mt-2`} placeholder="Enter your full name" />
                </label>
                <label className="block text-sm font-bold text-[#34406e]" htmlFor="date-of-birth">
                  Date of birth
                  <input id="date-of-birth" type="date" value={dateOfBirth} onChange={(event) => setDateOfBirth(event.target.value)} max={new Date().toISOString().slice(0, 10)} autoComplete="bday" className={`${inputClass(Boolean(identityError) && !dateOfBirth)} mt-2`} />
                </label>
              </div>
              <p className="mt-4 text-xs leading-5 text-[#7b85a7]">Your name and date of birth are not used as ML prediction features.</p>
              {identityError && <p role="alert" className="mt-3 text-sm font-semibold text-[#b54855]">{identityError}</p>}
            </section>
            <div className="grid gap-6 lg:grid-cols-[minmax(210px,0.7fr)_minmax(0,1.25fr)_minmax(290px,0.85fr)]">
              <aside className="rounded-[1.5rem] border border-[#dce2f6] bg-[#f5f7ff] p-3">
                <div className="flex items-center justify-between px-3 pb-3 pt-2">
                  <div>
                    <p className="text-sm font-bold text-[#1d2b68]">Your information</p>
                    <p className="mt-1 text-xs text-[#7882a6]">Choose a field to continue</p>
                  </div>
                  <span className="text-xs font-bold text-[#536fe8]">{fieldCatalog.length}</span>
                </div>
                <div className="max-h-[25rem] space-y-2 overflow-y-auto pr-1" aria-label="Assessment fields">
                  {fieldCatalog.map((field, index) => {
                    const isActive = field.name === activeField.name;
                    const hasError = Boolean(errors[field.name as keyof FormValues]);
                    return (
                      <button
                        key={field.name}
                        type="button"
                        onClick={() => setSelectedField(field.name)}
                        className={`group flex w-full items-center gap-3 rounded-2xl border px-3 py-3 text-left transition ${
                          isActive
                            ? "border-[#7890ee] bg-[#dfe5ff] shadow-[0_8px_20px_rgba(83,111,232,0.12)]"
                            : "border-transparent bg-white hover:border-[#cbd5f4] hover:bg-[#eef1ff]"
                        }`}
                        aria-current={isActive ? "step" : undefined}
                      >
                        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${isActive ? "bg-[#536fe8] text-white" : "bg-[#edf0fb] text-[#7b86ae]"}`}>
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className={`block truncate text-sm font-bold ${isActive ? "text-[#2944a6]" : "text-[#34406e]"}`}>{field.label}</span>
                          <span className="mt-0.5 block text-[11px] font-medium text-[#8a93b2]">{field.group}</span>
                        </span>
                        {hasError && <span className="h-2 w-2 rounded-full bg-[#d85b64]" aria-label="Needs attention" />}
                        <span className={`text-lg ${isActive ? "text-[#536fe8]" : "text-[#b1b9d1]"}`} aria-hidden="true">›</span>
                      </button>
                    );
                  })}
                </div>
              </aside>

              <section className="relative overflow-hidden rounded-[1.5rem] border border-[#cbd5f4] bg-gradient-to-br from-[#e8edff] via-[#f7f8ff] to-white p-6 sm:p-10">
                <div className="absolute -right-16 -top-20 h-56 w-56 rounded-full bg-[#dce4ff] blur-3xl" aria-hidden="true" />
                <div key={activeField.name} className="relative animate-[fade-in_220ms_ease-out]">
                  <div className="flex items-start justify-between gap-5">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#536fe8]">{activeField.group}</p>
                      <h2 className="mt-3 text-3xl font-bold tracking-[-0.035em] text-[#1d2b68]">{activeField.label}</h2>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className="hidden rounded-full bg-white/80 px-3 py-1.5 text-xs font-bold text-[#7180b5] sm:block">Field {String(fieldCatalog.indexOf(activeField) + 1).padStart(2, "0")} / {fieldCatalog.length}</span>
                      {isContextField && <span className="rounded-full bg-[#536fe8] px-3 py-1.5 text-xs font-bold text-white">Question {contextNumber} of 2</span>}
                    </div>
                  </div>
                  <p className="mt-5 max-w-xl text-sm leading-7 text-[#66719b]">{activeField.explanation}</p>
                  <div className="mt-8 max-w-md">
                    <Field id={activeField.name} label={activeField.description} error={activeError}>
                      {isContextField && activeField.contextStep === 1 ? (
                        <div className="space-y-2" role="radiogroup" aria-label="Emergency financial resilience">
                          {emergencyOptions.map((option) => (
                            <label key={option} className="flex cursor-pointer items-center gap-3 rounded-2xl border border-[#d9def3] bg-white px-4 py-3 text-sm font-semibold text-[#536189] transition has-[:checked]:border-[#536fe8] has-[:checked]:bg-[#dfe5ff]">
                              <input
                                type="radio"
                                name="emergency_financial_resilience"
                                value={option}
                                checked={financialContext.emergency_financial_resilience === option}
                                onChange={() => setFinancialContext((current) => ({ ...current, emergency_financial_resilience: option }))}
                                className="h-4 w-4 accent-[#536fe8]"
                              />
                              {option}
                            </label>
                          ))}
                          <p className="mt-4 text-xs leading-5 text-[#7b85a7]">Optional — you can skip this question.</p>
                        </div>
                      ) : isContextField && activeField.contextStep === 2 ? (
                        <div>
                          <div className="grid grid-cols-5 gap-2" role="radiogroup" aria-label="Repayment comfort">
                            {[1, 2, 3, 4, 5].map((rating) => (
                              <label key={rating} className="cursor-pointer">
                                <input type="radio" value={rating} checked={financialContext.repayment_comfort === rating} onChange={() => setFinancialContext((current) => ({ ...current, repayment_comfort: rating }))} className="peer sr-only" />
                                <span className="flex h-12 items-center justify-center rounded-2xl border border-[#d9def3] bg-white text-sm font-bold text-[#536189] transition peer-checked:border-[#536fe8] peer-checked:bg-[#536fe8] peer-checked:text-white peer-focus-visible:ring-4 peer-focus-visible:ring-[#dfe5ff]">
                                  {rating}
                                </span>
                              </label>
                            ))}
                          </div>
                          <div className="mt-3 grid grid-cols-5 text-center text-[11px] font-semibold text-[#7b85a7]">
                            <span>Very uncomfortable</span><span>Uncomfortable</span><span>Neutral</span><span>Comfortable</span><span>Very comfortable</span>
                          </div>
                          <p className="mt-4 text-xs leading-5 text-[#7b85a7]">Optional — you can skip this question.</p>
                        </div>
                      ) : activeField.kind === "select" ? (
                        <select id={activeField.name} className={inputClass(Boolean(activeError))} {...register(activeField.name as keyof FormValues)} aria-describedby={activeError ? `${activeField.name}-error` : undefined}>
                          <option value="">Select one</option>
                          {activeField.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                        </select>
                      ) : (
                        <input
                          id={activeField.name}
                          type="number"
                          step={integerFieldNames.has(activeField.name as keyof FormValues) ? "1" : activeField.step}
                          min={numericConstraint(activeField.name as keyof FormValues).min}
                          max={numericConstraint(activeField.name as keyof FormValues).max}
                          inputMode={integerFieldNames.has(activeField.name as keyof FormValues) ? "numeric" : "decimal"}
                          className={inputClass(Boolean(activeError))}
                          {...register(activeField.name as keyof FormValues, { valueAsNumber: true })}
                          aria-describedby={activeError ? `${activeField.name}-error` : undefined}
                        />
                      )}
                    </Field>
                  </div>
                  <div className="mt-12 flex flex-col gap-4 border-t border-[#d6ddf4] pt-6 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-2">
                      {isContextField && previousContext && (
                        <button type="button" onClick={() => setSelectedField(previousContext)} className="rounded-full border border-[#cbd5f4] bg-white px-4 py-3 text-sm font-bold text-[#536189] transition hover:border-[#536fe8] hover:text-[#3157c8]">
                          ← Back
                        </button>
                      )}
                      <p className="text-xs leading-5 text-[#7b85a7]">{isContextField ? "Optional — you can skip this question." : "You can leave this field blank if the information is unavailable."}</p>
                    </div>
                    {isContextField && nextContext ? (
                      <Button type="button" onClick={() => setSelectedField(nextContext)}>Continue →</Button>
                    ) : (
                      <Button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full shrink-0 whitespace-nowrap sm:w-auto sm:min-w-[190px]"
                      >
                        {isSubmitting ? "Assessing…" : isContextField ? "Generate my assessment →" : "Get my assessment →"}
                      </Button>
                    )}
                  </div>
                  {errors.root?.message && <p role="alert" className="mt-4 text-sm font-semibold text-[#b54855]">{errors.root.message}</p>}
                </div>
              </section>
              <LivingIdentityCard fullName={fullName} fieldValues={watchedValues} totalFactors={fieldCatalog.length} />
            </div>
          </form>
        </div>
        <div className="border-t border-[#e2e6f7] px-6 py-5 text-center text-xs text-[#8490b5] sm:px-10">
          Made with ♥ by AI &amp; DS Final Year Team (Prophetic Programmers)
        </div>
      </div>
    </main>
  );
}
