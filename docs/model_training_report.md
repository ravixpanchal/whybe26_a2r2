# Phase 4 Model Training Report

Three required classifiers were tuned on the Phase 3 training split using three-fold stratified cross-validation scored by ROC-AUC.
Validation metrics below are measured on the held-out validation split. The test split remains untouched for Phase 5 evaluation.

- Random seed: `42`
- scikit-learn: `1.5.1`
- Class imbalance: balanced sample weights were passed to each estimator during fitting.
- Probability calibration: not applied in Phase 4; Brier scores are recorded for Phase 5 assessment.

| Model | CV ROC-AUC | CV std | Validation ROC-AUC | F1 | Recall | Brier |
|---|---:|---:|---:|---:|---:|---:|
| `logistic_regression` | 0.8992 | 0.0077 | 0.9025 | 0.4444 | 0.9689 | 0.2672 |
| `random_forest` | 0.9052 | 0.0128 | 0.9053 | 0.5928 | 0.6178 | 0.0859 |
| `gradient_boosting` | 0.9153 | 0.0085 | 0.9145 | 0.6081 | 0.8311 | 0.1116 |

Primary model selection and risk thresholds are intentionally deferred to Phase 5.
