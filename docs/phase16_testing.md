# Phase 16: Testing

The repository's backend acceptance suite runs with pytest and uses the
validated portable artifact bundle. It covers:

- Pydantic schema, missing-field, extra-field, range, and logical validation;
- deterministic feature ordering before preprocessing;
- prediction probability bounds, class mapping, and the validated threshold;
- explainability/reliability output and degraded-input signals;
- simulator reruns, without hardcoded score-delta logic;
- PDF report generation and simulator inclusion;
- OpenRouter fallback and retry behavior;
- malformed requests, CORS behavior, frontend API-key hygiene, and `.env`
  ignore rules.

Run the backend suite from the repository root:

```bash
ARTIFACT_DIRECTORY="$PWD/ml/artifacts" OPENROUTER_API_KEY="" \
  .venv/bin/python -m pytest -q
```

Run the frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The frontend currently uses the existing lint/build validation rather than
introducing a second browser test runner.
