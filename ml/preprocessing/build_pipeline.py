from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.preprocessing.clean_data import DEFAULT_CLEAN_PATH, TARGET_COLUMN
from ml.preprocessing.split_data import DEFAULT_PROCESSED_DIR, RANDOM_SEED, run_split

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "ml" / "artifacts"
PIPELINE_FILENAME = "preprocessing_pipeline.joblib"
METADATA_FILENAME = "feature_metadata.json"


def classify_features(
    df: pd.DataFrame, target_column: str = TARGET_COLUMN
) -> tuple[list[str], list[str]]:
    if target_column not in df.columns:
        raise ValueError(f"Dataset is missing target column: {target_column}")
    features = df.drop(columns=[target_column])
    numeric = features.select_dtypes(include=np.number).columns.tolist()
    categorical = features.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    unclassified = set(features.columns) - set(numeric) - set(categorical)
    if unclassified:
        raise TypeError(f"Unsupported feature dtypes: {sorted(unclassified)}")
    if not numeric and not categorical:
        raise ValueError("At least one model feature is required")
    return numeric, categorical


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )


def _feature_metadata(
    preprocessor: ColumnTransformer,
    numeric_features: list[str],
    categorical_features: list[str],
    target_column: str,
    split_metadata: dict[str, Any],
) -> dict[str, Any]:
    transformed_features = preprocessor.get_feature_names_out().tolist()
    categorical_encoder = preprocessor.named_transformers_["categorical"].named_steps["encoder"]
    encoded_names = categorical_encoder.get_feature_names_out(categorical_features).tolist()
    transformation_mapping = {
        f"numeric__{feature}": feature for feature in numeric_features
    }
    transformation_mapping.update(
        {f"categorical__{encoded}": original for encoded, original in zip(encoded_names, _expanded_categories(categorical_features, categorical_encoder))}
    )
    return {
        "target_column": target_column,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "original_feature_names": numeric_features + categorical_features,
        "transformed_feature_names": transformed_features,
        "transformation_mapping": transformation_mapping,
        "preprocessing": {
            "numeric_imputation": "median",
            "numeric_scaling": "standard_scaler",
            "categorical_imputation": "most_frequent",
            "categorical_encoding": "one_hot",
            "unknown_categories": "ignored",
        },
        "random_seed": split_metadata["random_seed"],
        "split_ratios": split_metadata["ratios"],
    }


def _expanded_categories(features: list[str], encoder: OneHotEncoder) -> list[str]:
    return [feature for feature, categories in zip(features, encoder.categories_) for _ in categories]


def fit_and_save_pipeline(
    train_df: pd.DataFrame,
    split_metadata: dict[str, Any],
    output_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    target_column: str = TARGET_COLUMN,
) -> dict[str, Any]:
    numeric_features, categorical_features = classify_features(train_df, target_column)
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    preprocessor.fit(train_df.drop(columns=[target_column]))
    metadata = _feature_metadata(
        preprocessor,
        numeric_features,
        categorical_features,
        target_column,
        split_metadata,
    )
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, output_path / PIPELINE_FILENAME)
    (output_path / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def run_phase3(
    source: str | Path = DEFAULT_CLEAN_PATH,
    processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    split_metadata = run_split(source, processed_dir, random_seed)
    train_df = pd.read_csv(Path(processed_dir) / "train.csv")
    return fit_and_save_pipeline(train_df, split_metadata, artifact_dir)


if __name__ == "__main__":
    print(json.dumps(run_phase3(), indent=2))