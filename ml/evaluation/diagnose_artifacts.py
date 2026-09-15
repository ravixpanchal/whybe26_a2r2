"""Produce read-only evidence about the ML artifact and runtime state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
from typing import Any

EXPECTED_FILES = (
    "model.pkl",
    "model_metadata.json",
    "preprocessing_pipeline.joblib",
    "feature_metadata.json",
    "training_metadata.json",
    "model_logistic_regression.joblib",
    "model_random_forest.joblib",
    "model_gradient_boosting.joblib",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in ("joblib", "numpy", "pandas", "scikit-learn", "xgboost", "fastapi"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unavailable"
    return versions


def _json_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "missing"}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "valid", "type": type(value).__name__}


def collect_diagnostics(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    files: dict[str, Any] = {}
    for relative in EXPECTED_FILES:
        path = root / relative
        if path.is_file():
            files[relative] = {
                "status": "present",
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        else:
            files[relative] = {"status": "missing"}

    manifest_path = root / "portable" / "manifest.json"
    portable: dict[str, Any] = {"manifest": _json_status(manifest_path)}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            references = [manifest["preprocessing"]]
            references.extend(manifest.get("sklearn_estimators", {}).values())
            if manifest.get("xgboost_estimator"):
                references.append(manifest["xgboost_estimator"])
            portable["referenced_files"] = {
                reference: (manifest_path.parent / reference).is_file()
                for reference in references
            }
            portable["estimator_order"] = manifest.get("estimator_order")
            portable["weights"] = manifest.get("weights")
        except (OSError, json.JSONDecodeError, KeyError, AttributeError) as exc:
            portable["validation_error"] = f"{type(exc).__name__}: {exc}"

    model_path = root / "model.pkl"
    model_loading: dict[str, Any]
    if not model_path.is_file():
        model_loading = {"status": "not_attempted", "reason": "model.pkl is missing"}
    else:
        try:
            import joblib

            model = joblib.load(model_path)
            model_loading = {
                "status": "loaded",
                "type": f"{type(model).__module__}.{type(model).__name__}",
                "voting": getattr(model, "voting", None),
                "estimators": list(getattr(model, "named_estimators_", {})),
            }
        except Exception as exc:
            model_loading = {
                "status": "failed",
                "error": f"{type(exc).__module__}.{type(exc).__name__}: {exc}",
            }

    return {
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": _package_versions(),
        },
        "artifact_directory": str(root.resolve()),
        "files": files,
        "metadata": {
            name: _json_status(root / name)
            for name in ("model_metadata.json", "feature_metadata.json", "training_metadata.json")
        },
        "model_loading": model_loading,
        "portable_bundle": portable,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path, nargs="?", default=Path("ml/artifacts"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(collect_diagnostics(args.artifact_dir), indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(result + "\n", encoding="utf-8")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
