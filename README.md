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

- Model artifacts are intentionally ignored by git.
- This project is for educational/analytical use only and is not an official lender or credit decision system.
