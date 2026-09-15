# CrediLens AI Data Dictionary

This dictionary describes the Phase 3 cleaned modeling snapshot. The target is `defaulted`; `1` means defaulted and `0` means non-defaulted.

## Modeling features

### Numeric features

`household_size`, `income_month_1` through `income_month_6`, `months_at_current_job`, `num_income_sources`, `upi_transactions_per_month`, `upi_avg_transaction_amount`, `upi_months_active`, `mobile_wallet_used`, `utility_bills_paid`, `utility_bills_total`, `rent_paid_on_time_months`, `total_rental_months`, `same_number_since_year`, `avg_monthly_recharge_amount`, `recharge_frequency_per_month`, `ecomm_orders_per_month`, `ecomm_return_rate`, `prepaid_orders_ratio`, `survey_q1` through `survey_q8`, `loan_amount_requested`, and `loan_tenure_months`.

Numeric missing values are imputed with the training-set median and then standardized with `StandardScaler`.

### Categorical features

- `borrower_type`
- `employment_type`
- `loan_purpose`

Categorical missing values are imputed with the training-set most frequent value and then one-hot encoded. Categories not seen during training are ignored at transform time.

## Target

- `defaulted`: binary supervised-learning target; `0` = non-defaulted, `1` = defaulted.

## Excluded columns

- `borrower_id`: record identifier, not a borrower feature.
- `default_probability`: leakage-prone model-derived value.
- `age` and `state`: proxy-adjacent features excluded from the primary MVP model feature set by the Phase 1 decision.

## Reproducibility

- Split seed: `42`
- Split ratios: 70% train, 15% validation, 15% test
- Preprocessing is fitted only on `train.csv`.
- The authoritative transformed-feature mapping is stored in `ml/artifacts/feature_metadata.json`.