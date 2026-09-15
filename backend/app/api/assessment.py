from fastapi import APIRouter, Request

from app.core.exceptions import ArtifactLoadError
from app.schemas.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    ExplanationResponse,
    SimulatorRequest,
    SimulatorResponse,
)
from app.services.openrouter_service import EXPLANATION_DISCLAIMER
from app.services.prediction_service import predict_assessment
from app.services.simulator_service import simulate_assessment

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.post("/predict", response_model=AssessmentResponse)
def predict(request: Request, payload: AssessmentRequest) -> AssessmentResponse:
    artifacts = request.app.state.artifact_loader.artifacts
    if artifacts is None:
        raise ArtifactLoadError("ML artifacts are not loaded")
    return predict_assessment(artifacts, payload.borrower_input)


@router.post("/explanation", response_model=ExplanationResponse)
def explanation(request: Request, payload: AssessmentRequest) -> ExplanationResponse:
    artifacts = request.app.state.artifact_loader.artifacts
    if artifacts is None:
        raise ArtifactLoadError("ML artifacts are not loaded")
    assessment = predict_assessment(artifacts, payload.borrower_input)
    text, source = request.app.state.openrouter_service.explain(assessment)
    return ExplanationResponse(
        assessment=assessment,
        explanation=text,
        explanation_source=source,
        disclaimer=EXPLANATION_DISCLAIMER,
    )


@router.post("/simulator/predict", response_model=SimulatorResponse)
def simulator_predict(
    request: Request, payload: SimulatorRequest
) -> SimulatorResponse:
    artifacts = request.app.state.artifact_loader.artifacts
    if artifacts is None:
        raise ArtifactLoadError("ML artifacts are not loaded")
    return simulate_assessment(artifacts, payload.borrower_input)
