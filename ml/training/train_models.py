from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from ml.preprocessing.build_pipeline import DEFAULT_ARTIFACT_DIR, PIPELINE_FILENAME
from ml.preprocessing.clean_data import DEFAULT_CLEAN_PATH, TARGET_COLUMN
from ml.preprocessing.split_data import DEFAULT_PROCESSED_DIR, RANDOM_SEED

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAINING_REPORT = REPO_ROOT / "docs" / "model_training_report.md"
MODEL_FILENAMES = {
    "logistic_regression": "model_logistic_regression.joblib",
    "random_forest": "model_random_forest.joblib",
    "gradient_boosting": "model_gradient_boosting.joblib",
}
TRAINING_METADATA_FILENAME = "training_metadata.json"


def build_model_searches(random_seed: int = RANDOM_SEED) -> dict[str, GridSearchCV]:
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_seed)
    models_and_grids = {
        "logistic_regression": (
            LogisticRegression(class_weight="balanced", max_iter=2000, random_state=random_seed),
            {"C": [0.1, 1.0, 10.0]},
        ),
        "random_forest": (
            RandomForestClassifier(
                class_weight="balanced",
                n_estimators=200,
                n_jobs=-1,
                random_state=random_seed,
            ),
            {"max_depth": [None, 12], "min_samples_leaf": [1, 3]},
        ),
        "gradient_boosting": (
            GradientBoostingClassifier(random_state=random_seed),
            {
                "n_estimators": [100, 200],
                "learning_rate": [0.05, 0.1],
                "max_depth": [2, 3],
            },
        ),
    }
    return {
        name: GridSearchCV(
            estimator=model,
            param_grid=grid,
            scoring="roc_auc",
            cv=cv,
            n_jobs=-1,
            refit=True,
            return_train_score=False,
        )
        for name, (model, grid) in models_and_grids.items()
    }


def _classification_metrics(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    predictions = (probabilities >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
    }


def _cv_summary(search: GridSearchCV) -> dict[str, float]:
    best_index = int(search.best_index_)
    results = search.cv_results_
    return {
        "best_cv_roc_auc": float(results["mean_test_score"][best_index]),
        "cv_roc_auc_std": float(results["std_test_score"][best_index]),
    }


def train_model_suite(
    train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    preprocessor: Any,
    *,
    target_column: str = TARGET_COLUMN,
    random_seed: int = RANDOM_SEED,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    if target_column not in train_df.columns or target_column not in validation_df.columns:
        raise ValueError(f"Both datasets must contain target column: {target_column}")

    x_train = preprocessor.transform(train_df.drop(columns=[target_column]))
    x_validation = preprocessor.transform(validation_df.drop(columns=[target_column]))
    y_train = train_df[target_column].astype(int)
    y_validation = validation_df[target_column].astype(int)
    sample_weights = _balanced_sample_weights(y_train)

    output_path = Path(artifact_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    searches = build_model_searches(random_seed)
    model_metadata: dict[str, Any] = {}
    for name, search in searches.items():
        search.fit(x_train, y_train, sample_weight=sample_weights)
        probabilities = search.best_estimator_.predict_proba(x_validation)[:, 1]
        model_metadata[name] = {
            "best_parameters": search.best_params_,
            "cross_validation": _cv_summary(search),
            "validation_metrics": _classification_metrics(y_validation, probabilities),
            "class_weighting": "balanced sample weights",
            "calibration": {
                "implemented": False,
                "brier_score_recorded": True,
                "decision": "defer to Phase 5 evaluation",
            },
        }
        joblib.dump(search.best_estimator_, output_path / MODEL_FILENAMES[name])

    metadata = {
        "target_column": target_column,
        "positive_class": 1,
        "random_seed": random_seed,
        "training_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scikit_learn_version": sklearn.__version__,
        "preprocessing_artifact": PIPELINE_FILENAME,
        "models": model_metadata,
        "primary_model": None,
        "risk_thresholds": None,
    }
    (output_path / TRAINING_METADATA_FILENAME).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _balanced_sample_weights(y_train: pd.Series) -> np.ndarray:
    counts = y_train.value_counts().to_dict()
    total = len(y_train)
    classes = len(counts)
    weights = {label: total / (classes * count) for label, count in counts.items()}
    return y_train.map(weights).to_numpy(dtype=float)


def write_training_report(metadata: dict[str, Any], path: str | Path = DEFAULT_TRAINING_REPORT) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 4 Model Training Report",
        "",
        "Three required classifiers were tuned on the Phase 3 training split using three-fold stratified cross-validation scored by ROC-AUC.",
        "Validation metrics below are measured on the held-out validation split. The test split remains untouched for Phase 5 evaluation.",
        "",
        f"- Random seed: `{metadata['random_seed']}`",
        f"- scikit-learn: `{metadata['scikit_learn_version']}`",
        "- Class imbalance: balanced sample weights were passed to each estimator during fitting.",
        "- Probability calibration: not applied in Phase 4; Brier scores are recorded for Phase 5 assessment.",
        "",
        "| Model | CV ROC-AUC | CV std | Validation ROC-AUC | F1 | Recall | Brier |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, details in metadata["models"].items():
        cv = details["cross_validation"]
        metrics = details["validation_metrics"]
        lines.append(
            f"| `{name}` | {cv['best_cv_roc_auc']:.4f} | {cv['cv_roc_auc_std']:.4f} | "
            f"{metrics['roc_auc']:.4f} | {metrics['f1']:.4f} | {metrics['recall']:.4f} | {metrics['brier_score']:.4f} |"
        )
    lines.extend(["", "Primary model selection and risk thresholds are intentionally deferred to Phase 5.", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")


def run_phase4(
    processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
    report_path: str | Path = DEFAULT_TRAINING_REPORT,
    random_seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    processed_path = Path(processed_dir)
    artifact_path = Path(artifact_dir)
    preprocessor = joblib.load(artifact_path / PIPELINE_FILENAME)
    train_df = pd.read_csv(processed_path / "train.csv")
    validation_df = pd.read_csv(processed_path / "validation.csv")
    metadata = train_model_suite(
        train_df,
        validation_df,
        preprocessor,
        artifact_dir=artifact_path,
        random_seed=random_seed,
    )
    write_training_report(metadata, report_path)
    return metadata


if __name__ == "__main__":
    print(json.dumps(run_phase4(), indent=2))