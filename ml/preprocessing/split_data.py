from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.preprocessing.clean_data import DEFAULT_CLEAN_PATH, TARGET_COLUMN

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED_DIR = REPO_ROOT / "ml" / "data" / "processed"
RANDOM_SEED = 42
TRAIN_SIZE = 0.70
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15


def split_dataset(
    df: pd.DataFrame,
    *,
    target_column: str = TARGET_COLUMN,
    random_seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if target_column not in df.columns:
        raise ValueError(f"Dataset is missing target column: {target_column}")
    if df[target_column].isna().any():
        raise ValueError("Cannot split data while the target contains missing values")
    if df[target_column].nunique() < 2:
        raise ValueError("Stratified splitting requires at least two target classes")

    train, remainder = train_test_split(
        df,
        test_size=VALIDATION_SIZE + TEST_SIZE,
        random_state=random_seed,
        stratify=df[target_column],
    )
    validation, test = train_test_split(
        remainder,
        test_size=TEST_SIZE / (VALIDATION_SIZE + TEST_SIZE),
        random_state=random_seed,
        stratify=remainder[target_column],
    )

    split_frames = {"train": train, "validation": validation, "test": test}
    summary = {
        "random_seed": random_seed,
        "ratios": {"train": TRAIN_SIZE, "validation": VALIDATION_SIZE, "test": TEST_SIZE},
        "splits": {
            name: {
                "rows": int(frame.shape[0]),
                "class_distribution": {
                    str(label): int(count)
                    for label, count in frame[target_column].value_counts().sort_index().items()
                },
            }
            for name, frame in split_frames.items()
        },
    }
    return train, validation, test, summary


def write_splits(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    summary: dict[str, Any],
    output_dir: str | Path = DEFAULT_PROCESSED_DIR,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    train.to_csv(output_path / "train.csv", index=False)
    validation.to_csv(output_path / "validation.csv", index=False)
    test.to_csv(output_path / "test.csv", index=False)
    (output_path / "split_metadata.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run_split(
    source: str | Path = DEFAULT_CLEAN_PATH,
    output_dir: str | Path = DEFAULT_PROCESSED_DIR,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    train, validation, test, summary = split_dataset(pd.read_csv(source), random_seed=random_seed)
    write_splits(train, validation, test, summary, output_dir)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_split(), indent=2))