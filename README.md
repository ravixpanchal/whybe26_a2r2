# CrediLens AI

CrediLens AI is an explainable borrower risk assessment platform for educational and analytical decision support.

## Repository structure

- frontend/: Next.js + TypeScript application
- backend/: FastAPI API and business logic
- ml/: model training, preprocessing, and evaluation code
- data/: dataset snapshots and dataset documentation
- docs/: design and operational documentation

## Application flows

The frontend provides these routes:

- `/`: CrediLens AI home page with the product introduction, informational
  panels, and links to start an assessment.
- `/assessment`: guided borrower assessment with identity metadata, the
  30-field user-facing form, contextual questions, live completeness card,
  and validation before submission.
- `/assessment/results`: generated assessment report with the actual model
  probability and risk category, financial summaries, income history,
  contribution information, recommendations, report actions, and responsible-AI
  notices.
- `/simulator`: What-If Simulator opened from the results flow. It allows a
  limited set of editable inputs and sends them through the existing simulator
  endpoint without changing the model or threshold.

The assessment UI presents 30 editable/user-facing fields. The backend
prediction contract intentionally remains a 36-feature contract because the
trained model includes eight legacy `survey_q1` through `survey_q8` features.
Full Name, Date of Birth, and the two contextual survey answers are report
metadata and are not added to the model feature vector.

## Local setup

Run commands from the repository root unless a command explicitly changes
directory.

### Python environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r ml/requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r ml/requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Create `.env` only for local development. Never commit it or upload it to
Render/Vercel:

```bash
cp .env.example .env
```

For a local portable-artifact run, set `ARTIFACT_DIRECTORY` to the absolute
path of this repository's `ml/artifacts` directory and use:

```text
ARTIFACT_LOADING_REQUIRED=true
ARTIFACT_FORMAT=portable
PORTABLE_MANIFEST_FILENAME=portable/manifest.json
PREPROCESSING_MODE=embedded
BACKEND_CORS_ORIGINS=http://localhost:3000
OPENROUTER_API_KEY=
```

## FastAPI backend

Run the backend from the repository root:

```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

The backend exposes:

- `GET /api/health`
- `GET /api/model-info`
- `POST /api/assessment/predict`
- `POST /api/assessment/explanation`
- `POST /api/assessment/simulator/predict`
- `POST /api/report/generate`

The simulator uses `POST /api/assessment/simulator/predict` and preserves the
same preprocessing, validated ensemble, feature order, threshold, and artifact
bundle as the primary assessment flow.

Check backend readiness:

```bash
curl http://localhost:8000/api/health
```

The response must contain `"models_loaded": true` before using prediction
endpoints.
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

## Run the frontend

In a second terminal:

```bash
cd frontend
npm run dev
```

Open <http://localhost:3000>. For local frontend-to-backend calls, create
`frontend/.env.local` with:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

This variable is public because browser code calls the API directly. Never
place `OPENROUTER_API_KEY` in the frontend.

## Tests, lint, and production builds

Run backend tests from the repository root:

```bash
ARTIFACT_DIRECTORY="$PWD/ml/artifacts" \
ARTIFACT_FORMAT=portable \
ARTIFACT_LOADING_REQUIRED=true \
OPENROUTER_API_KEY="" \
.venv/bin/python -m pytest -q backend/tests
```

Run frontend lint and build:

```bash
cd frontend
npm run lint
npm run build
npm run start
```

The frontend uses the same pale-lavender, cobalt-blue visual system across the
home page, assessment page, results report, and What-If Simulator. UI styling
changes do not alter prediction requests, feature encoding, or report
generation behavior.

## Deployment

### Render backend

Create a Render Web Service connected to this repository:

```text
Root Directory: .
Build Command: pip install -r backend/requirements.txt
Start Command: uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

Required Render environment variables:

```text
ARTIFACT_DIRECTORY=/opt/render/project/src/ml/artifacts
ARTIFACT_FORMAT=portable
PORTABLE_MANIFEST_FILENAME=portable/manifest.json
PREPROCESSING_MODE=embedded
ARTIFACT_LOADING_REQUIRED=true
BACKEND_CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app
OPENROUTER_API_KEY=<rotated-key>
```

Do not use `Add from .env`. Do not upload `.env`, `model.pkl`, or legacy
artifacts. After deployment, verify:

```bash
curl https://YOUR-RENDER-DOMAIN.onrender.com/api/health
```

### Vercel frontend

Create a Vercel project using the `frontend` directory as the project root.
Add this Production environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR-RENDER-DOMAIN.onrender.com
```

Use these settings:

```text
Build Command: npm run build
Output Directory: .next
Install Command: npm install
```

Redeploy Vercel after changing environment variables. Ensure the Render
`BACKEND_CORS_ORIGINS` value exactly matches the deployed Vercel origin,
without a trailing slash.

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
