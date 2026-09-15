# Phase 14: Score Improvement Simulator

The simulator accepts the same finalized borrower schema as the assessment
endpoint and invokes the same validated preprocessing, portable ensemble,
explainability, and reliability pipeline. It does not calculate score deltas
with hand-written rules.

The frontend exposes a deliberately small set of editable, non-sensitive
scenario fields: recent income, income-source count, job tenure, and loan
tenure. All submitted values still pass the backend `BorrowerInput` contract
and its cross-field validation.

Simulator results are explicitly labeled simulated and are not guarantees,
financial advice, approvals, or rejections.
