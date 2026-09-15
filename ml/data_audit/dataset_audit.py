from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "dataset.csv"


def load_dataset(path: str | Path = DATASET_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def audit_dataset(path: str | Path = DATASET_PATH) -> dict[str, Any]:
    df = load_dataset(path)
    missing = df.isna().sum().sort_values(ascending=False)
    missing_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    target_column = "defaulted"
    classes = df[target_column].dropna().value_counts().sort_index()
    positive_class = int(classes.idxmax()) if not classes.empty else None

    return {
        "source_path": str(Path(path)),
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "target_column": target_column,
        "class_mapping": {
            0: "non_default",
            1: "defaulted",
        },
        "positive_class": positive_class,
        "class_distribution": {str(k): int(v) for k, v in classes.to_dict().items()},
        "class_rate": {str(k): round(float(v / len(df)), 4) for k, v in classes.to_dict().items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_value_counts": {str(k): int(v) for k, v in missing.to_dict().items() if v > 0},
        "missing_value_pct": {str(k): round(float(v), 4) for k, v in missing_pct.to_dict().items() if v > 0},
        "leakage_columns": ["default_probability"],
        "leakage_note": "default_probability is directly predictive of the target and must be removed from model inputs.",
        "sensitive_proxy_columns": ["age", "state"],
        "sensitive_proxy_note": "Age and geographic state are proxy-adjacent attributes and should be excluded from the primary model feature set unless explicitly justified.",
        "id_columns": ["borrower_id"],
    }


def main() -> None:
    report = audit_dataset()
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
