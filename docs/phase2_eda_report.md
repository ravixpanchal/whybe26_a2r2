# Phase 2 EDA and Cleaning Report

## Scope

This report is generated from the committed dataset snapshot and the Phase 2 cleaning script.
The target is `defaulted`, where `1` represents default risk.

## Cleaning summary

- Original shape: 10000 rows x 41 columns
- Cleaned shape: 10000 rows x 37 columns
- Duplicate rows removed: 0
- Rows with missing target removed: 0
- Columns removed: `borrower_id`, `default_probability`, `age`, `state`

## Class balance

| Class | Rows | Rate |
|---:|---:|---:|
| 0 | 8499 | 84.99% |
| 1 | 1501 | 15.01% |

## Missing values

Retain feature missingness in the cleaned snapshot. Imputation must be fitted on training data only in Phase 3 to prevent data leakage.

| Feature | Missing rows |
|---|---:|
| `upi_transactions_per_month` | 1725 |
| `upi_avg_transaction_amount` | 1725 |
| `upi_months_active` | 1736 |
| `mobile_wallet_used` | 1540 |
| `rent_paid_on_time_months` | 2058 |
| `total_rental_months` | 2058 |
| `same_number_since_year` | 779 |
| `ecomm_return_rate` | 2076 |
| `prepaid_orders_ratio` | 2076 |
| `survey_q4` | 1079 |
| `survey_q6` | 990 |

## Outlier scan

Potential outliers use the 1.5 x IQR rule; they are reported, not automatically removed.

| Feature | Potential outliers |
|---|---:|
| `household_size` | 0 |
| `income_month_1` | 144 |
| `income_month_2` | 136 |
| `income_month_3` | 317 |
| `income_month_4` | 124 |
| `income_month_5` | 123 |
| `income_month_6` | 256 |
| `months_at_current_job` | 67 |
| `num_income_sources` | 0 |
| `upi_transactions_per_month` | 0 |
| `upi_avg_transaction_amount` | 17 |
| `upi_months_active` | 0 |
| `mobile_wallet_used` | 0 |
| `utility_bills_paid` | 10 |
| `utility_bills_total` | 0 |
| `rent_paid_on_time_months` | 6 |
| `total_rental_months` | 0 |
| `same_number_since_year` | 0 |
| `avg_monthly_recharge_amount` | 0 |
| `recharge_frequency_per_month` | 18 |
| `ecomm_orders_per_month` | 0 |
| `ecomm_return_rate` | 17 |
| `prepaid_orders_ratio` | 0 |
| `survey_q1` | 0 |
| `survey_q2` | 0 |
| `survey_q3` | 0 |
| `survey_q4` | 0 |
| `survey_q5` | 0 |
| `survey_q6` | 0 |
| `survey_q7` | 0 |
| `survey_q8` | 0 |
| `loan_amount_requested` | 0 |
| `loan_tenure_months` | 0 |

## Numeric feature relationships

Top absolute Pearson correlations with the target:

| Feature | Correlation |
|---|---:|
| `upi_avg_transaction_amount` | -0.3847 |
| `recharge_frequency_per_month` | -0.3681 |
| `upi_transactions_per_month` | -0.3536 |
| `avg_monthly_recharge_amount` | -0.3450 |
| `upi_months_active` | -0.3442 |
| `num_income_sources` | -0.3372 |
| `income_month_5` | -0.3308 |
| `income_month_4` | -0.3306 |
| `ecomm_return_rate` | 0.3281 |
| `income_month_2` | -0.3241 |

## Phase 2 decisions

- Duplicate records are removed before modeling.
- Rows without a target are removed because they cannot be used for supervised learning.
- Identifier, leakage, and Phase 1 proxy-excluded columns are removed from the modeling snapshot.
- Potential numeric outliers are flagged for review and retained; automatic clipping would erase information without a domain rule.
- Missing feature values are retained and will be imputed inside a training-fitted preprocessing pipeline in Phase 3.
- Class imbalance is recorded for Phase 4; model evaluation must include minority-class recall and F1, not accuracy alone.
