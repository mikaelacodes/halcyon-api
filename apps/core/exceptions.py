# Every error response gets normalized to {"error": {"code", "message", "details"?}}
# so API consumers don't have to branch on which kind of error they hit.

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db.models.deletion import ProtectedError
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def standardized_exception_handler(exc, context):
    # A delete that would orphan FK references (e.g. a Warehouse with stock
    # history) isn't an APIException, so DRF's default handler never sees
    # it — without this it'd fall through as a raw 500 instead of a 409.
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "error": {
                    "code": "conflict",
                    "message": "Cannot delete: other records still reference this object.",
                }
            },
            status=status.HTTP_409_CONFLICT,
        )

    # DRF's exception_handler does this same swap internally before building
    # the response, but keeps the original exc. Mirror it here too, otherwise
    # `exc.default_code` below reads "Http404" instead of "not_found".
    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound(*exc.args)
    elif isinstance(exc, DjangoPermissionDenied):
        exc = drf_exceptions.PermissionDenied(*exc.args)

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
