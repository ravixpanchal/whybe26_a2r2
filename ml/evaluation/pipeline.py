"""Train-only model comparison and final evaluation for Phase 5.

The functions in this module deliberately keep the validation and test sets
outside model fitting.  Validation is used for model/threshold selection and
the test set is read only for the final, one-time estimate.
"""

from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

TARGET = "defaulted"
RANDOM_STATE = 42
MODEL_NAMES = ("logistic_regression", "random_forest", "xgboost", "soft_voting")


@dataclass
class ThresholdSelection:
    threshold: float
    objective: str
    validation_f1: float
    validation_balanced_accuracy: float


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value)!r}")


def load_splits(root: str | Path) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    """Load the supplied processed splits without changing their contents."""
    processed = Path(root) / "processed"
    result: dict[str, tuple[pd.DataFrame, pd.Series]] = {}
    for split in ("train", "validation", "test"):
        frame = pd.read_csv(processed / f"{split}.csv")
        if TARGET not in frame:
            raise ValueError(f"{TARGET!r} is missing from {split}.csv")
        result[split] = (frame.drop(columns=TARGET), frame[TARGET].astype(int))
    feature_sets = [set(value[0].columns) for value in result.values()]
    if any(features != feature_sets[0] for features in feature_sets[1:]):
        raise ValueError("Train, validation, and test feature columns differ")
    return result


def make_preprocessor(
    numeric_features: list[str], categorical_features: list[str]
) -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, numeric_features),
            ("categorical", categorical, categorical_features),
        ],
        remainder="drop",
    )


def build_model_specs(
    X: pd.DataFrame, y: pd.Series, random_state: int = RANDOM_STATE
) -> dict[str, Pipeline | VotingClassifier]:
    """Build independent pipelines with identical preprocessing and seed."""
    categorical = X.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    numeric = [column for column in X.columns if column not in categorical]
    positive_weight = float((y == 0).sum() / max((y == 1).sum(), 1))

    logistic = Pipeline(
        [
            ("preprocessor", make_preprocessor(numeric, categorical)),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=random_state,
                ),
            ),
        ]
    )
    forest = Pipeline(
        [
            ("preprocessor", make_preprocessor(numeric, categorical)),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=400,
                    class_weight="balanced_subsample",
                    max_features="sqrt",
                    min_samples_leaf=2,
                    n_jobs=-1,
                    random_state=random_state,
                ),
            ),
        ]
    )
    xgboost = Pipeline(
        [
            ("preprocessor", make_preprocessor(numeric, categorical)),
            (
                "classifier",
                XGBClassifier(
                    colsample_bytree=0.85,
                    eval_metric="logloss",
                    learning_rate=0.05,
                    max_depth=5,
                    n_estimators=350,
                    n_jobs=2,
                    objective="binary:logistic",
                    reg_lambda=2.0,
                    scale_pos_weight=positive_weight,
                    subsample=0.85,
                    tree_method="hist",
                    random_state=random_state,
                ),
            ),
        ]
    )
    ensemble = VotingClassifier(
        estimators=[
            ("logistic_regression", clone(logistic)),
            ("random_forest", clone(forest)),
            ("xgboost", clone(xgboost)),
        ],
        voting="soft",
        weights=[1, 1, 1],
        n_jobs=1,
        flatten_transform=True,
    )
    return {
        "logistic_regression": logistic,
        "random_forest": forest,
        "xgboost": xgboost,
        "soft_voting": ensemble,
    }


def classification_metrics(
    y_true: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float | int]:
    """Calculate thresholded and ranking metrics from positive-class scores."""
    y = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    predictions = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {
        "n": int(len(y)),
        "positive_rate": float(y.mean()),
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "average_precision": float(average_precision_score(y, scores)),
        "log_loss": float(log_loss(y, scores, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y, scores)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def select_threshold(
    y_validation: pd.Series, probabilities: np.ndarray, objective: str = "f1"
) -> ThresholdSelection:
    rows: list[dict[str, float]] = []
    for threshold in np.linspace(0.10, 0.90, 81):
        metrics = classification_metrics(y_validation, probabilities, float(threshold))
        rows.append(
            {
                "threshold": float(threshold),
                "f1": float(metrics["f1"]),
                "balanced_accuracy": float(metrics["balanced_accuracy"]),
                "precision": float(metrics["precision"]),
                "recall": float(metrics["recall"]),
            }
        )
    table = pd.DataFrame(rows)
    if objective not in {"f1", "balanced_accuracy"}:
        raise ValueError("objective must be f1 or balanced_accuracy")
    best = table.sort_values([objective, "threshold"], ascending=[False, True]).iloc[0]
    return ThresholdSelection(
        threshold=float(best["threshold"]),
        objective=objective,
        validation_f1=float(best["f1"]),
        validation_balanced_accuracy=float(best["balanced_accuracy"]),
    )


def cross_validate_models(
    models: dict[str, Any], X: pd.DataFrame, y: pd.Series, folds: int = 5
) -> pd.DataFrame:
    """Return fold-level metrics; every fold fits preprocessing on its fold only."""
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    rows: list[dict[str, float | int | str]] = []
    for name, estimator in models.items():
        if name == "soft_voting":
            # The ensemble is evaluated separately from the already cloned bases.
            pass
        for fold, (train_index, valid_index) in enumerate(cv.split(X, y), start=1):
            fitted = clone(estimator).fit(X.iloc[train_index], y.iloc[train_index])
            scores = fitted.predict_proba(X.iloc[valid_index])[:, 1]
            metrics = classification_metrics(y.iloc[valid_index], scores)
            rows.append({"model": name, "fold": fold, **metrics})
    return pd.DataFrame(rows)


def _fit_and_predict(
    models: dict[str, Any],
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_eval: pd.DataFrame,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    fitted: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    for name, estimator in models.items():
        fitted[name] = estimator.fit(X_train, y_train)
        predictions[name] = fitted[name].predict_proba(X_eval)[:, 1]
    return fitted, predictions


def evaluate_models(
    root: str | Path,
    output_dir: str | Path,
    threshold_objective: str = "f1",
    run_cv: bool = True,
) -> dict[str, Any]:
    """Run the complete train/validation/test evaluation and write artifacts."""
    root = Path(root)
    output = Path(output_dir)
    plots = output / "plots"
    output.mkdir(parents=True, exist_ok=True)
    plots.mkdir(parents=True, exist_ok=True)
    splits = load_splits(root)
    X_train, y_train = splits["train"]
    X_validation, y_validation = splits["validation"]
    X_test, y_test = splits["test"]
    models = build_model_specs(X_train, y_train)
    fitted, validation_scores = _fit_and_predict(models, X_train, y_train, X_validation)
    test_scores = {name: model.predict_proba(X_test)[:, 1] for name, model in fitted.items()}

    threshold_rows: list[dict[str, Any]] = []
    selected: dict[str, ThresholdSelection] = {}
    for name in MODEL_NAMES:
        selection = select_threshold(y_validation, validation_scores[name], threshold_objective)
        selected[name] = selection
        for threshold in np.linspace(0.10, 0.90, 81):
            metric = classification_metrics(y_validation, validation_scores[name], float(threshold))
            threshold_rows.append({"model": name, **metric})
    pd.DataFrame(threshold_rows).to_csv(output / "threshold_analysis.csv", index=False)

    validation_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    for name in MODEL_NAMES:
        threshold = selected[name].threshold
        validation_rows.append(
            {"model": name, "split": "validation", **classification_metrics(y_validation, validation_scores[name], threshold)}
        )
        test_rows.append(
            {"model": name, "split": "test", **classification_metrics(y_test, test_scores[name], threshold)}
        )
        prediction_frames.extend(
            [
                pd.DataFrame({"split": "validation", "model": name, "y_true": y_validation, "probability": validation_scores[name], "prediction": (validation_scores[name] >= threshold).astype(int)}),
                pd.DataFrame({"split": "test", "model": name, "y_true": y_test, "probability": test_scores[name], "prediction": (test_scores[name] >= threshold).astype(int)}),
            ]
        )
    validation_metrics = pd.DataFrame(validation_rows)
    test_metrics = pd.DataFrame(test_rows)
    validation_metrics.to_csv(output / "validation_metrics.csv", index=False)
    test_metrics.to_csv(output / "test_metrics.csv", index=False)
    pd.concat(prediction_frames, ignore_index=True).to_csv(output / "predictions.csv", index=False)
    validation_metrics.to_json(output / "validation_metrics.json", orient="records", indent=2)
    test_metrics.to_json(output / "test_metrics.json", orient="records", indent=2)

    cv_results = cross_validate_models(models, X_train, y_train) if run_cv else pd.DataFrame()
    if not cv_results.empty:
        cv_results.to_csv(output / "cross_validation_results.csv", index=False)
        cv_results.groupby("model")[["roc_auc", "average_precision", "log_loss", "f1", "balanced_accuracy"]].agg(["mean", "std"]).to_csv(output / "cross_validation_summary.csv")
    elif not run_cv:
        for stale in ("cross_validation_results.csv", "cross_validation_summary.csv"):
            (output / stale).unlink(missing_ok=True)

    # Model selection is based on validation ROC AUC, with F1 threshold analysis
    # reported separately. The selected model is still the train-only fit.
    ranking = validation_metrics.sort_values(["roc_auc", "average_precision"], ascending=False)
    selected_name = str(ranking.iloc[0]["model"])
    save_selected_model(fitted[selected_name], output / "model.pkl", output / "model_metadata.json", selected_name, selected[selected_name], X_train, root)

    _write_plots(
        plots,
        y_validation,
        y_test,
        validation_scores,
        test_scores,
        selected,
        selected_name,
    )
    _write_reports(output, validation_metrics, test_metrics, cv_results, selected_name, selected, root)
    _write_named_reports(
        output,
        validation_metrics,
        test_metrics,
        threshold_rows,
        validation_scores,
        y_validation,
    )
    return {
        "selected_model": selected_name,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "cv_results": cv_results,
        "thresholds": selected,
    }


def save_selected_model(
    model: Any,
    model_path: str | Path,
    metadata_path: str | Path,
    model_name: str,
    threshold: ThresholdSelection,
    X_train: pd.DataFrame,
    root: str | Path,
) -> None:
    """Persist the selected train-only pipeline and reproducibility metadata."""
    model_path = Path(model_path)
    metadata_path = Path(metadata_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path, compress=3)
    packages = {}
    for package in ("numpy", "pandas", "scikit-learn", "xgboost", "joblib", "matplotlib"):
        try:
            packages[package] = version(package)
        except Exception:
            packages[package] = "unavailable"
    metadata = {
        "model_name": model_name,
        "target": TARGET,
        "feature_count": int(X_train.shape[1]),
        "features": X_train.columns.tolist(),
        "training_rows": int(len(X_train)),
        "training_source": ["processed/train.csv"],
        "selection_source": "processed/validation.csv (ROC-AUC model selection; F1 threshold selection)",
        "test_source": "processed/test.csv (untouched until final evaluation)",
        "threshold": asdict(threshold),
        "random_state": RANDOM_STATE,
        "data_root": str(Path(root).resolve()),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "library_versions": packages,
        "caveat_existing_model": (
            "The repository-root model.pkl was trained on train+validation and is not "
            "used for independent comparison or threshold selection."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, default=_json_default) + "\n", encoding="utf-8")


def _write_plots(
    plots: Path,
    y_validation: pd.Series,
    y_test: pd.Series,
    validation_scores: dict[str, np.ndarray],
    test_scores: dict[str, np.ndarray],
    thresholds: dict[str, ThresholdSelection],
    selected_name: str,
) -> None:
    from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for name, scores in validation_scores.items():
        RocCurveDisplay.from_predictions(y_validation, scores, name=name, ax=axes[0])
        PrecisionRecallDisplay.from_predictions(y_validation, scores, name=name, ax=axes[1])
    axes[0].set_title("Validation ROC curves")
    axes[1].set_title("Validation precision-recall curves")
    fig.tight_layout()
    fig.savefig(plots / "validation_roc_pr.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    for name, scores in test_scores.items():
        RocCurveDisplay.from_predictions(y_test, scores, name=name, ax=ax)
    ax.set_title("Untouched test ROC curves")
    fig.tight_layout()
    fig.savefig(plots / "test_roc.png", dpi=140)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    for name, scores in validation_scores.items():
        fraction, mean_predicted = calibration_curve(y_validation, scores, n_bins=10, strategy="quantile")
        ax.plot(mean_predicted, fraction, marker="o", label=name)
    ax.plot([0, 1], [0, 1], "k--", label="perfect calibration")
    ax.set(xlabel="Mean predicted probability", ylabel="Fraction positive", title="Validation calibration")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots / "validation_calibration.png", dpi=140)
    plt.close(fig)

    cm = confusion_matrix(y_test, (test_scores[selected_name] >= thresholds[selected_name].threshold).astype(int), labels=[0, 1])
    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(cm, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set(xticks=[0, 1], yticks=[0, 1], xlabel="Predicted", ylabel="Actual", title=f"Test confusion matrix ({selected_name})")
    for (row, col), value in np.ndenumerate(cm):
        ax.text(col, row, str(value), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(plots / "test_confusion_matrix.png", dpi=140)
    plt.close(fig)


def _write_reports(
    output: Path,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    cv: pd.DataFrame,
    selected_name: str,
    thresholds: dict[str, ThresholdSelection],
    root: Path,
) -> None:
    comparison = validation.merge(test, on="model", suffixes=("_validation", "_test"))
    comparison.to_csv(output / "model_comparison.csv", index=False)
    summary = comparison[["model", "roc_auc_validation", "average_precision_validation", "log_loss_validation", "f1_validation", "roc_auc_test", "average_precision_test", "log_loss_test", "f1_test"]]
    summary.to_json(output / "model_comparison.json", orient="records", indent=2)

    report_lines = [
        "# Phase 5 model evaluation",
        "",
        "## Protocol",
        "- All four candidates were fit independently on `processed/train.csv` only.",
        "- `processed/validation.csv` was used for ROC-AUC model selection and F1 threshold analysis.",
        "- `processed/test.csv` was untouched until the final evaluation below.",
        f"- Selected primary model: **{selected_name}** (highest validation ROC-AUC).",
        "",
        "The repository-root `model.pkl` is not used for this comparison: its metadata shows it was fit on train + validation. Therefore validation is not independent for thresholding/model selection for that existing artifact; this report uses a new train-only fit for a fair comparison.",
        "",
        "## Validation and test metrics",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Thresholds",
        "",
        pd.DataFrame([{"model": name, **asdict(value)} for name, value in thresholds.items()]).to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Cross-validation",
        "",
        ("Five-fold stratified CV was run on the training split. Fold-level results are in `cross_validation_results.csv`."
         if not cv.empty else "Cross-validation was not run."),
        "",
        "## Reproducibility",
        f"- Data root: `{root.resolve()}`",
        "- Seed: 42",
        "- Plots are in `plots/`; predictions and machine-readable metrics are CSV/JSON.",
    ]
    (output / "evaluation_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    error_lines = [
        "# Error analysis",
        "",
        f"Error analysis uses the selected **{selected_name}** model and its validation-selected threshold.",
        "The complete row-level predictions are in `predictions.csv`; inspect false positives and false negatives there.",
        "",
        "Error counts and rates are reported in `test_metrics.csv` (`fp`, `fn`, `precision`, and `recall`).",
        "Because the test set is used only once for final evaluation, no test-derived tuning or subgroup selection was performed.",
    ]
    (output / "error_analysis.md").write_text("\n".join(error_lines) + "\n", encoding="utf-8")


def _write_named_reports(
    output: Path,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    threshold_rows: list[dict[str, Any]],
    validation_scores: dict[str, np.ndarray],
    y_validation: pd.Series,
) -> None:
    """Write the per-model and analysis filenames required by the deliverable."""
    report_names = {
        "logistic_regression": "logistic_regression_metrics.json",
        "random_forest": "random_forest_metrics.json",
        "xgboost": "xgboost_metrics.json",
        "soft_voting": "ensemble_metrics.json",
    }
    for name in MODEL_NAMES:
        validation_row = validation.loc[validation["model"] == name].iloc[0].to_dict()
        test_row = test.loc[test["model"] == name].iloc[0].to_dict()
        payload = {
            "model": name,
            "validation": validation_row,
            "test": test_row,
            "protocol": {
                "training_source": "processed/train.csv",
                "selection_source": "processed/validation.csv",
                "test_source": "processed/test.csv (untouched until final evaluation)",
            },
        }
        (output / report_names[name]).write_text(
            json.dumps(payload, indent=2, default=_json_default) + "\n",
            encoding="utf-8",
        )

    calibration_rows = []
    for name, scores in validation_scores.items():
        fraction, mean_predicted = calibration_curve(
            y_validation, scores, n_bins=10, strategy="quantile"
        )
        calibration_rows.append(
            {
                "model": name,
                "brier_score": float(brier_score_loss(y_validation, scores)),
                "calibration_bins": [
                    {"mean_predicted": float(predicted), "fraction_positive": float(actual)}
                    for predicted, actual in zip(mean_predicted, fraction)
                ],
            }
        )
    (output / "calibration_report.json").write_text(
        json.dumps(calibration_rows, indent=2) + "\n", encoding="utf-8"
    )
    threshold_payload = {
        "objective": "f1",
        "grid": threshold_rows,
        "selection_note": "Thresholds were selected on validation only; test labels were not used.",
    }
    (output / "threshold_analysis.json").write_text(
        json.dumps(threshold_payload, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    (output / "evaluation_summary.md").write_text(
        (output / "evaluation_report.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
