from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.assessment import ReportRequest
from app.services.report_service import generate_report

router = APIRouter(prefix="/api/report", tags=["reports"])


@router.post("/generate")
def generate(request: ReportRequest) -> Response:
    return Response(
        content=generate_report(request),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="credilens-assessment.pdf"'},
    )
