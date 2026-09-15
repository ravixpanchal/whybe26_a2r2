"""Command-line entry point for the complete Phase 5 evaluation."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

try:
    from .pipeline import evaluate_models
except ImportError:  # Direct execution: python ml/evaluation/run_phase5.py
    from pipeline import evaluate_models


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the train/validation/test Phase 5 evaluation")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--reports", type=Path, default=None)
    parser.add_argument("--artifacts", type=Path, default=None)
    parser.add_argument("--no-cv", action="store_true", help="Skip five-fold training-only cross-validation")
    args = parser.parse_args()

    root = args.root.resolve()
    reports = (args.reports or root / "ml" / "reports").resolve()
    artifacts = (args.artifacts or root / "ml" / "artifacts").resolve()
    result = evaluate_models(root, reports, run_cv=not args.no_cv)
    artifacts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(reports / "model.pkl", artifacts / "model.pkl")
    shutil.copy2(reports / "model_metadata.json", artifacts / "model_metadata.json")
    print(f"Selected model: {result['selected_model']}")
    print(f"Reports: {reports}")
    print(f"Artifact: {artifacts / 'model.pkl'}")


if __name__ == "__main__":
    main()
