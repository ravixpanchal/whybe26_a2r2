from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.schemas.assessment import BorrowerInput, ReliabilityInfo

DISCLAIMER = (
    "This is a rule-based reliability indicator, not calibrated statistical "
    "confidence and not a lending decision."
)


def assess_reliability(
    borrower: BorrowerInput,
    rows: pd.DataFrame,
    probability: float,
    category_threshold: float,
    feature_metadata: dict[str, Any],
    component_probabilities: dict[str, np.ndarray],
) -> ReliabilityInfo:
    score = 100
    reasons: list[str] = []
    values = borrower.model_dump()
    missing = [name for name, value in values.items() if value is None]
    if missing:
        score -= min(30, len(missing) * 5)
        reasons.append(f"{len(missing)} feature values will be imputed")

    numeric_ranges = feature_metadata.get("training_ranges", {})
    for name, bounds in numeric_ranges.items():
        value = values.get(name)
        if value is not None and isinstance(bounds, dict):
            if value < bounds.get("min", value) or value > bounds.get("max", value):
                score -= 15
                reasons.append(f"{name} is outside the training range")

    known_categories = feature_metadata.get("known_categories", {})
    for name, categories in known_categories.items():
        value = values.get(name)
        if value is not None and value not in categories:
            score -= 15
            reasons.append(f"{name} is an unseen category")

    if abs(probability - category_threshold) <= 0.05:
        score -= 20
        reasons.append("prediction is close to the risk threshold")

    if component_probabilities:
        component_classes = [
            int(np.argmax(probabilities[0]))
            for probabilities in component_probabilities.values()
        ]
        if len(set(component_classes)) > 1:
            score -= 10
            reasons.append("ensemble components disagree on the predicted class")

    score = max(0, min(100, score))
    level = "high" if score >= 80 else "medium" if score >= 50 else "low"
    if not reasons:
        reasons.append("complete in-range input and no threshold or agreement warning")
    return ReliabilityInfo(level=level, score=score, reasons=reasons, disclaimer=DISCLAIMER)
