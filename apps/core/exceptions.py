# Every error response gets normalized to {"error": {"code", "message", "details"?}}
# so API consumers don't have to branch on which kind of error they hit.

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
        message = (
            "One or more fields failed validation."
            if isinstance(data, dict)
            else str(data)
        )
        details = data

    error_body = {"code": code, "message": message}
    if details is not None:
        error_body["details"] = details

    return Response(
        {"error": error_body}, status=response.status_code, headers=response.headers
    )
