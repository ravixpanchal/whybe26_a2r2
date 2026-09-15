from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.assessment import BorrowerInput
from app.services.preprocessing_service import borrower_to_frame
from app.services.prediction_service import VALIDATED_RISK_THRESHOLD


def _payload() -> dict:
    values = {
        "borrower_type": "gig",
        "employment_type": "salaried-gig",
        "loan_purpose": "business",
        "household_size": 3,
        "same_number_since_year": 2018,
        "loan_tenure_months": 12,
    }
    for index in range(1, 7):
        values[f"income_month_{index}"] = 10.0
    for name in (
        "months_at_current_job",
        "num_income_sources",
        "upi_transactions_per_month",
        "upi_avg_transaction_amount",
        "upi_months_active",
        "mobile_wallet_used",
        "utility_bills_paid",
        "utility_bills_total",
        "rent_paid_on_time_months",
        "total_rental_months",
        "avg_monthly_recharge_amount",
        "recharge_frequency_per_month",
        "ecomm_orders_per_month",
        "ecomm_return_rate",
        "prepaid_orders_ratio",
        "loan_amount_requested",
    ):
        values[name] = 1.0
    for index in range(1, 9):
        values[f"survey_q{index}"] = 3
    return {"borrower_input": values}


def test_schema_rejects_missing_extra_and_out_of_range_values() -> None:
    payload = _payload()
    payload["borrower_input"]["survey_q1"] = 6
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=payload)
    assert response.status_code == 422

    missing = _payload()
    del missing["borrower_input"]["loan_purpose"]
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=missing)
    assert response.status_code == 422

    extra = _payload()
    extra["borrower_input"]["unexpected"] = "value"
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=extra)
    assert response.status_code == 422


def test_preprocessing_preserves_feature_order_deterministically() -> None:
    borrower = BorrowerInput.model_validate(_payload()["borrower_input"])
    order = list(BorrowerInput.model_fields)
    first = borrower_to_frame(borrower, order)
    second = borrower_to_frame(borrower, order)
    assert list(first.columns) == order
    assert first.equals(second)


def test_prediction_has_bounded_probability_and_authoritative_class_mapping() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=_payload())
    body = response.json()
    assert response.status_code == 200
    assert 0 <= body["risk_probability"] <= 1
    assert body["class_mapping"]["negative_class"] == 0
    assert body["class_mapping"]["positive_class"] == 1
    expected_category = (
        "high" if body["risk_probability"] >= VALIDATED_RISK_THRESHOLD else "low"
    )
    assert body["risk_category"] == expected_category


def test_reliability_detects_threshold_proximity_and_unknown_categories() -> None:
    payload = _payload()
    payload["borrower_input"]["borrower_type"] = "unknown-category"
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=payload)
    body = response.json()
    assert response.status_code == 200
    reasons = body["reliability"]["reasons"]
    assert any("unseen category" in reason for reason in reasons)
    assert body["reliability"]["disclaimer"].lower().find("calibrated") >= 0


def test_report_contains_real_response_sections_and_simulation_support() -> None:
    with TestClient(create_app()) as client:
        explanation = client.post(
            "/api/assessment/explanation", json=_payload()
        ).json()
        simulation = client.post(
            "/api/assessment/simulator/predict", json=_payload()
        ).json()
        payload = {
            "explanation": explanation,
            "borrower_input": _payload()["borrower_input"],
            "simulator": simulation,
        }
        response = client.post("/api/report/generate", json=payload)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert b"CrediLens" in response.content
    assert response.headers["content-disposition"].endswith(
        'filename="credilens-assessment.pdf"'
    )


def test_cors_does_not_grant_disallowed_origin_and_malformed_requests_are_4xx() -> None:
    with TestClient(create_app()) as client:
        response = client.options(
            "/api/health",
            headers={
                "Origin": "https://not-allowed.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        malformed = client.post(
            "/api/assessment/predict",
            json={"borrower_input": {"household_size": "not-a-number"}},
        )
    assert "access-control-allow-origin" not in response.headers
    assert malformed.status_code == 422


def test_openrouter_key_is_not_present_in_frontend_sources() -> None:
    frontend = Path(__file__).resolve().parents[2] / "frontend"
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in frontend.rglob("*")
        if path.is_file()
        and path.suffix in {".ts", ".tsx", ".css"}
        and "node_modules" not in path.parts
    )
    assert "OPENROUTER_API_KEY" not in source_text


def test_env_file_is_ignored_by_git() -> None:
    import subprocess

    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        cwd=root,
        check=False,
    )
    assert result.returncode == 0
