import json
from pathlib import Path

from ml.evaluation.diagnose_artifacts import collect_diagnostics


def test_diagnostics_report_missing_bundle_without_loading_it(tmp_path: Path) -> None:
    result = collect_diagnostics(tmp_path)

    assert result["model_loading"]["status"] == "not_attempted"
    assert result["files"]["model.pkl"]["status"] == "missing"
    assert result["metadata"]["training_metadata.json"]["status"] == "missing"


def test_diagnostics_report_hash_and_portable_references(tmp_path: Path) -> None:
    artifact = tmp_path / "model_metadata.json"
    artifact.write_text(json.dumps({"target": "defaulted"}), encoding="utf-8")
    portable = tmp_path / "portable"
    portable.mkdir()
    (portable / "preprocessing_pipeline.joblib").write_bytes(b"preprocessor")
    (portable / "manifest.json").write_text(
        json.dumps(
            {
                "preprocessing": "preprocessing_pipeline.joblib",
                "sklearn_estimators": {},
                "estimator_order": [],
                "weights": [],
            }
        ),
        encoding="utf-8",
    )

    result = collect_diagnostics(tmp_path)

    assert result["files"]["model_metadata.json"]["status"] == "present"
    assert len(result["files"]["model_metadata.json"]["sha256"]) == 64
    assert result["portable_bundle"]["referenced_files"] == {
        "preprocessing_pipeline.joblib": True
    }
