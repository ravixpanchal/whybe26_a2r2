from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    environment: str
    artifact_loading: str
    models_loaded: bool
    version: str
    artifact_error: str | None = None


class ArtifactStatus(BaseModel):
    model_loaded: bool
    metadata_loaded: bool
    preprocessing_loaded: bool
    metadata: dict[str, Any]


class ModelInfoResponse(BaseModel):
    model: dict[str, Any]
    primary_model: str
    compatibility_status: str
