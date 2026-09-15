"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Field } from "@/components/forms/field";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { requestExplanation } from "@/lib/api";
import type { AssessmentRequest, BorrowerInput } from "@/types/assessment";

const optionalNumber = (minimum?: number, maximum?: number) =>
  z.preprocess(
    (value) => (value === "" || (typeof value === "number" && Number.isNaN(value)) ? null : value),
    z.number().finite().min(minimum ?? -Infinity).max(maximum ?? Infinity).nullable(),
  );
const borrowerSchema = z
  .object({
    borrower_type: z.preprocess((value) => (value === "" ? null : value), z.enum(["gig", "migrant", "rural"]).nullable()),
    household_size: optionalNumber(0),
    income_month_1: optionalNumber(0),
    income_month_2: optionalNumber(0),
    income_month_3: optionalNumber(0),
    income_month_4: optionalNumber(0),
    income_month_5: optionalNumber(0),
    income_month_6: optionalNumber(0),
    employment_type: z.preprocess((value) => (value === "" ? null : value), z.enum(["daily-wage", "salaried-gig", "seasonal", "self-employed"]).nullable()),
    months_at_current_job: optionalNumber(0),
    num_income_sources: optionalNumber(0),
    upi_transactions_per_month: optionalNumber(0),
    upi_avg_transaction_amount: optionalNumber(0),
    upi_months_active: optionalNumber(0),
    mobile_wallet_used: optionalNumber(0, 1),
    utility_bills_paid: optionalNumber(0),
    utility_bills_total: optionalNumber(0),
    rent_paid_on_time_months: optionalNumber(0),
    total_rental_months: optionalNumber(0),
    same_number_since_year: optionalNumber(1900, 2100),
    avg_monthly_recharge_amount: optionalNumber(0),
    recharge_frequency_per_month: optionalNumber(0),
    ecomm_orders_per_month: optionalNumber(0),
    ecomm_return_rate: optionalNumber(0, 1),
    prepaid_orders_ratio: optionalNumber(0, 1),
    survey_q1: optionalNumber(1, 5),
    survey_q2: optionalNumber(1, 5),
    survey_q3: optionalNumber(1, 5),
    survey_q4: optionalNumber(1, 5),
    survey_q5: optionalNumber(1, 5),
    survey_q6: optionalNumber(1, 5),
    survey_q7: optionalNumber(1, 5),
    survey_q8: optionalNumber(1, 5),
    loan_amount_requested: optionalNumber(0),
    loan_purpose: z.preprocess((value) => (value === "" ? null : value), z.enum(["agriculture", "business", "consumption", "education", "medical"]).nullable()),
    loan_tenure_months: optionalNumber(0),
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

function inputClass(hasError: boolean) {
  return `w-full rounded-xl border bg-white px-3 py-3 text-sm text-[var(--brand-dark)] outline-none transition focus:border-[var(--brand)] focus:ring-2 focus:ring-[#bfe4d4] ${hasError ? "border-red-400" : "border-[var(--line)]"}`;
}

export default function AssessmentPage() {
  const router = useRouter();
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(borrowerSchema),
    defaultValues: defaults,
  });

  const onSubmit = async (values: FormValues) => {
    const parsed = borrowerSchema.parse(values);
    try {
      const result = await requestExplanation({ borrower_input: parsed as BorrowerInput } satisfies AssessmentRequest);
      sessionStorage.setItem("credilens:last-explanation", JSON.stringify(result));
      sessionStorage.setItem("credilens:last-assessment", JSON.stringify(result.assessment));
      sessionStorage.setItem("credilens:last-input", JSON.stringify(parsed));
      router.push("/assessment/results");
    } catch {
      setError("root", { message: "We could not reach the assessment service. Please try again." });
    }
  };

  return (
    <main className="min-h-screen bg-[var(--background)] px-6 py-10 lg:px-10">
      <div className="mx-auto max-w-5xl">
        <Link href="/" className="text-sm font-bold text-[var(--brand)]">← Back to CrediLens</Link>
        <div className="mt-10 max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-[var(--brand)]">Borrower assessment</p>
          <h1 className="display-font mt-4 text-5xl tracking-[-0.04em] text-[var(--brand-dark)]">Bring your context.</h1>
          <p className="mt-5 text-base leading-7 text-[var(--muted)]">
            All 36 fields come directly from the finalized model schema. You can leave a value blank when it is unavailable; the result will show how missing information affects reliability.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-12 space-y-8" noValidate>
          <Card className="p-6 sm:p-8">
            <h2 className="display-font text-2xl text-[var(--brand-dark)]">Identity and employment</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">A little context about your household and work.</p>
            <div className="mt-7 grid gap-6 sm:grid-cols-2">
              <Field id="borrower_type" label="Borrower type" error={errors.borrower_type?.message}>
                <select id="borrower_type" className={inputClass(!!errors.borrower_type)} {...register("borrower_type")} aria-describedby={errors.borrower_type ? "borrower_type-error" : undefined}>
                  <option value="">Select one</option><option value="gig">Gig worker</option><option value="migrant">Migrant worker</option><option value="rural">Rural borrower</option>
                </select>
              </Field>
              {numericFields.slice(0, 1).map(([name, label, description]) => (
                <Field key={name} id={name} label={label} description={description} error={errors[name]?.message as string | undefined}>
                  <input id={name} type="number" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} />
                </Field>
              ))}
              <Field id="employment_type" label="Employment type" error={errors.employment_type?.message}>
                <select id="employment_type" className={inputClass(!!errors.employment_type)} {...register("employment_type")}><option value="">Select one</option><option value="daily-wage">Daily wage</option><option value="salaried-gig">Salaried gig</option><option value="seasonal">Seasonal</option><option value="self-employed">Self-employed</option></select>
              </Field>
              {numericFields.slice(1, 3).map(([name, label, description]) => (
                <Field key={name} id={name} label={label} description={description} error={errors[name]?.message as string | undefined}>
                  <input id={name} type="number" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} />
                </Field>
              ))}
            </div>
          </Card>

          <Card className="p-6 sm:p-8">
            <h2 className="display-font text-2xl text-[var(--brand-dark)]">Income and everyday activity</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">Use monthly averages where the field asks for a month.</p>
            <div className="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((month) => {
                const name = `income_month_${month}` as keyof FormValues;
                return <Field key={name} id={name} label={`Income month ${month}`} error={errors[name]?.message as string | undefined}><input id={name} type="number" step="0.01" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} /></Field>;
              })}
              {numericFields.slice(3, 17).map(([name, label, description]) => (
                <Field key={name} id={name} label={label} description={description} error={errors[name]?.message as string | undefined}>
                  <input id={name} type="number" step="0.01" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} />
                </Field>
              ))}
            </div>
          </Card>

          <Card className="p-6 sm:p-8">
            <h2 className="display-font text-2xl text-[var(--brand-dark)]">Survey and loan details</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">Survey answers use a 1–5 scale.</p>
            <div className="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 8 }, (_, index) => {
                const name = `survey_q${index + 1}` as keyof FormValues;
                return <Field key={name} id={name} label={`Survey question ${index + 1}`} error={errors[name]?.message as string | undefined}><input id={name} type="number" min="1" max="5" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} /></Field>;
              })}
              <Field id="loan_purpose" label="Loan purpose" error={errors.loan_purpose?.message}>
                <select id="loan_purpose" className={inputClass(!!errors.loan_purpose)} {...register("loan_purpose")}><option value="">Select one</option><option value="agriculture">Agriculture</option><option value="business">Business</option><option value="consumption">Consumption</option><option value="education">Education</option><option value="medical">Medical</option></select>
              </Field>
              {numericFields.slice(-2).map(([name, label, description]) => (
                <Field key={name} id={name} label={label} description={description} error={errors[name]?.message as string | undefined}>
                  <input id={name} type="number" step="0.01" className={inputClass(!!errors[name])} {...register(name, { valueAsNumber: true })} />
                </Field>
              ))}
            </div>
          </Card>

          <div className="flex flex-col items-start justify-between gap-5 rounded-2xl bg-[var(--brand-dark)] p-6 text-white sm:flex-row sm:items-center sm:p-8">
            <div><p className="font-bold">Ready to see your assessment?</p><p className="mt-1 text-sm text-[#c5ddd2]">The result is educational, explainable, and not a lending decision.</p></div>
            <div className="flex flex-col items-start gap-3 sm:items-end">
              {errors.root?.message && <p role="alert" className="text-sm font-semibold text-[#ffc4bb]">{errors.root.message}</p>}
              <Button type="submit" variant="light" disabled={isSubmitting}>{isSubmitting ? "Assessing…" : "Get my assessment →"}</Button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
