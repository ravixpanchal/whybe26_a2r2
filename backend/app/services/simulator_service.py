from __future__ import annotations

from app.schemas.assessment import BorrowerInput, SimulatorResponse
from app.services.ml_artifact_loader import LoadedArtifacts
from app.services.prediction_service import predict_assessment

SIMULATOR_DISCLAIMER = (
    "This is a simulated rerun of the validated model with changed inputs. "
    "It is not a guarantee, lending decision, or financial advice."
)


def simulate_assessment(
    artifacts: LoadedArtifacts, borrower: BorrowerInput
) -> SimulatorResponse:
    return SimulatorResponse(
        assessment=predict_assessment(artifacts, borrower),
        disclaimer=SIMULATOR_DISCLAIMER,
    )
