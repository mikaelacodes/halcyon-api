"""Standardized JSON error schema for the API.

Every error response (validation, auth, permission, not-found, throttling,
unhandled 500s) is normalized to:

    {
        "error": {
            "code": "validation_error",
            "message": "A human-readable summary.",
            "details": {...}  # optional, field-level or extra context
        }
    }
"""

from rest_framework.response import Response
from rest_framework.views import exception_handler


def standardized_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    data = response.data
    code = getattr(exc, "default_code", exc.__class__.__name__)

    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        message = str(data["detail"])
        details = None
    else:
        message = "One or more fields failed validation." if isinstance(data, dict) else str(data)
        details = data

    error_body = {"code": code, "message": message}
    if details is not None:
        error_body["details"] = details

    return Response({"error": error_body}, status=response.status_code, headers=response.headers)
