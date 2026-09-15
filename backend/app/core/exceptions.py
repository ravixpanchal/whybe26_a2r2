from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ArtifactLoadError(RuntimeError):
    """Raised when the configured ML artifact bundle cannot be loaded."""


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    return error_response("validation_error", str(exc), 422)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    del request
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "Request failed")
    return error_response("http_error", str(detail), status_code)
