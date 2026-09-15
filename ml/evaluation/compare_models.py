"""Generate the complete comparison and model-selection report."""

from pathlib import Path
try:
    from .pipeline import evaluate_models
except ImportError:
    from pipeline import evaluate_models


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    reports = root / "ml" / "reports"
    # Comparison is the authoritative entry point and includes five-fold CV.
    evaluate_models(root, reports, run_cv=True)
    print(reports / "evaluation_summary.md")


if __name__ == "__main__":
    main()
