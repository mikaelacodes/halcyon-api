from django.http import JsonResponse
from django.views import defaults


def not_found_view(request, exception=None):
    if not request.path.startswith("/api/"):
        return defaults.page_not_found(request, exception)
    return JsonResponse(
        {
            "error": {
                "code": "not_found",
                "message": "The requested resource was not found.",
            }
        },
        status=404,
    )


def server_error_view(request):
    if not request.path.startswith("/api/"):
        return defaults.server_error(request)
    return JsonResponse(
        {"error": {"code": "server_error", "message": "An unexpected error occurred."}},
        status=500,
    )
