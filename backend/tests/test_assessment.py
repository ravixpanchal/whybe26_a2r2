from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.openrouter_service import OpenRouterService


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


def test_predict_returns_received_ensemble_result() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["model_comparison"]["primary_model"] == "soft_voting_ensemble"
    assert body["model_comparison"]["compatibility_status"] == "validated"
    assert 0 <= body["risk_probability"] <= 1
    assert body["risk_category"] in {"low", "moderate", "high"}
    assert body["feature_contributions"]
    assert body["feature_contributions"][0]["direction"] in {
        "risk_increasing",
        "risk_reducing",
    }
    assert body["reliability"]["level"] in {"high", "medium", "low"}
    assert "not calibrated" in body["reliability"]["disclaimer"]


def test_predict_rejects_logically_inconsistent_input() -> None:
    payload = _payload()
    payload["borrower_input"]["utility_bills_paid"] = 20
    payload["borrower_input"]["utility_bills_total"] = 3

    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_predict_marks_missing_and_unknown_values_as_lower_reliability() -> None:
    payload = _payload()
    payload["borrower_input"]["income_month_1"] = None
    payload["borrower_input"]["borrower_type"] = "unseen-category"

    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/predict", json=payload)

    assert response.status_code == 200
    reliability = response.json()["reliability"]
    assert reliability["level"] == "low"
    assert any("imputed" in reason for reason in reliability["reasons"])
    assert any("unseen category" in reason for reason in reliability["reasons"])


def test_explanation_endpoint_returns_safe_fallback_without_api_key() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/assessment/explanation", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["explanation_source"] == "fallback"
    assert "not a loan approval or rejection" in body["explanation"]
    assert body["assessment"]["risk_category"] in {"low", "moderate", "high"}


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            self._content
                        )
                    }
                }
            ]
        }


class _FakeClient:
    def __init__(self, category: str) -> None:
        self.category = category

    def post(self, *args, **kwargs) -> _FakeResponse:
        return _FakeResponse(
            f"The {self.category} risk category reflects a {self.category} "
            "default-risk probability. This is educational and not a loan approval."
        )


def test_openrouter_response_is_accepted_only_as_translation() -> None:
    with TestClient(create_app()) as client:
        assessment = client.post("/api/assessment/predict", json=_payload()).json()

    from app.schemas.assessment import AssessmentResponse

    service = OpenRouterService(
        Settings(openrouter_api_key="test-key"),
        client=_FakeClient(assessment["risk_category"]),
    )
    text, source = service.explain(AssessmentResponse.model_validate(assessment))
    assert source == "openrouter"
    assert f"{assessment['risk_category']} risk category" in text


def test_openrouter_contradiction_falls_back() -> None:
    class ContradictingClient:
        def post(self, *args, **kwargs) -> _FakeResponse:
            response = _FakeResponse("This is high risk and approved.")
            response.json = lambda: {
                "choices": [{"message": {"content": "This is high risk and approved."}}]
            }
            return response

    service = OpenRouterService(
        Settings(openrouter_api_key="test-key"),
        client=ContradictingClient(),
    )
    with TestClient(create_app()) as client:
        assessment = client.post("/api/assessment/predict", json=_payload()).json()

    from app.schemas.assessment import AssessmentResponse

    text, source = service.explain(AssessmentResponse.model_validate(assessment))
    assert source == "fallback"
    assert text.startswith("The validated model places")


def test_openrouter_transient_failure_is_retried_then_falls_back() -> None:
    class TransientClient:
        calls = 0

        def post(self, *args, **kwargs) -> _FakeResponse:
            self.calls += 1
            response = _FakeResponse("temporary failure")
            response.status_code = 503
            return response

    client = TransientClient()
    service = OpenRouterService(
        Settings(openrouter_api_key="test-key"),
        client=client,
        sleep=lambda _: None,
    )
    with TestClient(create_app()) as api_client:
        assessment = api_client.post("/api/assessment/predict", json=_payload()).json()

    from app.schemas.assessment import AssessmentResponse

    text, source = service.explain(AssessmentResponse.model_validate(assessment))
    assert source == "fallback"
    assert client.calls == 2
    assert text.startswith("The validated model places")
