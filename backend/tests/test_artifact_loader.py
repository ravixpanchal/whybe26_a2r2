import json
from pathlib import Path

import joblib
import pytest

from app.config import Settings
from app.core.exceptions import ArtifactLoadError
from app.services.ml_artifact_loader import MLArtifactLoader


class PredictableModel:
    def predict(self, rows):
        return [0 for _ in rows]


def _write_bundle(directory: Path) -> None:
    directory.mkdir()
    joblib.dump(PredictableModel(), directory / "model.pkl")
    joblib.dump({"transform": "test"}, directory / "preprocessing_pipeline.joblib")
    (directory / "model_metadata.json").write_text(
        json.dumps({"target": "defaulted", "feature_count": 1, "features": ["feature"]}),
        encoding="utf-8",
    )


def test_loader_loads_bundle_once(tmp_path: Path) -> None:
    _write_bundle(tmp_path)
    loader = MLArtifactLoader(
        Settings(ARTIFACT_DIRECTORY=tmp_path, PREPROCESSING_MODE="separate")
    )

    first = loader.load()
    second = loader.load()

    assert first is second
    assert first.preprocessing == {"transform": "test"}
    assert first.metadata["target"] == "defaulted"


def test_loader_reports_missing_model(tmp_path: Path) -> None:
    loader = MLArtifactLoader(
        Settings(ARTIFACT_DIRECTORY=tmp_path, PREPROCESSING_MODE="embedded")
    )

    with pytest.raises(ArtifactLoadError, match="Required ML artifact is missing"):
        loader.load()
