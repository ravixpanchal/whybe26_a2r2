"""Small helpers shared by the required Phase 5 wrapper scripts."""

from __future__ import annotations

from pathlib import Path

try:
    from .pipeline import evaluate_models
except ImportError:  # Direct execution from this directory
    from pipeline import evaluate_models


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_reports(run_cv: bool = False) -> Path:
    root = project_root()
    reports = root / "ml" / "reports"
    required = reports / "evaluation_summary.md"
    if not required.exists():
        evaluate_models(root, reports, run_cv=run_cv)
    return reports
