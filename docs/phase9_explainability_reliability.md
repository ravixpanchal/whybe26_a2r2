# Phase 9: Explainability and Reliability

The prediction response includes local feature contributions and a qualitative
reliability indicator.

## Explainability

The portable bundle's embedded Logistic Regression component supplies
coefficient-based local contributions in transformed feature space. One-hot
contributions are aggregated back to their original feature names using
`feature_metadata.json`. A positive contribution increases the model's
default-risk score; a negative contribution reduces it. These are directional
model explanations, not causal effects.

## Reliability

The reliability score is a transparent heuristic, not calibrated statistical
confidence. It starts at 100 and applies documented penalties for:

- missing values that preprocessing must impute;
- numeric values outside the observed training range;
- unseen categorical values;
- disagreement among embedded ensemble components;
- probability within 0.05 of the validated `0.59` threshold.

The response exposes the resulting `high`, `medium`, or `low` level, score,
and reasons. Artifact compatibility remains a startup requirement; an
incompatible bundle does not produce a lower reliability prediction.
