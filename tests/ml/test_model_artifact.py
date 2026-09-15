import json
from pathlib import Path

import joblib
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "ml" / "artifacts"


@pytest.mark.skipif(
    not (ARTIFACT_DIR / "model.pkl").is_file(),
    reason="received ML artifacts are not present",
)
def test_received_ensemble_matches_metadata_and_predicts() -> None:
    model = joblib.load(ARTIFACT_DIR / "model.pkl")
    metadata = json.loads((ARTIFACT_DIR / "model_metadata.json").read_text())
    rows = pd.DataFrame(
        [
            {
                feature: (
                    "gig"
                    if feature == "borrower_type"
                    else "salaried-gig"
                    if feature == "employment_type"
                    else "business"
                    if feature == "loan_purpose"
                    else 3
                    if feature == "household_size"
                    else 2018
                    if feature == "same_number_since_year"
                    else 12
                    if feature == "loan_tenure_months"
                    else 3
                    if feature.startswith("survey_q")
                    else 10.0
                )
                for feature in metadata["features"]
            }
        ],
        columns=metadata["features"],
    )

    assert type(model).__name__ == "VotingClassifier"
    assert metadata["model_type"] == "soft_voting_ensemble"
    assert metadata["target"] == "defaulted"
    assert metadata["feature_count"] == len(metadata["features"]) == 36
    assert model.voting == "soft"
    assert list(model.named_estimators_) == [
        "logistic_regression",
        "random_forest",
        "xgboost",
    ]
    assert list(model.weights) == metadata["weights"] == [1, 1, 1]

    prediction = model.predict(rows)
    probabilities = model.predict_proba(rows)
    assert prediction.shape == (1,)
    assert probabilities.shape == (1, 2)
    assert (probabilities >= 0).all() and (probabilities <= 1).all()
