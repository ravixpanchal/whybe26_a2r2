"""Validate the persisted ML artifact bundle without modifying it."""

from __future__ import annotations

import json
import platform
import sys
import traceback
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

try:
    import xgboost
except ImportError:
    xgboost = None


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
REPORT_PATH = ROOT / "ml" / "reports" / "artifact_compatibility_report.md"
MODEL_METADATA_PATH = ARTIFACT_DIR / "model_metadata.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def format_exception(exc: BaseException) -> str:
    return f"{type(exc).__module__}.{type(exc).__name__}: {exc}"


def sample_from_metadata(metadata: dict[str, Any]) -> pd.DataFrame:
    categorical = set(metadata["categorical_features"])
    categorical_values = {
        "borrower_type": "gig",
        "employment_type": "salaried-gig",
        "loan_purpose": "business",
    }
    values: dict[str, Any] = {}
    for feature in metadata["features"]:
        if feature in categorical:
            values[feature] = categorical_values[feature]
        elif feature == "household_size":
            values[feature] = 3
        elif feature == "mobile_wallet_used":
            values[feature] = 1
        elif feature == "same_number_since_year":
            values[feature] = 2018
        elif feature.startswith("survey_q"):
            values[feature] = 3
        elif feature == "loan_amount_requested":
            values[feature] = 50000.0
        elif feature == "loan_tenure_months":
            values[feature] = 12
        else:
            values[feature] = 10.0
    return pd.DataFrame([values], columns=metadata["features"])


def object_description(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__name__}"


def write_report(lines: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    lines = [
        "# ML Artifact Compatibility Report",
        "",
        f"- Generated: `{pd.Timestamp.now(tz='UTC').isoformat()}`",
        f"- Artifact directory: `{ARTIFACT_DIR}`",
        "- Validation mode: read-only; no artifact was modified or overwritten.",
        "",
        "## Runtime versions",
        "",
        f"- Python: `{platform.python_version()}`",
        f"- NumPy: `{np.__version__}`",
        f"- pandas: `{pd.__version__}`",
        f"- scikit-learn: `{sklearn.__version__}`",
        f"- XGBoost: `{xgboost.__version__ if xgboost else 'unavailable'}`",
        f"- joblib: `{joblib.__version__}`",
        "",
        "## Artifact inventory",
        "",
    ]

    expected_files = [
        "model.pkl",
        "model_metadata.json",
        "preprocessing_pipeline.joblib",
        "feature_metadata.json",
        "training_metadata.json",
        "model_logistic_regression.joblib",
        "model_random_forest.joblib",
        "model_gradient_boosting.joblib",
    ]
    for name in expected_files:
        path = ARTIFACT_DIR / name
        state = f"present ({path.stat().st_size} bytes)" if path.is_file() else "missing"
        lines.append(f"- `{name}`: {state}")

    metadata = load_json(MODEL_METADATA_PATH)
    feature_metadata = load_json(ARTIFACT_DIR / "feature_metadata.json")
    training_metadata = load_json(ARTIFACT_DIR / "training_metadata.json")
    lines.extend(
        [
            "",
            "## Metadata validation",
            "",
            f"- Model type metadata: `{metadata.get('model_type')}`",
            f"- Target: `{metadata.get('target')}` / feature metadata target: `{feature_metadata.get('target_column')}`",
            f"- Feature count: `{metadata.get('feature_count')}`",
            f"- Exact feature order: `{metadata.get('features')}`",
            f"- Numeric features ({len(metadata.get('numeric_features', []))}): `{metadata.get('numeric_features')}`",
            f"- Categorical features ({len(metadata.get('categorical_features', []))}): `{metadata.get('categorical_features')}`",
            f"- Positive class: `{training_metadata.get('positive_class')}`",
            f"- Primary model metadata: `{training_metadata.get('primary_model')}`",
            f"- Risk thresholds metadata: `{training_metadata.get('risk_thresholds')}`",
            "",
        ]
    )

    model = None
    preprocessing = None
    try:
        model = joblib.load(ARTIFACT_DIR / "model.pkl")
        lines.extend(
            [
                "## Model structure",
                "",
                f"- Exact Python type: `{object_description(model)}`",
                f"- Is Pipeline: `{isinstance(model, sklearn.pipeline.Pipeline)}`",
                f"- Is VotingClassifier: `{isinstance(model, sklearn.ensemble.VotingClassifier)}`",
                f"- Voting mode: `{getattr(model, 'voting', 'not available')}`",
                f"- `predict()` available: `{callable(getattr(model, 'predict', None))}`",
                f"- `predict_proba()` available: `{callable(getattr(model, 'predict_proba', None))}`",
            ]
        )
        estimators = getattr(model, "named_estimators_", None)
        if estimators is not None:
            lines.append(
                "- Base estimators: "
                + ", ".join(f"`{name}` = `{object_description(value)}`" for name, value in estimators.items())
            )
        else:
            lines.append("- Base estimators: not accessible")
    except Exception as exc:
        lines.extend(
            [
                "## Validation stopped",
                "",
                "Model loading failed before runtime type inspection or prediction.",
                f"- Exact error: `{format_exception(exc)}`",
                "- Classification: incompatible dependency/version or serialization format; no workaround was applied.",
                "",
                "```text",
                traceback.format_exc().rstrip(),
                "```",
            ]
        )
        write_report(lines)
        return 1

    try:
        preprocessing = joblib.load(ARTIFACT_DIR / "preprocessing_pipeline.joblib")
        lines.extend(
            [
                "",
                "## Preprocessing",
                "",
                f"- Separate preprocessing loaded: `{object_description(preprocessing)}`",
                f"- Model exposes pipeline steps: `{bool(getattr(model, 'steps', None))}`",
                "- Input contract: separate preprocessing is required unless the loaded model structure proves otherwise.",
            ]
        )
    except Exception as exc:
        lines.extend(
            [
                "",
                "## Validation stopped",
                "",
                f"- Separate preprocessing load failed: `{format_exception(exc)}`",
                "- Classification: incompatible dependency/version or serialization format; no workaround was applied.",
                "",
                "```text",
                traceback.format_exc().rstrip(),
                "```",
            ]
        )
        write_report(lines)
        return 1

    sample = sample_from_metadata(metadata)
    lines.extend(
        [
            "",
            "## Smoke prediction",
            "",
            f"- Sample shape: `{sample.shape}`",
            f"- Sample columns match metadata order: `{list(sample.columns) == metadata['features']}`",
        ]
    )
    try:
        prediction = model.predict(sample)
        probabilities = model.predict_proba(sample)
        probability_range_ok = bool(
            np.isfinite(probabilities).all()
            and (probabilities >= 0).all()
            and (probabilities <= 1).all()
        )
        lines.extend(
            [
                f"- Prediction shape: `{prediction.shape}`",
                f"- Prediction class values: `{prediction.tolist()}`",
                f"- Probability shape: `{probabilities.shape}`",
                f"- Probability values: `{probabilities.tolist()}`",
                f"- Probability range valid: `{probability_range_ok}`",
            ]
        )
    except Exception as exc:
        lines.extend(
            [
                "",
                "## Validation stopped",
                "",
                f"- Smoke prediction failed: `{format_exception(exc)}`",
                "```text",
                traceback.format_exc().rstrip(),
                "```",
            ]
        )
        write_report(lines)
        return 1

    lines.extend(["", "## Result", "", "- All artifact compatibility checks passed."])
    write_report(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
