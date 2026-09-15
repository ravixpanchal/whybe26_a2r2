from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "dataset.csv"
DEFAULT_RAW_PATH = REPO_ROOT / "ml" / "data" / "raw" / "original_dataset.csv"
DEFAULT_CLEAN_PATH = REPO_ROOT / "ml" / "data" / "processed" / "cleaned_dataset.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "phase2_eda_report.md"
TARGET_COLUMN = "defaulted"
EXCLUDED_COLUMNS = ("borrower_id", "default_probability", "age", "state")


def load_source(path: str | Path = DEFAULT_SOURCE) -> pd.DataFrame:
    return pd.read_csv(path)


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    missing_columns = {TARGET_COLUMN} - set(df.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")

    original_shape = df.shape
    duplicate_rows = int(df.duplicated().sum())
    target_missing_rows = int(df[TARGET_COLUMN].isna().sum())
    cleaned = df.drop_duplicates().copy().dropna(subset=[TARGET_COLUMN])

    categorical_columns = cleaned.select_dtypes(include=["object", "string"]).columns
    for column in categorical_columns:
        cleaned[column] = cleaned[column].astype("string").str.strip().replace("", pd.NA)

    removed_columns = [column for column in EXCLUDED_COLUMNS if column in cleaned.columns]
    cleaned = cleaned.drop(columns=removed_columns)
    cleaned[TARGET_COLUMN] = cleaned[TARGET_COLUMN].astype("int64")

    summary = {
        "original_shape": {"rows": int(original_shape[0]), "columns": int(original_shape[1])},
        "cleaned_shape": {"rows": int(cleaned.shape[0]), "columns": int(cleaned.shape[1])},
        "duplicate_rows_removed": duplicate_rows,
        "target_missing_rows_removed": target_missing_rows,
        "removed_columns": removed_columns,
        "remaining_missing_values": {
            str(column): int(value)
            for column, value in cleaned.isna().sum().items()
            if value > 0
        },
        "missing_value_policy": (
            "Retain feature missingness in the cleaned snapshot. Imputation must be fitted "
            "on training data only in Phase 3 to prevent data leakage."
        ),
    }
    return cleaned, summary


def _outlier_counts(df: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for column in df.select_dtypes(include=np.number).columns:
        if column == TARGET_COLUMN:
            continue
        values = df[column].dropna()
        if values.empty:
            counts[column] = 0
            continue
        first_quartile, third_quartile = values.quantile([0.25, 0.75])
        spread = third_quartile - first_quartile
        lower, upper = first_quartile - 1.5 * spread, third_quartile + 1.5 * spread
        counts[column] = int(((values < lower) | (values > upper)).sum())
    return counts


def profile_dataset(df: pd.DataFrame) -> dict[str, Any]:
    numeric = df.select_dtypes(include=np.number)
    correlations = numeric.corr(numeric_only=True)[TARGET_COLUMN].drop(TARGET_COLUMN)
    correlations = correlations.dropna().sort_values(key=lambda values: values.abs(), ascending=False)
    classes = df[TARGET_COLUMN].value_counts().sort_index()
    return {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        "class_distribution": {str(key): int(value) for key, value in classes.items()},
        "class_rate": {str(key): round(float(value / len(df)), 4) for key, value in classes.items()},
        "missing_value_counts": {
            str(column): int(value) for column, value in df.isna().sum().items() if value > 0
        },
        "outlier_counts_iqr": _outlier_counts(df),
        "numeric_target_correlations": {
            str(key): round(float(value), 4) for key, value in correlations.head(10).items()
        },
    }


def write_eda_report(summary: dict[str, Any], profile: dict[str, Any], path: str | Path) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2 EDA and Cleaning Report", "",
        "## Scope", "",
        "This report is generated from the committed dataset snapshot and the Phase 2 cleaning script.",
        "The target is `defaulted`, where `1` represents default risk.", "",
        "## Cleaning summary", "",
        f"- Original shape: {summary['original_shape']['rows']} rows x {summary['original_shape']['columns']} columns",
        f"- Cleaned shape: {summary['cleaned_shape']['rows']} rows x {summary['cleaned_shape']['columns']} columns",
        f"- Duplicate rows removed: {summary['duplicate_rows_removed']}",
        f"- Rows with missing target removed: {summary['target_missing_rows_removed']}",
        f"- Columns removed: {', '.join(f'`{column}`' for column in summary['removed_columns'])}", "",
        "## Class balance", "", "| Class | Rows | Rate |", "|---:|---:|---:|",
    ]
    for label, count in profile["class_distribution"].items():
        lines.append(f"| {label} | {count} | {profile['class_rate'][label]:.2%} |")
    lines.extend(["", "## Missing values", "", summary["missing_value_policy"], "", "| Feature | Missing rows |", "|---|---:|"])
    for column, count in profile["missing_value_counts"].items():
        lines.append(f"| `{column}` | {count} |")
    lines.extend(["", "## Outlier scan", "", "Potential outliers use the 1.5 x IQR rule; they are reported, not automatically removed.", "", "| Feature | Potential outliers |", "|---|---:|"])
    for column, count in profile["outlier_counts_iqr"].items():
        lines.append(f"| `{column}` | {count} |")
    lines.extend(["", "## Numeric feature relationships", "", "Top absolute Pearson correlations with the target:", "", "| Feature | Correlation |", "|---|---:|"])
    for column, value in profile["numeric_target_correlations"].items():
        lines.append(f"| `{column}` | {value:.4f} |")
    lines.extend(["", "## Phase 2 decisions", "", "- Duplicate records are removed before modeling.", "- Rows without a target are removed because they cannot be used for supervised learning.", "- Identifier, leakage, and Phase 1 proxy-excluded columns are removed from the modeling snapshot.", "- Potential numeric outliers are flagged for review and retained; automatic clipping would erase information without a domain rule.", "- Missing feature values are retained and will be imputed inside a training-fitted preprocessing pipeline in Phase 3.", "- Class imbalance is recorded for Phase 4; model evaluation must include minority-class recall and F1, not accuracy alone.", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_phase2(source: str | Path = DEFAULT_SOURCE) -> dict[str, Any]:
    source_path = Path(source)
    DEFAULT_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != DEFAULT_RAW_PATH.resolve():
        shutil.copy2(source_path, DEFAULT_RAW_PATH)
    cleaned, summary = clean_dataset(load_source(source_path))
    profile = profile_dataset(cleaned)
    DEFAULT_CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(DEFAULT_CLEAN_PATH, index=False)
    metadata_path = DEFAULT_CLEAN_PATH.with_suffix(".json")
    metadata_path.write_text(json.dumps({"cleaning": summary, "profile": profile}, indent=2), encoding="utf-8")
    write_eda_report(summary, profile, DEFAULT_REPORT_PATH)
    return {"cleaning": summary, "profile": profile}


if __name__ == "__main__":
    print(json.dumps(run_phase2(), indent=2))