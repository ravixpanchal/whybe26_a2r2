import numpy as np
import pandas as pd

from ml.training.train_models import _balanced_sample_weights, _classification_metrics, build_model_searches


def test_phase4_builds_the_required_three_model_searches():
    searches = build_model_searches(random_seed=11)

    assert list(searches) == ["logistic_regression", "random_forest", "gradient_boosting"]
    assert all(search.scoring == "roc_auc" for search in searches.values())
    assert all(search.cv.random_state == 11 for search in searches.values())


def test_phase4_metrics_and_balanced_weights_are_bounded():
    target = pd.Series([0, 0, 0, 1])
    probabilities = np.array([0.1, 0.2, 0.6, 0.9])

    metrics = _classification_metrics(target, probabilities)
    weights = _balanced_sample_weights(target)

    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc", "log_loss", "brier_score"}
    assert all(0.0 <= value <= 1.0 for key, value in metrics.items() if key not in {"log_loss"})
    assert metrics["log_loss"] >= 0.0
    assert weights[3] > weights[0]