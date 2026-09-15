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
        if (
            not estimators
            or len(weights) != len(estimators)
            or not classes
            or not np.isfinite(weights).all()
            or any(weight < 0 for weight in weights)
            or sum(weights) <= 0
        ):
            raise ValueError("Portable ensemble manifest contains invalid dimensions")
        self.preprocessing = preprocessing
        self.estimators = estimators
        self.weights = np.asarray(weights, dtype=float)
        self.classes_ = np.asarray(classes)

    def predict_proba(self, rows: pd.DataFrame) -> np.ndarray:
        transformed = self.preprocessing.transform(rows)
        values = np.stack(
            [self._predict_proba_in_class_order(estimator, transformed) for estimator in self.estimators.values()],
            axis=0,
        )
        probabilities = np.average(values, axis=0, weights=self.weights)
        if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
            raise ValueError("Portable ensemble probabilities are outside [0, 1]")
        return probabilities

    def _predict_proba_in_class_order(self, estimator: Any, rows: Any) -> np.ndarray:
        probabilities = np.asarray(estimator.predict_proba(rows), dtype=float)
        estimator_classes = getattr(estimator, "classes_", self.classes_)
        if list(estimator_classes) != list(self.classes_):
            try:
                indices = [list(estimator_classes).index(value) for value in self.classes_]
            except ValueError as exc:
                raise ValueError("Portable estimator classes do not match ensemble classes") from exc
            probabilities = probabilities[:, indices]
        if probabilities.ndim != 2 or probabilities.shape[1] != len(self.classes_):
            raise ValueError("Portable estimator probabilities have an invalid shape")
        return probabilities

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(rows), axis=1)]

    def component_predict_proba(self, rows: pd.DataFrame) -> dict[str, np.ndarray]:
        transformed = self.preprocessing.transform(rows)
        return {
            name: self._predict_proba_in_class_order(estimator, transformed)
            for name, estimator in self.estimators.items()
        }

    def transform(self, rows: pd.DataFrame) -> Any:
        return self.preprocessing.transform(rows)

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "PortableSoftVotingEnsemble":
        manifest_file = Path(manifest_path)
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        root = manifest_file.parent
        preprocessing = joblib.load(root / manifest["preprocessing"])
        sklearn_estimators = manifest["sklearn_estimators"]
        estimator_order = manifest.get("estimator_order", list(sklearn_estimators))
        loaded_estimators = {
            name: joblib.load(root / sklearn_estimators[name])
            for name in estimator_order
            if name in sklearn_estimators
        }
        if manifest.get("xgboost_estimator_name"):
            import xgboost

            xgb = xgboost.XGBClassifier()
            xgb.load_model(root / manifest["xgboost_estimator"])
            loaded_estimators[manifest["xgboost_estimator_name"]] = xgb
        estimators = {
            name: loaded_estimators[name]
            for name in estimator_order
            if name in loaded_estimators
        }
        if list(estimators) != list(estimator_order):
            raise ValueError("Portable ensemble manifest does not define every estimator")
        return cls(preprocessing, estimators, manifest["weights"], manifest["classes"])
