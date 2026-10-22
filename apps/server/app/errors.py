"""Errores públicos sin valores de entrada ni detalles privados."""

from fastapi.responses import JSONResponse

from .api_models import ProblemDTO

PROBLEMS = {
    "INVALID_HOST": (403, "Invalid host"),
    "FORBIDDEN_ORIGIN": (403, "Forbidden origin"),
    "INVALID_PARAMS": (422, "Invalid parameters"),
    "LYRICS_DECLARATION_REQUIRED": (422, "Lyrics declaration required"),
    "NOT_FOUND": (404, "Not found"),
    "METHOD_NOT_ALLOWED": (405, "Method not allowed"),
    "CONFLICT": (409, "Conflict"),
    "PURGE_RETENTION": (409, "Song retention period has not elapsed"),
    "PURGE_PROTECTED": (409, "Song has durable history and cannot be purged"),
    "INTERNAL": (500, "Internal server error"),
    "SESSION_REQUIRED": (401, "Session required"),
    "FORBIDDEN_SCOPE": (403, "Forbidden scope"),
    "SESSION_LIMIT": (503, "Session limit"),
    "SNAPSHOT_LIMIT": (503, "Snapshot limit"),
    "SERVICE_UNAVAILABLE": (503, "Service unavailable"),
}


def problem(code, status=None, headers=None):
    default_status, title = PROBLEMS[code]
    status = status or default_status
    safe_headers = {}
    if isinstance(headers, dict):
        for name, value in headers.items():
            if (
                isinstance(name, str)
                and name.lower() in {"allow", "www-authenticate"}
                and isinstance(value, str)
                and value
                and all(32 <= ord(char) <= 126 for char in value)
            ):
                safe_headers[name.lower()] = value
    return JSONResponse(
        ProblemDTO(title=title, status=status, detail=title, code=code).model_dump(),
        status_code=status,
        media_type="application/problem+json",
        headers=safe_headers,
    )
