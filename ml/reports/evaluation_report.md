# Phase 5 model evaluation

## Protocol
- All four candidates were fit independently on `processed/train.csv` only.
- `processed/validation.csv` was used for ROC-AUC model selection and F1 threshold analysis.
- `processed/test.csv` was untouched until the final evaluation below.
- Selected primary model: **soft_voting** (highest validation ROC-AUC).

The repository-root `model.pkl` is not used for this comparison: its metadata shows it was fit on train + validation. Therefore validation is not independent for thresholding/model selection for that existing artifact; this report uses a new train-only fit for a fair comparison.

## Validation and test metrics

| model               |   roc_auc_validation |   average_precision_validation |   log_loss_validation |   f1_validation |   roc_auc_test |   average_precision_test |   log_loss_test |   f1_test |
|:--------------------|---------------------:|-------------------------------:|----------------------:|----------------:|---------------:|-------------------------:|----------------:|----------:|
| logistic_regression |               0.9011 |                         0.6549 |                0.3941 |          0.6110 |         0.9009 |                   0.6315 |          0.4077 |    0.5938 |
| random_forest       |               0.9076 |                         0.6434 |                0.2587 |          0.6316 |         0.9104 |                   0.6665 |          0.2569 |    0.5982 |
| xgboost             |               0.9122 |                         0.6706 |                0.2859 |          0.6337 |         0.9110 |                   0.6606 |          0.2905 |    0.6132 |
| soft_voting         |               0.9135 |                         0.6732 |                0.2816 |          0.6313 |         0.9153 |                   0.6799 |          0.2845 |    0.6154 |

## Thresholds

| model               |   threshold | objective   |   validation_f1 |   validation_balanced_accuracy |
|:--------------------|------------:|:------------|----------------:|-------------------------------:|
| logistic_regression |      0.6800 | f1          |          0.6110 |                         0.8025 |
| random_forest       |      0.2900 | f1          |          0.6316 |                         0.8271 |
| xgboost             |      0.5500 | f1          |          0.6337 |                         0.8003 |
| soft_voting         |      0.5900 | f1          |          0.6313 |                         0.7844 |

## Cross-validation

Five-fold stratified CV was run on the training split. Fold-level results are in `cross_validation_results.csv`.

## Reproducibility
- Data root: `/home/ravi/Desktop/whybe26_a2r2`
- Seed: 42
- Plots are in `plots/`; predictions and machine-readable metrics are CSV/JSON.
