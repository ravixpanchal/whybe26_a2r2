"""Export a loadable soft-voting ensemble into portable component artifacts.

This command intentionally refuses to overwrite an existing output directory.
It must be run in the training-compatible environment where the source
``model.pkl`` can be deserialized.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
OUTPUT_DIR = ARTIFACT_DIR / "portable"


def export(source: Path = ARTIFACT_DIR / "model.pkl", output: Path = OUTPUT_DIR) -> None:
    if not source.is_file():
        raise FileNotFoundError(
            f"Source model is missing: {source}. Copy the original model.pkl "
            "from the training machine; do not retrain or substitute component artifacts."
        )
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing portable artifact directory: {output}"
        )
    model = joblib.load(source)
    if not hasattr(model, "named_estimators_") or getattr(model, "voting", None) != "soft":
        raise TypeError("Source model must be a fitted soft-voting ensemble")
    if not hasattr(model, "classes_") or not hasattr(model, "estimators"):
        raise TypeError("Source model is not a complete fitted VotingClassifier")

    preprocessing_path = ARTIFACT_DIR / "preprocessing_pipeline.joblib"
    fitted_estimators = list(model.named_estimators_.items())
    pipeline_estimators = [
        estimator for _, estimator in fitted_estimators if isinstance(estimator, Pipeline)
    ]
    if pipeline_estimators:
        if len(pipeline_estimators) != len(fitted_estimators):
            raise TypeError("Source ensemble mixes pipeline and non-pipeline estimators")
        preprocessors = [
            estimator.named_steps.get("preprocessor") for estimator in pipeline_estimators
        ]
        if any(preprocessor is None for preprocessor in preprocessors):
            raise TypeError("Source estimator pipeline is missing a preprocessor step")
        preprocessing = preprocessors[0]
        classifiers = [
            estimator.named_steps.get("classifier") for estimator in pipeline_estimators
        ]
        if any(classifier is None for classifier in classifiers):
            raise TypeError("Source estimator pipeline is missing a classifier step")
        estimator_items = [
            (name, classifier)
            for (name, _), classifier in zip(fitted_estimators, classifiers, strict=True)
        ]
    else:
        preprocessing = joblib.load(preprocessing_path)
        estimator_items = fitted_estimators

    if len(estimator_items) != len(model.estimators):
        raise TypeError("Source ensemble estimator count does not match its fitted estimators")

    output.mkdir(parents=True)
    joblib.dump(preprocessing, output / "preprocessing_pipeline.joblib")

    sklearn_estimators: dict[str, str] = {}
    xgboost_name: str | None = None
    estimator_order: list[str] = []
    for name, estimator in estimator_items:
        estimator_order.append(name)
        if estimator.__class__.__module__.startswith("xgboost"):
            xgboost_name = name
            estimator.save_model(output / "estimator_xgboost.json")
        else:
            filename = f"estimator_{name}.joblib"
            joblib.dump(estimator, output / filename)
            sklearn_estimators[name] = filename

    weights = model.weights if model.weights is not None else [1] * len(model.estimators)
    manifest: dict[str, Any] = {
        "format": "credilens_portable_soft_voting_v1",
        "preprocessing": "preprocessing_pipeline.joblib",
        "sklearn_estimators": sklearn_estimators,
        "estimator_order": estimator_order,
        "weights": list(weights),
        "classes": model.classes_.tolist(),
    }
    if xgboost_name is not None:
        manifest["xgboost_estimator_name"] = xgboost_name
        manifest["xgboost_estimator"] = "estimator_xgboost.json"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    export()
