from fastapi import APIRouter, Request

from app.schemas.common import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        environment=settings.environment_name,
        artifact_loading="required" if settings.artifact_loading_required else "disabled",
    )
