import pandas as pd

from ml.preprocessing.build_pipeline import classify_features, fit_and_save_pipeline
from ml.preprocessing.split_data import split_dataset


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "income": [float(value) for value in range(20)],
            "employment_type": ["a", "b"] * 10,
            "defaulted": [0] * 10 + [1] * 10,
        }
    )


def test_split_dataset_is_stratified_and_disjoint():
    train, validation, test, summary = split_dataset(_sample_frame(), random_seed=7)

    assert len(train) == 14
    assert len(validation) == 3
    assert len(test) == 3
    assert set(train.index).isdisjoint(validation.index)
    assert set(train.index).isdisjoint(test.index)
    assert set(validation.index).isdisjoint(test.index)
    assert summary["random_seed"] == 7
    assert all(set(frame["defaulted"]) == {0, 1} for frame in (train, validation, test))


def test_pipeline_fits_imputation_and_ignores_unknown_categories(tmp_path):
    frame = _sample_frame()
    numeric, categorical = classify_features(frame)
    assert numeric == ["income"]
    assert categorical == ["employment_type"]
    train, _, _, summary = split_dataset(frame)

    metadata = fit_and_save_pipeline(train, summary, tmp_path)
    import joblib

    pipeline = joblib.load(tmp_path / "preprocessing_pipeline.joblib")
    transformed = pipeline.transform(
        pd.DataFrame({"income": [None], "employment_type": ["unseen"]})
    )

    assert transformed.shape[1] == len(metadata["transformed_feature_names"])
    assert transformed.dtype.kind == "f"
    assert pd.notna(transformed).all()
    assert (tmp_path / "feature_metadata.json").exists()