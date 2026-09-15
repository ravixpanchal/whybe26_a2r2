import pandas as pd

from ml.preprocessing.clean_data import clean_dataset, profile_dataset


def test_clean_dataset_removes_duplicates_target_gaps_and_excluded_columns():
    source = pd.DataFrame(
        {
            "borrower_id": ["a", "a", "b"],
            "age": [30, 30, 40],
            "state": [" NY ", " NY ", "CA"],
            "default_probability": [0.2, 0.2, 0.3],
            "borrower_type": [" salaried ", " salaried ", "self-employed"],
            "income": [100.0, 100.0, 200.0],
            "defaulted": [0, 0, None],
        }
    )

    cleaned, summary = clean_dataset(source)

    assert cleaned.shape == (1, 3)
    assert cleaned.columns.tolist() == ["borrower_type", "income", "defaulted"]
    assert cleaned.loc[0, "borrower_type"] == "salaried"
    assert summary["duplicate_rows_removed"] == 1
    assert summary["target_missing_rows_removed"] == 1


def test_profile_dataset_reports_class_rates_and_outliers():
    frame = pd.DataFrame({"income": [1.0, 1.0, 1.0, 100.0], "defaulted": [0, 0, 1, 1]})

    profile = profile_dataset(frame)

    assert profile["class_distribution"] == {"0": 2, "1": 2}
    assert profile["class_rate"] == {"0": 0.5, "1": 0.5}
    assert profile["outlier_counts_iqr"]["income"] == 1