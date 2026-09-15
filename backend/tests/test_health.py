from fastapi.testclient import TestClient

from app.config import Settings
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
        "status": "ok",
        "environment": "development",
        "artifact_loading": "disabled",
        "artifact_error": None,
    }
