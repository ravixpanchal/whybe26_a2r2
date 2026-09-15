# ML Artifact Compatibility Report

- Generated: `2026-09-15T07:11:48.514094+00:00`
- Artifact directory: `D:\ENGINEER\WHYBEE\ml\artifacts`
- Validation mode: read-only; no artifact was modified or overwritten.

## Runtime versions

- Python: `3.12.7`
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

## Validation stopped

Model loading failed before runtime type inspection or prediction.
- Exact error: `xgboost._c_api.XGBoostError: input stream corrupted`
- Classification: incompatible dependency/version or serialization format; no workaround was applied.

```text
Traceback (most recent call last):
  File "D:\ENGINEER\WHYBEE\ml\evaluation\validate_artifacts.py", line 138, in main
    model = joblib.load(ARTIFACT_DIR / "model.pkl")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\ENGINEER\WHYBEE\ml\.venv\Lib\site-packages\joblib\numpy_pickle.py", line 755, in load
    obj = _unpickle(
          ^^^^^^^^^^
  File "D:\ENGINEER\WHYBEE\ml\.venv\Lib\site-packages\joblib\numpy_pickle.py", line 632, in _unpickle
    obj = unpickler.load()
          ^^^^^^^^^^^^^^^^
  File "C:\Users\Ajitesh Channa\anaconda3\Lib\pickle.py", line 1255, in load
    dispatch[key[0]](self)
  File "D:\ENGINEER\WHYBEE\ml\.venv\Lib\site-packages\joblib\numpy_pickle.py", line 452, in load_build
    Unpickler.load_build(self)
  File "C:\Users\Ajitesh Channa\anaconda3\Lib\pickle.py", line 1759, in load_build
    setstate(state)
  File "D:\ENGINEER\WHYBEE\ml\.venv\Lib\site-packages\xgboost\core.py", line 1906, in __setstate__
    _check_call(_LIB.XGBoosterUnserializeFromBuffer(handle, ptr, length))
  File "D:\ENGINEER\WHYBEE\ml\.venv\Lib\site-packages\xgboost\_c_api.py", line 190, in _check_call
    raise XGBoostError(py_str(_LIB.XGBGetLastError()))
xgboost._c_api.XGBoostError: input stream corrupted
```
