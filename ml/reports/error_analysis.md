# Error analysis

Error analysis uses the selected **soft_voting** model and its validation-selected threshold.
The complete row-level predictions are in `predictions.csv`; inspect false positives and false negatives there.

Error counts and rates are reported in `test_metrics.csv` (`fp`, `fn`, `precision`, and `recall`).
Because the test set is used only once for final evaluation, no test-derived tuning or subgroup selection was performed.
