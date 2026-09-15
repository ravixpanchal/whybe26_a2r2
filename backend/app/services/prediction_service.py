from __future__ import annotations

from typing import Any

import numpy as np

from app.core.exceptions import ArtifactLoadError
from app.schemas.assessment import (
    AssessmentResponse,
    BorrowerInput,
    ModelComparison,
    ModelPrediction,
)
from app.services.ml_artifact_loader import LoadedArtifacts
from app.services.preprocessing_service import borrower_to_frame
from app.services.explainability_service import explain_prediction
from app.services.reliability_service import assess_reliability

VALIDATED_RISK_THRESHOLD = 0.59


def predict_assessment(
    artifacts: LoadedArtifacts, borrower: BorrowerInput
) -> AssessmentResponse:
    metadata = artifacts.metadata
    feature_order = metadata.get("features")
    if not isinstance(feature_order, list) or not all(
        isinstance(feature, str) for feature in feature_order
    ):
        raise ArtifactLoadError("Loaded model metadata has no valid feature order")

    rows = borrower_to_frame(borrower, feature_order)
    model = artifacts.model
    try:
        predictions = np.asarray(model.predict(rows))
        probabilities = np.asarray(model.predict_proba(rows), dtype=float)
    except Exception as exc:
        raise ArtifactLoadError(f"Model inference failed: {exc}") from exc

    classes = np.asarray(getattr(model, "classes_", [0, 1]))
    if predictions.shape != (1,) or probabilities.shape != (1, len(classes)):
        raise ArtifactLoadError("Loaded model returned an invalid prediction shape")
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or (probabilities > 1).any():
        raise ArtifactLoadError("Loaded model returned invalid probabilities")
    try:
        positive_index = list(classes).index(1)
    except ValueError as exc:
        raise ArtifactLoadError("Loaded model does not expose positive class 1") from exc

    probability = float(probabilities[0, positive_index])
    category = "high" if probability >= VALIDATED_RISK_THRESHOLD else "low"
    predicted_class = str(predictions[0].item())
    feature_metadata = metadata.get("feature_metadata", {})
    contributions = explain_prediction(
        model,
        rows,
        feature_metadata.get("transformation_mapping", {}),
    )
    reliability = assess_reliability(
        borrower,
        rows,
        probability,
        VALIDATED_RISK_THRESHOLD,
        feature_metadata,
        model.component_predict_proba(rows),
    )
    return AssessmentResponse(
        model_comparison=ModelComparison(
            prediction=ModelPrediction(
                model_name="soft_voting_ensemble",
                predicted_class=predicted_class,
                probability=probability,
            ),
            primary_model="soft_voting_ensemble",
            compatibility_status="validated",
        ),
        risk_probability=probability,
        risk_category=category,
        class_mapping={"negative_class": 0, "positive_class": 1, "positive_class_meaning": "defaulted"},
        feature_contributions=contributions,
        reliability=reliability,
    )
