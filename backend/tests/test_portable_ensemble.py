import numpy as np
import pandas as pd

from app.services.portable_ensemble import PortableSoftVotingEnsemble


class IdentityPreprocessor:
    def transform(self, rows: pd.DataFrame) -> pd.DataFrame:
        return rows


class FixedEstimator:
    def __init__(self, probabilities: list[list[float]]) -> None:
        self.probabilities = np.asarray(probabilities)

    def predict_proba(self, rows: pd.DataFrame) -> np.ndarray:
        return np.repeat(self.probabilities, len(rows), axis=0)


def test_portable_ensemble_preserves_weighted_soft_voting() -> None:
    ensemble = PortableSoftVotingEnsemble(
        preprocessing=IdentityPreprocessor(),
        estimators={
            "logistic_regression": FixedEstimator([[0.8, 0.2]]),
            "random_forest": FixedEstimator([[0.2, 0.8]]),
        },
        weights=[1, 1],
        classes=[0, 1],
    )

    rows = pd.DataFrame([{"feature": 1}])
    probabilities = ensemble.predict_proba(rows)

    assert probabilities.shape == (1, 2)
    assert np.allclose(probabilities, [[0.5, 0.5]])
    assert ensemble.predict(rows).tolist() == [0]
