# CrediLens AI

CrediLens AI is an explainable borrower risk assessment platform for educational and analytical decision support.

## Repository structure

- frontend/: Next.js + TypeScript application
- backend/: FastAPI API and business logic
- ml/: model training, preprocessing, and evaluation code
- data/: dataset snapshots and dataset documentation
- docs/: design and operational documentation

## Local setup

1. Create the Python environment in `backend/` and `ml/`.
2. Install backend dependencies: `pip install -r backend/requirements.txt`
3. Install ML dependencies: `pip install -r ml/requirements.txt`
4. Install frontend dependencies: `cd frontend && npm install`
5. Copy `.env.example` to `.env` and fill in the required values.

## FastAPI backend

Run the backend from the `backend/` directory:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The development server exposes `GET http://localhost:8000/api/health`.
The health endpoint is available while artifact validation is explicitly disabled
with `ARTIFACT_LOADING_REQUIRED=false`; this mode is for health/API development
only and does not enable predictions.

By default, startup validates and loads the configured model, metadata, and
separate preprocessing artifact once. The current `model.pkl` requires the ML
runtime dependencies used to create it (including XGBoost). Keep
`ARTIFACT_LOADING_REQUIRED=true` in production so missing or incompatible
artifacts fail startup clearly. `PREPROCESSING_MODE` can be `separate`,
`embedded`, or `auto`; do not change it without confirming the training-machine
artifact contract. No prediction endpoint is exposed until Phase 5/6 finalize
the input and preprocessing contract.

### ML artifact compatibility

The original `ml/artifacts/model.pkl` is a legacy joblib pickle containing
XGBoost state that is not reliably portable across runtimes. The repository
does not replace it automatically. The supported remediation is to run
`ml/evaluation/export_portable_artifacts.py` in the exact environment where the
source ensemble and preprocessing pipeline load successfully. The exporter
refuses to overwrite an existing `ml/artifacts/portable/` directory and writes
the XGBoost estimator in native JSON format while keeping scikit-learn
estimators and preprocessing as separate joblib artifacts.

After validating that bundle, set `ARTIFACT_FORMAT=portable` and
`PORTABLE_MANIFEST_FILENAME=portable/manifest.json`. If the source pickle
cannot be loaded, do not substitute the separate legacy estimators: they do not
represent the declared soft-voting ensemble and cannot establish compatible
preprocessing or prediction behavior.

### Recovery sequence for a new machine

1. Obtain the complete `ml/artifacts/` directory from the original training
   machine or an external backup. Git and the GitHub repository do not contain
   these gitignored files.
2. On the original machine, use the recorded runtime as the starting point:
   Python `3.14.4`, NumPy `2.5.3`, pandas `3.0.5`, scikit-learn `1.9.1`,
   XGBoost `3.4.1`, and joblib `1.6.0`. Verify the actual installed versions
   before loading the pickle; the checked-in requirements alone are not proof
   of pickle compatibility.
3. Run this read-only load check. It must print the ensemble type and all three
   estimator names:

   ```bash
   python -c "import joblib; model = joblib.load('ml/artifacts/model.pkl'); print(type(model)); print(model.named_estimators_); print(model.weights)"
   ```

4. In that same environment, run:

   ```bash
   python ml/evaluation/export_portable_artifacts.py
   python ml/evaluation/validate_artifacts.py
   ```

   Do not copy or enable the portable bundle if either command fails.
5. Transfer the validated `ml/artifacts/portable/` directory and metadata to
   this machine, rerun `diagnose_artifacts.py`, and only then configure
   `ARTIFACT_FORMAT=portable`. Production must retain
   `ARTIFACT_LOADING_REQUIRED=true`.

If the original machine is unavailable and no external copy exists, migration
cannot be completed without retraining. Retraining would create a new model,
not recover the original ensemble, and is intentionally not performed here.

### Render deployment

The backend fails fast when the portable bundle is absent, so the validated
portable files must be included in the commit deployed to Render. The
repository ignores legacy pickles and all unrelated model files, but explicitly
allows the portable bundle and its metadata.

From the repository root, verify the files before pushing:

```bash
git status --short ml/artifacts
git add .gitignore ml/artifacts/model_metadata.json \
  ml/artifacts/feature_metadata.json ml/artifacts/portable
git commit -m "Include validated portable ML bundle"
git push
```

Use these Render settings:

```text
Root Directory: .
Build Command: pip install -r backend/requirements.txt
Start Command: uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
ARTIFACT_DIRECTORY=/opt/render/project/src/ml/artifacts
ARTIFACT_FORMAT=portable
PORTABLE_MANIFEST_FILENAME=portable/manifest.json
PREPROCESSING_MODE=embedded
ARTIFACT_LOADING_REQUIRED=true
```

Do not upload `.env`, `model.pkl`, or any legacy artifacts to Render. After
deployment, `GET /api/health` must report `models_loaded: true` before the
frontend is pointed at the service.

Run the read-only migration diagnostic from the repository root before changing
artifact settings:

```bash
python ml/evaluation/diagnose_artifacts.py ml/artifacts \
  --output ml/reports/artifact_diagnostics.json
```

It records artifact sizes and SHA-256 hashes, metadata validity, installed
package versions, source-pickle loading status, and portable-bundle references.
The recorded artifact metadata identifies Python 3.14.4, scikit-learn 1.9.1,
XGBoost 3.4.1, and joblib 1.6.0; the checked-in requirements are not proof of
the original training environment.

## ML experimentation notebooks

The executable Phase 4 experiments are in `ml/notebooks/`:

- `03_logistic_regression.ipynb`
- `04_random_forest.ipynb`
- `05_gradient_boosting.ipynb`
- `06_model_comparison.ipynb`

Run Phase 2 and Phase 3 preparation first, then train the reusable Phase 4 artifacts:

```powershell
python -m ml.preprocessing.clean_data
python -m ml.preprocessing.build_pipeline
python -m ml.training.train_models
```

Open the notebooks from the repository root in VS Code or Jupyter and run them in numeric order. They load the cleaned train/validation/test splits, the fitted preprocessing artifact, and shared training helpers from `ml/training/`. The notebooks include cross-validation, hyperparameter tuning, evaluation metrics, visual diagnostics, feature interpretation, and written observations. The test split is reserved for final comparison and primary-model decisions remain a Phase 5 responsibility.

## Notes

- Legacy model artifacts are intentionally ignored by git. Only the validated
  portable deployment bundle is explicitly allowed.
- This project is for educational/analytical use only and is not an official lender or credit decision system.
