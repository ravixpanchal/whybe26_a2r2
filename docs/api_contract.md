# API Contract

## `POST /api/assessment/predict`

The endpoint accepts the finalized 36-feature borrower contract under
`borrower_input` and runs the validated portable soft-voting ensemble. It does
not substitute individual legacy estimators.

```json
{
  "borrower_input": {
    "borrower_type": "gig",
    "household_size": 3,
    "income_month_1": 10,
    "income_month_2": 10,
    "income_month_3": 10,
    "income_month_4": 10,
    "income_month_5": 10,
    "income_month_6": 10,
    "employment_type": "salaried-gig",
    "months_at_current_job": 12,
    "num_income_sources": 1,
    "upi_transactions_per_month": 10,
    "upi_avg_transaction_amount": 100,
    "upi_months_active": 12,
    "mobile_wallet_used": 1,
    "utility_bills_paid": 6,
    "utility_bills_total": 6,
    "rent_paid_on_time_months": 12,
    "total_rental_months": 12,
    "same_number_since_year": 2018,
    "avg_monthly_recharge_amount": 100,
    "recharge_frequency_per_month": 1,
    "ecomm_orders_per_month": 1,
    "ecomm_return_rate": 0.1,
    "prepaid_orders_ratio": 0.5,
    "survey_q1": 3,
    "survey_q2": 3,
    "survey_q3": 3,
    "survey_q4": 3,
    "survey_q5": 3,
    "survey_q6": 3,
    "survey_q7": 3,
    "survey_q8": 3,
    "loan_amount_requested": 50000,
    "loan_purpose": "business",
    "loan_tenure_months": 12
  }
}
```

Example response:

```json
{
  "model_comparison": {
    "prediction": {
      "model_name": "soft_voting_ensemble",
      "predicted_class": "0",
      "probability": 0.18
    },
    "primary_model": "soft_voting_ensemble",
    "compatibility_status": "validated"
  },
  "risk_probability": 0.18,
  "risk_category": "low",
  "class_mapping": {
    "negative_class": 0,
    "positive_class": 1,
    "positive_class_meaning": "defaulted"
  }
}
```

The response returns the ensemble class, positive-class (`defaulted`)
probability, validated compatibility status, and the documented `0.59`
positive-risk threshold. The two-band category is `low` below the threshold
and `high` at or above it; no unsupported moderate threshold is invented.

## `POST /api/assessment/explanation`

This endpoint accepts the same request body, first obtains the validated model
prediction, and then optionally translates that fixed result into concise
educational language through OpenRouter. The model result is never delegated to
the language model.

The response includes:

- `assessment`: the complete prediction, feature contributions, and reliability
  information;
- `explanation`: OpenRouter text or a deterministic local fallback;
- `explanation_source`: `openrouter` or `fallback`;
- `disclaimer`: a responsible-use limitation.

If `OPENROUTER_API_KEY` is absent, the upstream service times out, returns a
transient error after one retry, or produces unsafe/contradictory text, the
endpoint returns the local fallback with HTTP 200. API keys remain backend-only
and are never included in prompts or responses.
