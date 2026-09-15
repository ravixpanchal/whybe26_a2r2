# ML Artifact Compatibility Report

- Generated: `2026-09-15T08:21:02.156719+00:00`
- Artifact directory: `/home/ravi/Desktop/whybe26_a2r2/ml/artifacts`
- Validation mode: read-only; no artifact was modified or overwritten.

## Runtime versions

- Python: `3.14.4`
- NumPy: `2.5.3`
- pandas: `3.0.5`
- scikit-learn: `1.9.1`
- XGBoost: `3.4.1`
- joblib: `1.6.0`

## Artifact inventory

- `model.pkl`: present (11658905 bytes)
- `model_metadata.json`: present (2291 bytes)
- `preprocessing_pipeline.joblib`: present (7674 bytes)
- `feature_metadata.json`: present (6643 bytes)
- `training_metadata.json`: present (2693 bytes)
- `model_logistic_regression.joblib`: present (1199 bytes)
- `model_random_forest.joblib`: present (14267225 bytes)
- `model_gradient_boosting.joblib`: present (225436 bytes)

## Metadata validation

- Model type metadata: `soft_voting_ensemble`
- Target: `defaulted` / feature metadata target: `defaulted`
- Feature count: `36`
- Exact feature order: `['borrower_type', 'household_size', 'income_month_1', 'income_month_2', 'income_month_3', 'income_month_4', 'income_month_5', 'income_month_6', 'employment_type', 'months_at_current_job', 'num_income_sources', 'upi_transactions_per_month', 'upi_avg_transaction_amount', 'upi_months_active', 'mobile_wallet_used', 'utility_bills_paid', 'utility_bills_total', 'rent_paid_on_time_months', 'total_rental_months', 'same_number_since_year', 'avg_monthly_recharge_amount', 'recharge_frequency_per_month', 'ecomm_orders_per_month', 'ecomm_return_rate', 'prepaid_orders_ratio', 'survey_q1', 'survey_q2', 'survey_q3', 'survey_q4', 'survey_q5', 'survey_q6', 'survey_q7', 'survey_q8', 'loan_amount_requested', 'loan_purpose', 'loan_tenure_months']`
- Numeric features (33): `['household_size', 'income_month_1', 'income_month_2', 'income_month_3', 'income_month_4', 'income_month_5', 'income_month_6', 'months_at_current_job', 'num_income_sources', 'upi_transactions_per_month', 'upi_avg_transaction_amount', 'upi_months_active', 'mobile_wallet_used', 'utility_bills_paid', 'utility_bills_total', 'rent_paid_on_time_months', 'total_rental_months', 'same_number_since_year', 'avg_monthly_recharge_amount', 'recharge_frequency_per_month', 'ecomm_orders_per_month', 'ecomm_return_rate', 'prepaid_orders_ratio', 'survey_q1', 'survey_q2', 'survey_q3', 'survey_q4', 'survey_q5', 'survey_q6', 'survey_q7', 'survey_q8', 'loan_amount_requested', 'loan_tenure_months']`
- Categorical features (3): `['borrower_type', 'employment_type', 'loan_purpose']`
- Positive class: `1`
- Primary model metadata: `None`
- Risk thresholds metadata: `None`

## Model structure

- Exact Python type: `sklearn.ensemble._voting.VotingClassifier`
- Is Pipeline: `False`
- Is VotingClassifier: `True`
- Voting mode: `soft`
- `predict()` available: `True`
- `predict_proba()` available: `True`
- Base estimators: `logistic_regression` = `sklearn.pipeline.Pipeline`, `random_forest` = `sklearn.pipeline.Pipeline`, `xgboost` = `sklearn.pipeline.Pipeline`

## Preprocessing

- Effective preprocessing loaded: `sklearn.compose._column_transformer.ColumnTransformer`
- Effective preprocessing source: `embedded estimator pipeline`
- Model exposes pipeline steps: `False`
- Input contract: use the validated effective preprocessing source.
- Standalone preprocessing artifact warning: `builtins.AttributeError: module 'sklearn.compose._column_transformer' has no attribute '_RemainderColsList'`

## Smoke prediction

- Sample shape: `(1, 36)`
- Sample columns match metadata order: `True`
- Prediction shape: `(1,)`
- Prediction class values: `[0]`
- Probability shape: `(1, 2)`
- Probability values: `[[0.7722906641565409, 0.22770933087640524]]`
- Probability range valid: `True`

## Result

- All artifact compatibility checks passed.
