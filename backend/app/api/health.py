from fastapi import APIRouter, Request

from app.schemas.common import HealthResponse, ModelInfoResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    loaded = request.app.state.artifact_loader.artifacts is not None
    return HealthResponse(
        status="ok" if loaded else "degraded",
        environment=settings.environment_name,
        artifact_loading="required" if settings.artifact_loading_required else "disabled",
        models_loaded=loaded,
        version=settings.app_version,
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(request: Request) -> ModelInfoResponse:
    loaded = request.app.state.artifact_loader.artifacts
    if loaded is None:
        from app.core.exceptions import ArtifactLoadError

        raise ArtifactLoadError("ML artifacts are not loaded")

    metadata = loaded.metadata
    return ModelInfoResponse(
        model={
            "name": metadata.get("model_name", metadata.get("model_type", "unknown")),
            "version": metadata.get("artifact_version", "unversioned"),
            "trained_on": metadata.get("training_source", []),
            "metrics": metadata.get("metrics", {}),
        },
        primary_model=metadata.get("model_name", metadata.get("model_type", "unknown")),
        compatibility_status="validated",
    )
