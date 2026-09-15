from fastapi.testclient import TestClient

from app.config import REPOSITORY_ROOT, Settings
from app.main import create_app


def test_health_endpoint_returns_200_when_artifact_loading_is_disabled() -> None:
    settings = Settings(
        ENVIRONMENT_NAME="development",
        ARTIFACT_LOADING_REQUIRED=False,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "environment": "development",
        "artifact_loading": "disabled",
        "models_loaded": False,
        "version": "1.0.0",
        "artifact_error": None,
    }


def test_model_info_reports_loaded_portable_artifact() -> None:
    settings = Settings(ARTIFACT_DIRECTORY=REPOSITORY_ROOT / "ml" / "artifacts")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/model-info")

    assert response.status_code == 200
    body = response.json()
    assert body["model"]["name"] == "soft_voting_ensemble"
    assert body["primary_model"] == "soft_voting_ensemble"
    assert body["compatibility_status"] == "validated"


def test_health_reports_degraded_when_loading_is_disabled() -> None:
    settings = Settings(
        ENVIRONMENT_NAME="development",
        ARTIFACT_LOADING_REQUIRED=False,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health")

    assert response.json()["status"] == "degraded"
    assert response.json()["models_loaded"] is False
