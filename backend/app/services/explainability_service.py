from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.schemas.assessment import FeatureContribution


def explain_prediction(
    model: Any, rows: pd.DataFrame, feature_mapping: dict[str, str], limit: int = 10
) -> list[FeatureContribution]:
    """Return local, model-specific contributions for the validated ensemble.

    The portable bundle's Logistic Regression component supplies coefficients
    in transformed space. Contributions are aggregated back to source fields.
    They are directional explanations, not causal effects.
    """
    transformed = model.transform(rows)
    estimator = model.estimators.get("logistic_regression")
    if estimator is None or not hasattr(estimator, "coef_"):
        raise ValueError("Portable bundle has no explainable Logistic Regression component")
    coefficients = np.asarray(estimator.coef_, dtype=float)[0]
    values = np.asarray(transformed)[0]
    if len(coefficients) != len(values):
        raise ValueError("Explanation coefficients do not match transformed features")
    names = list(feature_mapping)
    if len(names) != len(values):
        raise ValueError("Explanation feature mapping does not match transformed values")
    grouped: dict[str, float] = {}
    for name, value, coefficient in zip(names, values, coefficients):
        source = feature_mapping[name]
        grouped[source] = grouped.get(source, 0.0) + float(value * coefficient)
    ranked = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]
    return [
        FeatureContribution(
            feature=name,
            contribution=round(value, 6),
            direction="risk_increasing" if value >= 0 else "risk_reducing",
        )
        for name, value in ranked
    ]
