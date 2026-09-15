import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.assessment import router as assessment_router
from app.config import Settings, get_settings
from app.core.exceptions import (
    ArtifactLoadError,
    error_response,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.services.ml_artifact_loader import MLArtifactLoader
from app.services.openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging()
    artifact_loader = MLArtifactLoader(app_settings)
    openrouter_service = OpenRouterService(app_settings)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.settings = app_settings
        application.state.artifact_loader = artifact_loader
        application.state.openrouter_service = openrouter_service
        if app_settings.environment_name.lower() == "production":
            if not app_settings.artifact_loading_required:
                raise ArtifactLoadError(
                    "Artifact loading cannot be disabled in production"
                )
        if app_settings.artifact_loading_required:
            try:
                artifact_loader.load()
            except ArtifactLoadError:
                logger.exception("ML artifact startup validation failed")
                raise
        else:
            logger.warning(
                "ML artifact loading is disabled; prediction integration is unavailable"
            )
        yield

    app = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    async def artifact_error_handler(request, exc: ArtifactLoadError):
        del request
        return error_response("artifact_error", str(exc), 503)

    app.add_exception_handler(ArtifactLoadError, artifact_error_handler)
    app.add_exception_handler(Exception, http_exception_handler)
    app.include_router(health_router)
    app.include_router(assessment_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "CrediLens AI backend is running."}

    return app


app = create_app()
