from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class PortableSoftVotingEnsemble:
    """Loads the validated portable ensemble bundle used by the API process."""

    def __init__(
        self,
        preprocessing: Any,
        estimators: dict[str, Any],
        weights: list[float],
        classes: list[Any],
    ) -> None:
        if not estimators or len(weights) != len(estimators) or not classes:
            raise ValueError("Portable ensemble manifest contains invalid dimensions")
        self.preprocessing = preprocessing
        self.estimators = estimators
        self.weights = np.asarray(weights, dtype=float)
        self.classes_ = np.asarray(classes)

    def predict_proba(self, rows: pd.DataFrame) -> np.ndarray:
        transformed = self.preprocessing.transform(rows)
        values = np.stack(
            [np.asarray(estimator.predict_proba(transformed)) for estimator in self.estimators.values()],
            axis=0,
        )
        probabilities = np.average(values, axis=0, weights=self.weights)
        if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
            raise ValueError("Portable ensemble probabilities are outside [0, 1]")
        return probabilities

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(rows), axis=1)]

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "PortableSoftVotingEnsemble":
        manifest_file = Path(manifest_path)
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        root = manifest_file.parent
        preprocessing = joblib.load(root / manifest["preprocessing"])
        estimators = {
            name: joblib.load(root / filename)
            for name, filename in manifest["sklearn_estimators"].items()
        }
        if manifest.get("xgboost_estimator_name"):
            import xgboost

            xgb = xgboost.XGBClassifier()
            xgb.load_model(root / manifest["xgboost_estimator"])
            estimators[manifest["xgboost_estimator_name"]] = xgb
        return cls(preprocessing, estimators, manifest["weights"], manifest["classes"])
