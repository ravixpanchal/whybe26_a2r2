# Dataset Documentation

## Dataset source and scope

This project uses the loan-risk borrower dataset stored in `dataset.csv` at the repository root. The dataset contains 10,000 borrower rows and 41 columns. It is treated as the working dataset for the MVP and has been assessed for model readiness.

## Target definition

- Target column: `defaulted`
- Positive class: 1 (`defaulted`)
- Negative class: 0 (`non_default`)
- Class distribution: 8,499 rows with label 0 and 1,501 rows with label 1
- Base default rate: 15.01%

This means the problem is a binary risk classification task where higher risk is represented by the positive class (`1`).

## Leakage review

The following column is explicitly treated as a leakage risk and must be excluded from training features:

- `default_probability`: this is a direct model-derived risk estimate and is strongly correlated with the target; it is not a borrower-provided feature and would leak target-related information into the model.

Additional non-feature identifiers that must be removed from model input:

- `borrower_id`: unique record ID, not a predictive feature

## Sensitive feature review

The following columns are considered proxy-adjacent or sensitive: 

- `age`
- `state`

These features are not automatically excluded from all analysis, but they should be excluded from the primary MVP feature set for fairness and model simplicity unless a product/legal review explicitly justifies keeping them. For the initial implementation, exclude them from the primary training feature list.

## Missing value profile

The dataset has missing values in several fields, with the largest missingness concentrated in:

- `ecomm_return_rate`: 20.76%
- `prepaid_orders_ratio`: 20.76%
- `rent_paid_on_time_months`: 20.58%
- `total_rental_months`: 20.58%
- `upi_months_active`: 17.36%
- `upi_transactions_per_month`: 17.25%
- `upi_avg_transaction_amount`: 17.25%
- `mobile_wallet_used`: 15.40%
- `survey_q4`: 10.79%
- `survey_q6`: 9.90%

No duplicate rows were found. Missingness is a real preprocessing requirement. Phase 2 retains missing feature values in the cleaned snapshot; Phase 3 must fit imputation statistics on training data only and reuse them for validation, test, and inference.

## Feature schema decisions for MVP

### Numeric features

The following columns are numeric and should be passed through the preprocessing pipeline as numeric features:

- `age`
- `household_size`
- `income_month_1` to `income_month_6`
- `months_at_current_job`
- `num_income_sources`
- `upi_transactions_per_month`
- `upi_avg_transaction_amount`
- `upi_months_active`
- `mobile_wallet_used`
- `utility_bills_paid`
- `utility_bills_total`
- `rent_paid_on_time_months`
- `total_rental_months`
- `same_number_since_year`
- `avg_monthly_recharge_amount`
- `recharge_frequency_per_month`
- `ecomm_orders_per_month`
- `ecomm_return_rate`
- `prepaid_orders_ratio`
- `survey_q1` to `survey_q8`
- `loan_amount_requested`
- `loan_tenure_months`

### Categorical features

The following columns are categorical and should be encoded before model fitting:

- `borrower_type`
- `state`
- `employment_type`
- `loan_purpose`

### Excluded from primary model input

- `borrower_id`
- `default_probability`
- `defaulted` (target only)
- `age` and `state` (fairness-proxy and model simplification decision for the MVP)

## Dataset-dependent decision summary

| Decision | Resolution |
|---|---|
| Target variable | `defaulted` |
| Positive class | 1 = defaulted |
| Feature list | finalized from the audited dataset with exclusions applied |
| Missing-value policy | retain missing feature values through Phase 2; fit and apply imputation inside the Phase 3 training pipeline only |
| Sensitive features | `age`, `state` excluded from primary model feature set |
| Leakage detection | `default_probability` excluded |
| Duplicate rows | none |
| Risk thresholds | not yet finalized; must be derived from model validation outputs during Phase 5 |

## Phase 2 outputs

- Cleaned modeling snapshot: `ml/data/processed/cleaned_dataset.csv`
- Cleaning metadata and EDA profile: `ml/data/processed/cleaned_dataset.json`
- Reproducible raw snapshot: `ml/data/raw/original_dataset.csv`
- EDA and cleaning report: `docs/phase2_eda_report.md`
- Generator: `ml/preprocessing/clean_data.py`

## Phase 3 outputs

- Stratified splits: `ml/data/processed/train.csv`, `validation.csv`, and `test.csv`
- Split summary: `ml/data/processed/split_metadata.json`
- Fitted preprocessing pipeline: `ml/artifacts/preprocessing_pipeline.joblib`
- Feature metadata and transformed-name mapping: `ml/artifacts/feature_metadata.json`
- Data dictionary: `docs/data_dictionary.md`
- Split and pipeline generators: `ml/preprocessing/split_data.py` and `ml/preprocessing/build_pipeline.py`

## Phase 4 outputs

- Logistic Regression artifact: `ml/artifacts/model_logistic_regression.joblib`
- Random Forest artifact: `ml/artifacts/model_random_forest.joblib`
- Gradient Boosting artifact: `ml/artifacts/model_gradient_boosting.joblib`
- Training metrics and reproducibility metadata: `ml/artifacts/training_metadata.json`
- Training report: `docs/model_training_report.md`
- Training entry point: `ml/training/train_models.py`

Phase 4 records validation metrics and calibration diagnostics but does not select a primary model or define risk thresholds. Those decisions are reserved for Phase 5 and must use the untouched test split.

## Implementation note

This document is the source of truth for Phase 1. All downstream modeling and API work must not use a hardcoded feature list, target mapping, or threshold logic that contradicts this decision record.
