export type RiskCategory = "low" | "moderate" | "high";
export type ReliabilityLevel = "high" | "medium" | "low";

export type FeatureContribution = {
  feature: string;
  contribution: number;
  direction: "risk_increasing" | "risk_reducing";
};

export type ReliabilityInfo = {
  level: ReliabilityLevel;
  score: number;
  reasons: string[];
  disclaimer: string;
};

export type AssessmentResponse = {
  model_comparison: {
    prediction: {
      model_name: "soft_voting_ensemble";
      predicted_class: string;
      probability: number;
    };
    primary_model: "soft_voting_ensemble";
    compatibility_status: "validated";
  };
  risk_probability: number;
  risk_category: RiskCategory;
  class_mapping: Record<string, unknown>;
  feature_contributions: FeatureContribution[];
  reliability: ReliabilityInfo;
};

export type BorrowerInput = {
  borrower_type: string | null;
  household_size: number | null;
  income_month_1: number | null;
  income_month_2: number | null;
  income_month_3: number | null;
  income_month_4: number | null;
  income_month_5: number | null;
  income_month_6: number | null;
  employment_type: string | null;
  months_at_current_job: number | null;
  num_income_sources: number | null;
  upi_transactions_per_month: number | null;
  upi_avg_transaction_amount: number | null;
  upi_months_active: number | null;
  mobile_wallet_used: number | null;
  utility_bills_paid: number | null;
  utility_bills_total: number | null;
  rent_paid_on_time_months: number | null;
  total_rental_months: number | null;
  same_number_since_year: number | null;
  avg_monthly_recharge_amount: number | null;
  recharge_frequency_per_month: number | null;
  ecomm_orders_per_month: number | null;
  ecomm_return_rate: number | null;
  prepaid_orders_ratio: number | null;
  survey_q1: number | null;
  survey_q2: number | null;
  survey_q3: number | null;
  survey_q4: number | null;
  survey_q5: number | null;
  survey_q6: number | null;
  survey_q7: number | null;
  survey_q8: number | null;
  loan_amount_requested: number | null;
  loan_purpose: string | null;
  loan_tenure_months: number | null;
};
export type AssessmentRequest = { borrower_input: BorrowerInput };
export type BorrowerMetadata = {
  full_name: string;
  date_of_birth: string;
};
export type FinancialContext = {
  emergency_financial_resilience: string | null;
  repayment_comfort: number | null;
};

export type ExplanationResponse = {
  assessment: AssessmentResponse;
  explanation: string;
  explanation_source: "openrouter" | "fallback";
  disclaimer: string;
};

export type SimulatorResponse = {
  assessment: AssessmentResponse;
  disclaimer: string;
};
