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

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
OUTPUT_DIR = ARTIFACT_DIR / "portable"


def export(source: Path = ARTIFACT_DIR / "model.pkl", output: Path = OUTPUT_DIR) -> None:
    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing portable artifact directory: {output}"
        )
    model = joblib.load(source)
    if not hasattr(model, "named_estimators_") or getattr(model, "voting", None) != "soft":
        raise TypeError("Source model must be a fitted soft-voting ensemble")

    preprocessing_path = ARTIFACT_DIR / "preprocessing_pipeline.joblib"
    preprocessing = joblib.load(preprocessing_path)
    output.mkdir(parents=True)
    joblib.dump(preprocessing, output / "preprocessing_pipeline.joblib")

    sklearn_estimators: dict[str, str] = {}
    xgboost_name: str | None = None
    for name, estimator in model.named_estimators_.items():
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
        "weights": list(weights),
        "classes": model.classes_.tolist(),
    }
    if xgboost_name is not None:
        manifest["xgboost_estimator_name"] = xgboost_name
        manifest["xgboost_estimator"] = "estimator_xgboost.json"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    export()
